#!/usr/bin/env python3
"""
Phase B (read-only audit): find duplicate BibDesk entries for the same paper
and classify their linked PDFs as arXiv preprint vs. published, so a winner
(and any needed file swap) can be chosen before anything is touched.

Detection signals (all exact-match, unioned via union-find):
  - shared `eprint` id
  - shared resolved bibcode (from `adsurl`)
  - shared linked-file content hash (SHA-256)

Writes nothing to ioannis.bib, BibDesk, or any PDF. Output: a markdown report.
"""
import base64
import hashlib
import os
import plistlib
import re
import subprocess
import unicodedata
from collections import defaultdict

BIBDESK_ROOT = os.path.expanduser("~/research/bibdesk")
BIB_PATH = os.path.join(BIBDESK_ROOT, "ioannis.bib")
REPORT_PATH = os.path.expanduser("~/research/bibdesk/tools/pdf_dedup_report.md")

ARXIV_JOURNAL_VALUES = {"arxiv e-prints"}


def nfc(s):
    return unicodedata.normalize("NFC", s) if s else s


def parse_entries(text):
    parts = re.split(r"\n(?=@)", text)
    return [p for p in parts if p.startswith("@")]


def get_relpaths(entry):
    paths = []
    for m in re.finditer(r"bdsk-file-\d+\s*=\s*\{([^}]+)\}", entry):
        try:
            data = plistlib.loads(base64.b64decode(m.group(1)))
            rp = data.get("relativePath")
            if rp:
                paths.append(nfc(rp))
        except Exception:
            pass
    return paths


def parse_entry(entry):
    key_m = re.match(r"@\w+\{([^,]+),", entry)
    if not key_m:
        return None
    eprint_m = re.search(r"^\s*eprint\s*=\s*\{([^}]+)\}", entry, re.M)
    adsurl_m = re.search(r"^\s*adsurl\s*=\s*\{[^}]*abs/([^}]+)\}", entry, re.M)
    journal_m = re.search(r"^\s*journal\s*=\s*\{([^}]*)\}", entry, re.M)
    date_m = re.search(r"^\s*date-added\s*=\s*\{([^}]*)\}", entry, re.M)
    doi_m = re.search(r"^\s*doi\s*=\s*\{([^}]*)\}", entry, re.M)
    return {
        "key": key_m.group(1),
        "eprint": eprint_m.group(1) if eprint_m else None,
        "bibcode": adsurl_m.group(1) if adsurl_m else None,
        "journal": (journal_m.group(1).strip() if journal_m else ""),
        "date_added": date_m.group(1) if date_m else "",
        "doi": doi_m.group(1) if doi_m else None,
        "relpaths": get_relpaths(entry),
    }


