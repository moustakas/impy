#!/usr/bin/env python3
"""
Phase C: apply the duplicate-resolution decisions from find_pdf_duplicates.py
to a running BibDesk. Re-derives clusters/decisions fresh from the current
ioannis.bib (same logic as the audit script) rather than parsing its markdown
report, to avoid any parse-format mismatch.

For each cluster:
  - if the winner's own file needs replacing (rescue: winner's file is
    missing/broken; or swap: a better-ranked file exists elsewhere in the
    cluster), link the better file into the winner via `add POSIX file ...`
  - merge losers' static-group membership into the winner
  - delete each losing entry (plain `delete`, not ads2bibdesk's safe_delete,
    which would risk removing files we still want)
  - move now-orphaned loser PDFs to Trash (via Finder, not permanent removal),
    skipping any file still referenced by a surviving entry anywhere in the
    library, or any file that's already gone on disk

Clusters where no working file exists anywhere (the winner's-best-rank is
still "missing" after considering every candidate) are skipped entirely and
logged for manual attention.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import find_pdf_duplicates as fpd
from apply_arxiv_updates import find_pid_by_citekey
from ads2bibdesk.bibdesk import BibDesk

LOG_PATH = os.path.expanduser("~/research/bibdesk/tools/pdf_dedup_apply_log.md")


def as_applescript_string(value):
    return value.replace("\\", r"\\").replace('"', r"\"")


def trash_file(path):
    if not os.path.exists(path):
        return "already-gone"
    escaped = as_applescript_string(path)
    script = f'tell application "Finder" to delete POSIX file "{escaped}"'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"
    return "trashed"


def main():
    text = open(fpd.BIB_PATH, encoding="utf-8").read()
    records = [r for r in (fpd.parse_entry(e) for e in fpd.parse_entries(text)) if r]
    by_key = {r["key"]: r for r in records}

    # library-wide relpath -> referencing keys, for safe-to-trash checks
    relpath_refs = {}
    for r in records:
        for rp in r["relpaths"]:
            relpath_refs.setdefault(rp, set()).add(r["key"])

    # same clustering as the audit script
    path_hash = {}
    for r in records:
        for rp in r["relpaths"]:
            if rp in path_hash:
                continue
            full = os.path.join(fpd.BIBDESK_ROOT, rp)
            path_hash[rp] = fpd.sha256_of(full) if os.path.exists(full) else None

    uf = fpd.UnionFind()
    from collections import defaultdict
    by_eprint, by_bibcode, by_hash = defaultdict(list), defaultdict(list), defaultdict(list)
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

    RANKD = {"published": 3, "arxiv": 2, "unknown": 1, "missing": 0}
    classify_cache = {}

    def classify(rp, doi):
        if rp not in classify_cache:
            full = os.path.join(fpd.BIBDESK_ROOT, rp)
            classify_cache[rp] = fpd.classify_pdf(full, doi) if os.path.exists(full) else "missing"
        return classify_cache[rp]

    bibdesk = BibDesk()
    doc_path = bibdesk('return path of first document of application "BibDesk"').stringValue()
    if os.path.realpath(doc_path) != os.path.realpath(fpd.BIB_PATH):
        sys.exit(f"BibDesk's front document ({doc_path}) is not {fpd.BIB_PATH} — aborting, nothing changed.")
    print(f"Confirmed BibDesk front document: {doc_path}")

    log = ["# PDF dedup apply log\n"]
    all_losers_this_run = set()

    for root, keys in sorted(clusters.items()):
        recs = [by_key[k] for k in keys]
        published = [r for r in recs if fpd.is_published(r["journal"])]
        pool = published if published else recs
        winner = max(pool, key=lambda r: r["date_added"])
        losers = [r for r in recs if r["key"] != winner["key"]]

        winner_paths = [(rp, classify(rp, winner["doi"]), winner["key"]) for rp in winner["relpaths"]]
        winner_best_rank = max((RANKD[c] for _, c, _ in winner_paths), default=-1)
        candidates = list(winner_paths)
        for loser in losers:
            for rp in loser["relpaths"]:
                candidates.append((rp, classify(rp, loser["doi"] or winner["doi"]), loser["key"]))
        best = max(candidates, key=lambda c: RANKD[c[1]])

        if RANKD[best[1]] <= RANKD["missing"]:
            msg = f"- **SKIPPED cluster (winner {winner['key']})**: no working file found anywhere; left untouched."
            print(msg)
            log.append(msg)
            continue

        swap_from = None
        if RANKD[best[1]] > winner_best_rank:
            swap_from = (best[2], best[0])

        winner_pid = find_pid_by_citekey(bibdesk, winner["key"])
        if winner_pid is None:
            msg = f"- **ERROR**: winner cite key {winner['key']} not found in BibDesk, cluster skipped"
            print(msg)
            log.append(msg)
            continue

        cluster_log = [f"- **{winner['key']}** (cluster of {len(recs)})"]

        if swap_from:
            full = os.path.join(fpd.BIBDESK_ROOT, swap_from[1])
            try:
                bibdesk(f'add POSIX file "{full}" to beginning of linked files', winner_pid)
                cluster_log.append(f"    - linked file from `{swap_from[0]}`: `{swap_from[1]}`")
            except Exception as exc:
                cluster_log.append(f"    - ERROR linking swap file: {exc}")

        winner_groups = set(bibdesk.get_groups(winner_pid))
        for loser in losers:
            loser_pid = find_pid_by_citekey(bibdesk, loser["key"])
            if loser_pid is None:
                cluster_log.append(f"    - loser {loser['key']}: not found in BibDesk, skipped")
                continue
            try:
                winner_groups |= set(bibdesk.get_groups(loser_pid))
            except Exception:
                pass
            try:
                bibdesk("delete", loser_pid)
                cluster_log.append(f"    - deleted entry {loser['key']}")
            except Exception as exc:
                cluster_log.append(f"    - ERROR deleting {loser['key']}: {exc}")
                continue
            all_losers_this_run.add(loser["key"])

        if winner_groups:
            try:
                bibdesk.add_groups(winner_pid, list(winner_groups))
                cluster_log.append(f"    - groups merged: {sorted(winner_groups)}")
            except Exception as exc:
                cluster_log.append(f"    - ERROR merging groups: {exc}")

        # trash orphaned loser files (not the swap source, and not still referenced)
        for loser in losers:
            for rp in loser["relpaths"]:
                if swap_from and (loser["key"], rp) == swap_from:
                    cluster_log.append(f"    - file kept (used for swap): `{rp}`")
                    continue
                refs = relpath_refs.get(rp, set())
                still_referenced = bool(refs - all_losers_this_run - {loser["key"]})
                if still_referenced:
                    cluster_log.append(f"    - file kept (still referenced elsewhere): `{rp}`")
                    continue
                full = os.path.join(fpd.BIBDESK_ROOT, rp)
                result = trash_file(full)
                cluster_log.append(f"    - file `{rp}`: {result}")

        print("\n".join(cluster_log))
        log.extend(cluster_log)

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"\nLog written to {LOG_PATH}")


if __name__ == "__main__":
    main()
