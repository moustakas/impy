#!/usr/bin/env python3
"""
Phase 2: apply arXiv-only -> published metadata updates to BibDesk, for the
entries flagged in arxiv_stale_report.md (produced by audit_arxiv_stale.py).

Design: edit publication-venue fields IN PLACE on the existing BibDesk
publication (found by cite key) via AppleScript. Does NOT delete/reimport
the entry and does NOT touch linked files, cite keys, static groups, notes,
or ratings — those are only at risk if the entry is deleted, and it never
is. Only a fixed whitelist of fields is touched:
    journal, volume, number, pages, doi, adsurl, adsnote, month, year
"""
import configparser
import os
import re
import sys

import ads
from ads2bibdesk.bibdesk import BibDesk

BIB_PATH = os.path.expanduser("~/research/bibdesk/ioannis.bib")
CFG_PATH = os.path.expanduser("~/.ads/ads2bibdesk.cfg")
REPORT_PATH = os.path.expanduser("~/research/bibdesk/tools/arxiv_stale_report.md")
LOG_PATH = os.path.expanduser("~/research/bibdesk/tools/arxiv_apply_log.md")

FIELD_WHITELIST = {"journal", "volume", "number", "pages", "doi", "adsurl", "adsnote", "month", "year"}


def load_ads_token():
    cfg = configparser.ConfigParser()
    cfg.read(CFG_PATH)
    token = cfg["default"]["ads_token"]
    if "dev_key" in token:
        sys.exit(f"No real ADS token configured in {CFG_PATH}")
    return token


def parse_report_candidates(path):
    text = open(path, encoding="utf-8").read()
    table = text.split("## Update candidates")[1].split("## Still arXiv-only")[0]
    rows = []
    for line in table.splitlines():
        if not line.startswith("|") or line.startswith("|---") or "cite key" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        rows.append({"key": cols[0], "old_bibcode": cols[2], "new_bibcode": cols[3]})
    return rows


def parse_bibtex_fields(bibtex_text):
    m = re.search(r"@\w+\{[^,]+,", bibtex_text)
    body = bibtex_text[m.end():]
    fields = {}
    i = 0
    n = len(body)
    while i < n:
        m2 = re.match(r"\s*,?\s*([A-Za-z][\w-]*)\s*=\s*", body[i:])
        if not m2:
            break
        name = m2.group(1).lower()
        i += m2.end()
        if i < n and body[i] == "{":
            depth = 1
            j = i + 1
            while depth > 0 and j < n:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            value = body[i + 1:j - 1]
            i = j
        elif i < n and body[i] == '"':
            # ADS bibtex quote-delimits some fields (e.g. title = "{...}"),
            # which can itself contain nested braces.
            depth = 0
            j = i + 1
            while j < n:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                elif body[j] == '"' and depth == 0:
                    break
                j += 1
            value = body[i + 1:j]
            i = j + 1
        else:
            m3 = re.match(r"([^,}]+)", body[i:])
            if not m3:
                break
            value = m3.group(1).strip()
            i += m3.end()
        fields[name] = value.strip()
    return fields


def as_applescript_string(value):
    return value.replace("\\", r"\\").replace('"', r"\"")


def get_field_value(bibdesk, pid, name):
    try:
        val = bibdesk(f'value of field "{name}"', pid)
        return val.stringValue() if val is not None else None
    except Exception:
        return None


def set_field(bibdesk, pid, name, value):
    escaped = as_applescript_string(value)
    exists = bibdesk(f'exists field "{name}"', pid)
    exists_bool = exists.booleanValue() if hasattr(exists, "booleanValue") else bool(exists)
    if not exists_bool:
        bibdesk(f'make new field with properties {{name:"{name}"}}', pid)
    bibdesk(f'set value of field "{name}" to "{escaped}"', pid)


def find_pid_by_citekey(bibdesk, key):
    result = bibdesk(f'return id of first publication whose cite key is "{key}"', error=True)
    value, err = result[0], result[1]
    if err is not None or value is None:
        return None
    return value.stringValue()


def main():
    ads.config.token = load_ads_token()
    candidates = parse_report_candidates(REPORT_PATH)
    print(f"Loaded {len(candidates)} update candidates from {REPORT_PATH}")

    bibdesk = BibDesk()

    doc_path = bibdesk("return path of first document of application \"BibDesk\"").stringValue()
    if os.path.realpath(doc_path) != os.path.realpath(BIB_PATH):
        sys.exit(f"BibDesk's front document ({doc_path}) is not {BIB_PATH} — aborting, nothing changed.")
    print(f"Confirmed BibDesk front document: {doc_path}")

    log_lines = ["# arXiv -> published field-update log\n"]

    for c in candidates:
        key = c["key"]
        pid = find_pid_by_citekey(bibdesk, key)
        if pid is None:
            msg = f"- **{key}**: ERROR — cite key not found in open BibDesk document, skipped"
            print(msg)
            log_lines.append(msg)
            continue

        try:
            bibtex = ads.ExportQuery(bibcodes=c["new_bibcode"], format="bibtex").execute()

            new_fields = parse_bibtex_fields(bibtex)
            to_set = {k: v for k, v in new_fields.items() if k in FIELD_WHITELIST and v}

            changes = []
            for name, value in to_set.items():
                old_value = get_field_value(bibdesk, pid, name)
                if old_value == value:
                    continue  # already correct, no-op
                try:
                    set_field(bibdesk, pid, name, value)
                except Exception as exc:
                    changes.append(f"    - {name}: ERROR setting value ({exc})")
                    continue
                new_value_check = get_field_value(bibdesk, pid, name)
                ok = "OK" if new_value_check == value else f"UNVERIFIED (now reads '{new_value_check}')"
                changes.append(f"    - {name}: `{old_value}` -> `{value}` [{ok}]")

            cite_key_after = bibdesk("cite key", pid).stringValue()
            key_ok = "OK" if cite_key_after == key else f"MISMATCH (now '{cite_key_after}')"

            msg = f"- **{key}** (bibcode {c['old_bibcode']} -> {c['new_bibcode']}), cite key: {key_ok}"
            print(msg)
            log_lines.append(msg)
            log_lines.extend(changes)
        except Exception as exc:
            msg = f"- **{key}**: ERROR — unexpected failure ({exc}), moving on to next entry"
            print(msg)
            log_lines.append(msg)
            continue

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    print(f"\nLog written to {LOG_PATH}")


if __name__ == "__main__":
    main()
