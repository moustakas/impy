#!/usr/bin/env python3
"""
Phase H: attempt to upgrade entries whose metadata is "published" but whose
linked file is still the arXiv preprint. Priority order deliberately
excludes arXiv (the whole point is finding something better). On success,
the new file is classified (reusing phase 3's pdftotext-based classifier) to
confirm it's actually published-looking before accepting it, then the old
arXiv file is moved to Trash (not deleted permanently). On failure, the
existing file is left untouched — expected for most non-open-access venues
given no institutional proxy is configured.

Politeness / rate-limit safety: same as fetch_missing_pdfs.py — a delay
after every ADS call, a delay between entries, and a stop-if-low check on
ADS's own reported rate-limit remaining.
"""
import base64
import configparser
import os
import plistlib
import re
import subprocess
import sys
import time

import requests

# ads2bibdesk's process_pdf() calls requests.get() with no timeout, so a
# single unresponsive server can hang the whole batch indefinitely. Patch a
# default timeout in for every requests.get call made anywhere in this
# process (including inside process_pdf), rather than editing the installed
# package.
_original_requests_get = requests.get


def _requests_get_with_timeout(*args, **kwargs):
    kwargs.setdefault("timeout", 30)
    return _original_requests_get(*args, **kwargs)


requests.get = _requests_get_with_timeout

sys.path.insert(0, os.path.dirname(__file__))
import ads
import find_pdf_duplicates as fpd
from apply_arxiv_updates import find_pid_by_citekey
from ads2bibdesk.ads2bibdesk import process_pdf
from ads2bibdesk.bibdesk import BibDesk
from ads2bibdesk.prefs import Preferences

BIBDESK_ROOT = fpd.BIBDESK_ROOT
BIB_PATH = fpd.BIB_PATH
LOG_PATH = os.path.expanduser("~/research/bibdesk/tools/upgrade_arxiv_pdfs_log.md")
CFG_PATH = os.path.expanduser("~/.ads/ads2bibdesk.cfg")

ADS_QUERY_DELAY = 1.5
ENTRY_DELAY = 2.0
MIN_REMAINING_RATELIMIT = 50

ESOURCE_TYPES = ["pub_pdf", "pub_html", "ads_pdf", "author_pdf"]


def load_ads_token():
    cfg = configparser.ConfigParser()
    cfg.read(CFG_PATH)
    token = cfg["default"]["ads_token"]
    if "dev_key" in token:
        sys.exit(f"No real ADS token configured in {CFG_PATH}")
    return token


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


def find_candidates():
    text = open(BIB_PATH, encoding="utf-8").read()
    entries = [e for e in re.split(r"\n(?=@)", text) if e.startswith("@")]
    candidates = []
    for e in entries:
        key_m = re.match(r"@\w+\{([^,]+),", e)
        if not key_m:
            continue
        key = key_m.group(1)
        journal_m = re.search(r"^\s*journal\s*=\s*\{([^}]*)\}", e, re.M)
        journal = journal_m.group(1).strip() if journal_m else ""
        if not fpd.is_published(journal):
            continue
        m = re.search(r"bdsk-file-1\s*=\s*\{([^}]+)\}", e)
        if not m:
            continue
        try:
            rp = plistlib.loads(base64.b64decode(m.group(1))).get("relativePath")
        except Exception:
            continue
        if not rp:
            continue
        full = os.path.join(BIBDESK_ROOT, rp)
        if not os.path.exists(full):
            continue
        doi_m = re.search(r"^\s*doi\s*=\s*\{([^}]*)\}", e, re.M)
        doi = doi_m.group(1) if doi_m else None
        adsurl_m = re.search(r"^\s*adsurl\s*=\s*\{[^}]*abs/([^}]+)\}", e, re.M)
        bibcode = adsurl_m.group(1) if adsurl_m else None
        if fpd.classify_pdf(full, doi) == "arxiv" and bibcode:
            candidates.append((key, bibcode, full))
    return candidates


def check_ratelimit(response):
    try:
        limits = response.get_ratelimits()
        remaining = int(limits.get("remaining", 9999))
        if remaining < MIN_REMAINING_RATELIMIT:
            print(f"ADS rate limit nearly exhausted ({remaining} remaining) — stopping cleanly.")
            return False
    except Exception:
        pass
    return True