def is_published(journal):
    return journal.strip().lower() not in ARXIV_JOURNAL_VALUES


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_pdf(full_path, doi=None):
    """Return 'arxiv', 'published', or 'unknown' based on page-1 text."""
    try:
        out = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", full_path, "-"],
            capture_output=True, text=True, timeout=20,
        )
        text = out.stdout
    except Exception:
        return "unknown"
    if re.search(r"arXiv:\d{4}\.\d{4,5}", text) or "arXiv:" in text:
        return "arxiv"
    if doi and doi in text:
        return "published"
    if re.search(r"\bDOI\b|\bdoi\.org\b|Received:.*Accepted:", text, re.I):
        return "published"
    return "unknown"


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def main():
    text = open(BIB_PATH, encoding="utf-8").read()
    records = [r for r in (parse_entry(e) for e in parse_entries(text)) if r]
    by_key = {r["key"]: r for r in records}
    print(f"Parsed {len(records)} entries")

    # hash every distinct linked file once
    path_hash = {}
    for r in records:
        for rp in r["relpaths"]:
            if rp in path_hash:
                continue
            full = os.path.join(BIBDESK_ROOT, rp)
            if os.path.exists(full):
                path_hash[rp] = sha256_of(full)
            else:
                path_hash[rp] = None
    print(f"Hashed {len(path_hash)} distinct linked files")

    uf = UnionFind()
    by_eprint = defaultdict(list)
    by_bibcode = defaultdict(list)
    by_hash = defaultdict(list)
    for r in records:
        uf.find(r["key"])
        if r["eprint"]:
            by_eprint[r["eprint"]].append(r["key"])
        if r["bibcode"]:
            by_bibcode[r["bibcode"]].append(r["key"])
        for rp in r["relpaths"]:
            h = path_hash.get(rp)
            if h:
                by_hash[h].append(r["key"])

    for group_map in (by_eprint, by_bibcode, by_hash):
        for keys in group_map.values():
            for k in keys[1:]:
                uf.union(keys[0], k)

    clusters = defaultdict(list)
    for r in records:
        clusters[uf.find(r["key"])].append(r["key"])
    clusters = {root: keys for root, keys in clusters.items() if len(keys) > 1}
    print(f"Found {len(clusters)} duplicate clusters covering {sum(len(v) for v in clusters.values())} entries")

    lines = ["# PDF duplicate-resolution report\n",
             f"Total entries: {len(records)}. Duplicate clusters: {len(clusters)}.\n"]

    file_classify_cache = {}

    def classify(rp, doi):
        if rp not in file_classify_cache:
            full = os.path.join(BIBDESK_ROOT, rp)
            file_classify_cache[rp] = classify_pdf(full, doi) if os.path.exists(full) else "missing"
        return file_classify_cache[rp]

    for i, (root, keys) in enumerate(sorted(clusters.items()), 1):
        recs = [by_key[k] for k in keys]
        published = [r for r in recs if is_published(r["journal"])]
        pool = published if published else recs
        winner = max(pool, key=lambda r: r["date_added"])
        losers = [r for r in recs if r["key"] != winner["key"]]

        lines.append(f"\n## Cluster {i}: winner `{winner['key']}`\n")
        lines.append(f"- winner: **{winner['key']}** journal=`{winner['journal']}` "
                      f"date-added={winner['date_added']} doi={winner['doi']}")
        for rp in winner["relpaths"]:
            cls = classify(rp, winner["doi"])
            lines.append(f"    - file: `{rp}` [{cls}]")

        # Rank every file in the cluster (winner's own + every loser's) so we can
        # tell whether some OTHER file in the cluster is strictly better than the
        # winner's own — either because it's the published PDF and the winner's
        # is arXiv, or (more urgently) because the winner's own file is broken/
        # missing on disk while a loser's is not.
        RANK = {"published": 3, "arxiv": 2, "unknown": 1, "missing": 0}
        winner_paths = [(rp, classify(rp, winner["doi"]), winner["key"]) for rp in winner["relpaths"]]
        winner_best_rank = max((RANK[c] for _, c, _ in winner_paths), default=-1)

        candidates = list(winner_paths)
        for loser in losers:
            for rp in loser["relpaths"]:
                candidates.append((rp, classify(rp, loser["doi"] or winner["doi"]), loser["key"]))

        best = max(candidates, key=lambda c: RANK[c[1]])
        swap_from = None
        rescue = False
        if RANK[best[1]] > winner_best_rank:
            swap_from = (best[2], best[0])
            rescue = winner_best_rank <= RANK["missing"]  # winner's own file is broken/missing

        if swap_from:
            tag = "RESCUE (winner's own file is broken/missing)" if rescue else "SWAP (better file available)"
            lines.append(f"    - **{tag} PLANNED**: will link file `{swap_from[1]}` "
                          f"from `{swap_from[0]}` instead of winner's current file(s)")
        elif winner_best_rank <= RANK["missing"]:
            lines.append("    - **WARNING: winner's file is missing/broken and no better "
                          "file was found anywhere in this cluster — needs manual attention**")

        for loser in losers:
            lines.append(f"- loser (to delete): **{loser['key']}** journal=`{loser['journal']}` "
                          f"date-added={loser['date_added']} doi={loser['doi']}")
            for rp in loser["relpaths"]:
                cls = classify(rp, loser["doi"])
                will_trash = (swap_from is None or (loser["key"], rp) != swap_from)
                shared = any(
                    rp in by_key[other]["relpaths"]
                    for other in keys if other != loser["key"]
                )
                action = "kept (referenced elsewhere)" if shared else ("trashed" if will_trash else "kept (used for swap)")
                lines.append(f"    - file: `{rp}` [{cls}] -> {action}")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
