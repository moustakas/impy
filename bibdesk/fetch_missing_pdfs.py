#!/usr/bin/env python3
"""
Phase G: fetch a PDF for entries that currently have none (or whose only
linked file is unrecoverably stale). Priority favors *getting something*
over the ideal source: arXiv first (always free, no paywall), then whatever
else ADS reports as available. Reuses ads2bibdesk's own multi-source fetch
(process_pdf) rather than re-deriving fetch logic.

Politeness / rate-limit safety (explicitly requested):
  - a delay after every ADS API call (search or export)
  - a delay between every candidate entry's fetch attempt
  - checks ADS's own rate-limit headers after each query and backs off (or
    stops cleanly) rather than hammering through a real limit
"""
import base64
import configparser
import os
import plistlib
import re
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
from apply_arxiv_updates import find_pid_by_citekey
from ads2bibdesk.ads2bibdesk import process_pdf
from ads2bibdesk.bibdesk import BibDesk
from ads2bibdesk.prefs import Preferences

BIBDESK_ROOT = os.path.expanduser("~/research/bibdesk")
BIB_PATH = os.path.join(BIBDESK_ROOT, "ioannis.bib")
LOG_PATH = os.path.expanduser("~/research/bibdesk/tools/fetch_missing_pdfs_log.md")
CFG_PATH = os.path.expanduser("~/.ads/ads2bibdesk.cfg")

ADS_QUERY_DELAY = 1.5     # seconds, after every ADS API call
ENTRY_DELAY = 2.0         # seconds, between candidate entries
MIN_REMAINING_RATELIMIT = 50  # stop cleanly if ADS reports fewer requests left

ESOURCE_TYPES = ["eprint_pdf", "pub_pdf", "ads_pdf", "author_pdf"]


def load_ads_token():
    cfg = configparser.ConfigParser()
    cfg.read(CFG_PATH)
    token = cfg["default"]["ads_token"]
    if "dev_key" in token:
        sys.exit(f"No real ADS token configured in {CFG_PATH}")
    return token


def find_candidates():
    text = open(BIB_PATH, encoding="utf-8").read()
    entries = [e for e in re.split(r"\n(?=@)", text) if e.startswith("@")]
    candidates = []
    for e in entries:
        key_m = re.match(r"@\w+\{([^,]+),", e)
        if not key_m:
            continue
        key = key_m.group(1)
        has_working_file = False
        for m in re.finditer(r"bdsk-file-\d+\s*=\s*\{([^}]+)\}", e):
            try:
                rp = plistlib.loads(base64.b64decode(m.group(1))).get("relativePath")
            except Exception:
                continue
            if rp and os.path.exists(os.path.join(BIBDESK_ROOT, rp)):
                has_working_file = True
                break
        if has_working_file:
            continue
        adsurl_m = re.search(r"^\s*adsurl\s*=\s*\{[^}]*abs/([^}]+)\}", e, re.M)
        bibcode = adsurl_m.group(1) if adsurl_m else None
        candidates.append((key, bibcode))
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
    no_bibcode = [k for k, b in candidates if b is None]
    fetchable = [(k, b) for k, b in candidates if b is not None]
    print(f"{len(candidates)} candidates total; {len(no_bibcode)} have no adsurl (skipped); "
          f"{len(fetchable)} to attempt")

    bibdesk = BibDesk()
    doc_path = bibdesk('return path of first document of application "BibDesk"').stringValue()
    if os.path.realpath(doc_path) != os.path.realpath(BIB_PATH):
        sys.exit(f"BibDesk's front document ({doc_path}) is not {BIB_PATH} — aborting, nothing changed.")
    print(f"Confirmed BibDesk front document: {doc_path}")

    log = ["# fetch missing PDFs log\n",
           f"Total candidates: {len(candidates)}, no adsurl (skipped): {len(no_bibcode)}, "
           f"attempted: {len(fetchable)}\n",
           "\n## Skipped (no adsurl)\n"]
    log.extend(f"- {k}" for k in no_bibcode)
    log.append("\n## Attempts\n")

    fetched, failed, errors = 0, 0, 0
    for i, (key, bibcode) in enumerate(fetchable, 1):
        print(f"[{i}/{len(fetchable)}] {key} ...", flush=True)
        try:
            query = ads.SearchQuery(identifier=bibcode, fl=["bibcode", "esources", "title"])
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
            log.append(f"- {key}: no PDF found via {ESOURCE_TYPES}")
            failed += 1
            time.sleep(ENTRY_DELAY)
            continue

        pid = find_pid_by_citekey(bibdesk, key)
        if pid is None:
            log.append(f"- {key}: fetched a PDF but cite key not found in BibDesk")
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
                log.append(f"- {key}: OK - fetched and linked")
                fetched += 1
            else:
                log.append(f"- {key}: ERROR - add succeeded but no linked file resolves "
                            f"afterward (paths reported: {after})")
                errors += 1
        except Exception as exc:
            log.append(f"- {key}: ERROR - fetched but failed to link: {exc}")
            errors += 1
        finally:
            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)  # auto file copies it in; clean up the temp download

        if i % 10 == 0:
            print(f"  ... {i}/{len(fetchable)} (fetched={fetched} failed={failed} errors={errors})")
        time.sleep(ENTRY_DELAY)

    log.insert(2, f"Result: fetched={fetched}, no-pdf-found={failed}, errors={errors}\n")
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"\nDone. fetched={fetched} failed={failed} errors={errors}")
    print(f"Log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