def main():
    ads.config.token = load_ads_token()
    prefs = Preferences().prefs

    candidates = find_candidates()
    print(f"{len(candidates)} arXiv-only-file candidates to attempt upgrading")

    bibdesk = BibDesk()
    doc_path = bibdesk('return path of first document of application "BibDesk"').stringValue()
    if os.path.realpath(doc_path) != os.path.realpath(BIB_PATH):
        sys.exit(f"BibDesk's front document ({doc_path}) is not {BIB_PATH} — aborting, nothing changed.")
    print(f"Confirmed BibDesk front document: {doc_path}")

    log = ["# upgrade arXiv PDFs log\n"]
    upgraded, no_alt, errors = 0, 0, 0

    for i, (key, bibcode, old_full) in enumerate(candidates, 1):
        print(f"[{i}/{len(candidates)}] {key} ...", flush=True)
        try:
            query = ads.SearchQuery(identifier=bibcode, fl=["bibcode", "esources", "doi"])
            results = list(query)
            if not check_ratelimit(query.response):
                log.append(f"- {key}: STOPPED - ADS rate limit nearly exhausted")
                break
            time.sleep(ADS_QUERY_DELAY)
        except Exception as exc:
            log.append(f"- {key}: ERROR - ADS query failed: {exc}")
            errors += 1
            time.sleep(ADS_QUERY_DELAY)
            continue

        if len(results) != 1:
            log.append(f"- {key}: SKIPPED - {len(results)} ADS matches for bibcode {bibcode}")
            time.sleep(ENTRY_DELAY)
            continue

        article = results[0]
        doi = (article.doi[0] if getattr(article, "doi", None) else None)
        try:
            pdf_filename, pdf_status = process_pdf(
                article.bibcode, article.esources, prefs=prefs, esource_types=ESOURCE_TYPES
            )
        except Exception as exc:
            log.append(f"- {key}: ERROR - fetch attempt raised {exc!r}, skipping")
            errors += 1
            time.sleep(ENTRY_DELAY)
            continue

        if not pdf_status:
            log.append(f"- {key}: no open-access alternative found via {ESOURCE_TYPES}")
            no_alt += 1
            time.sleep(ENTRY_DELAY)
            continue

        cls = fpd.classify_pdf(pdf_filename, doi)
        if cls != "published":
            log.append(f"- {key}: fetched a file but it classified as '{cls}', not 'published' "
                        f"- discarding, leaving existing arXiv file in place")
            os.remove(pdf_filename)
            no_alt += 1
            time.sleep(ENTRY_DELAY)
            continue

        pid = find_pid_by_citekey(bibdesk, key)
        if pid is None:
            log.append(f"- {key}: fetched a good PDF but cite key not found in BibDesk")
            errors += 1
            os.remove(pdf_filename)
            time.sleep(ENTRY_DELAY)
            continue

        try:
            result = bibdesk(f'add POSIX file "{pdf_filename}" to beginning of linked files', pid, error=True)
            if result[1] is not None:
                raise RuntimeError(f"AppleScript error: {result[1]}")
            bibdesk("auto file", pid)
            after = bibdesk("POSIX path of linked files", pid, strlist=True)
            if any(p and os.path.exists(p) for p in after):
                trash_result = trash_file(old_full)
                log.append(f"- {key}: OK - upgraded to published PDF; old arXiv file: {trash_result}")
                upgraded += 1
            else:
                log.append(f"- {key}: ERROR - add succeeded but no linked file resolves "
                            f"afterward; old file left in place")
                errors += 1
        except Exception as exc:
            log.append(f"- {key}: ERROR - fetched a good PDF but failed to link: {exc}")
            errors += 1
        finally:
            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)

        if i % 10 == 0:
            print(f"  ... {i}/{len(candidates)} (upgraded={upgraded} no_alt={no_alt} errors={errors})")
        time.sleep(ENTRY_DELAY)

    log.insert(1, f"Total: {len(candidates)}, upgraded: {upgraded}, no alternative found: {no_alt}, "
                  f"errors: {errors}\n")
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"\nDone. upgraded={upgraded} no_alt={no_alt} errors={errors}")
    print(f"Log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
