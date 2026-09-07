#!/usr/bin/env python3
"""
Phase 1 (read-only audit): find BibDesk entries still marked as arXiv-only
preprints and check ADS for a published version.

Writes nothing to ioannis.bib or BibDesk. Reads ~/research/bibdesk/ioannis.bib
as text and queries the ADS API. Output: a markdown report of proposed updates.
"""
import configparser
import os
import re
import sys

import ads

BIB_PATH = os.path.expanduser("~/research/bibdesk/ioannis.bib")
CFG_PATH = os.path.expanduser("~/.ads/ads2bibdesk.cfg")
REPORT_PATH = os.path.expanduser("~/research/bibdesk/tools/arxiv_stale_report.md")


def load_ads_token():
    cfg = configparser.ConfigParser()
    cfg.read(CFG_PATH)
    token = cfg["default"]["ads_token"]
    if "dev_key" in token:
        sys.exit(f"No real ADS token configured in {CFG_PATH}")
    return token


def split_entries(text):
    """Split raw bibtex text into individual @entry blocks (text, not parsed)."""
    parts = re.split(r"\n(?=@)", text)
    return [p for p in parts if p.startswith("@")]


def parse_candidate(entry):
    if "journal = {arXiv e-prints}" not in entry:
        return None
    key_m = re.match(r"@\w+\{([^,]+),", entry)
    eprint_m = re.search(r"^\s*eprint\s*=\s*\{([^}]+)\}", entry, re.M)
    year_m = re.search(r"^\s*year\s*=\s*\{?(\d{4})\}?", entry, re.M)
    adsurl_m = re.search(r"^\s*adsurl\s*=\s*\{([^}]+)\}", entry, re.M)
    if not (key_m and eprint_m):
        return None
    return {
        "key": key_m.group(1),
        "eprint": eprint_m.group(1),
        "year": year_m.group(1) if year_m else "?",
        "old_bibcode": adsurl_m.group(1).rsplit("/", 1)[-1] if adsurl_m else None,
    }


def is_still_arxiv(article):
    # Trust ADS's own publication-venue field rather than parsing the bibcode
    # string — old-style pre-2007 bibcodes use "astro.ph" instead of "arXiv"
    # in the bibcode itself, which a bibcode-pattern check would miss.
    return (article.pub or "").strip() == "arXiv e-prints"


def main():
    ads.config.token = load_ads_token()

    text = open(BIB_PATH, encoding="utf-8").read()
    candidates = [c for e in split_entries(text) if (c := parse_candidate(e))]
    print(f"Found {len(candidates)} candidate arXiv-only entries in {BIB_PATH}")

    rows = []
    for c in candidates:
        try:
            query = ads.SearchQuery(
                identifier=c["eprint"],
                fl=["bibcode", "pub", "volume", "page", "doi", "year", "title",
                    "property", "alternate_bibcode"],
            )
            results = list(query)
        except Exception as exc:
            rows.append({**c, "status": f"ADS query error: {exc}"})
            continue

        if len(results) != 1:
            rows.append({**c, "status": f"{len(results)} ADS matches (expected 1) — skipped"})
            continue

        art = results[0]
        new_bibcode = art.bibcode

        if is_still_arxiv(art):
            rows.append({**c, "status": "still arXiv-only on ADS — no update available"})
            continue

        rows.append({
            **c,
            "status": "PUBLISHED — update available",
            "new_bibcode": new_bibcode,
            "pub": art.pub,
            "volume": art.volume,
            "page": art.page,
            "doi": art.doi,
        })

    stale = [r for r in rows if r["status"] == "PUBLISHED — update available"]
    still_pre = [r for r in rows if "still arXiv-only" in r["status"]]
    errors = [r for r in rows if r not in stale and r not in still_pre]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# arXiv-only entry audit\n\n")
        f.write(f"Total candidates checked: {len(rows)}\n\n")
        f.write(f"- Published, update available: **{len(stale)}**\n")
        f.write(f"- Still arXiv-only on ADS (no action): {len(still_pre)}\n")
        f.write(f"- Skipped / errors: {len(errors)}\n\n")

        f.write("## Update candidates\n\n")
        f.write("| cite key | year | old bibcode | new bibcode | pub | vol | page | doi |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in sorted(stale, key=lambda r: r["year"]):
            f.write(
                f"| {r['key']} | {r['year']} | {r.get('old_bibcode','?')} | "
                f"{r['new_bibcode']} | {r['pub']} | {r.get('volume','')} | "
                f"{r.get('page','')} | {r.get('doi','') or ''} |\n"
            )

        f.write("\n## Still arXiv-only (no action)\n\n")
        for r in still_pre:
            f.write(f"- {r['key']} ({r['year']})\n")

        if errors:
            f.write("\n## Skipped / errors\n\n")
            for r in errors:
                f.write(f"- {r['key']}: {r['status']}\n")

    print(f"Report written to {REPORT_PATH}")
    print(f"  published/update-available: {len(stale)}")
    print(f"  still arXiv-only: {len(still_pre)}")
    print(f"  skipped/errors: {len(errors)}")


if __name__ == "__main__":
    main()
