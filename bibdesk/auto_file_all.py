#!/usr/bin/env python3
"""
Phase D: apply BibDesk's own "auto file" action to every entry that has a
linked file. This reuses the library's existing, already-in-use naming
template (BDSKLocalFileFormatKey = "%a1/%y%a1_%u1 %t100%e", confirmed from
~/Library/Preferences/edu.ucsd.cs.mmccrack.bibdesk.plist) rather than
inventing a new one — a no-op for already-correctly-named files, and expected
to fix the ones currently missing a proper .pdf suffix.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from apply_arxiv_updates import find_pid_by_citekey
from ads2bibdesk.bibdesk import BibDesk

BIB_PATH = os.path.expanduser("~/research/bibdesk/ioannis.bib")
LOG_PATH = os.path.expanduser("~/research/bibdesk/tools/auto_file_log.md")


def keys_with_linked_files():
    text = open(BIB_PATH, encoding="utf-8").read()
    entries = [e for e in re.split(r"\n(?=@)", text) if e.startswith("@")]
    keys = []
    for e in entries:
        m = re.match(r"@\w+\{([^,]+),", e)
        if m and re.search(r"bdsk-file-\d+\s*=", e):
            keys.append(m.group(1))
    return keys


def main():
    keys = keys_with_linked_files()
    print(f"{len(keys)} entries have a linked file; running 'auto file' on each")

    bibdesk = BibDesk()
    doc_path = bibdesk('return path of first document of application "BibDesk"').stringValue()
    if os.path.realpath(doc_path) != os.path.realpath(BIB_PATH):
        sys.exit(f"BibDesk's front document ({doc_path}) is not {BIB_PATH} — aborting, nothing changed.")
    print(f"Confirmed BibDesk front document: {doc_path}")

    log = ["# auto-file log\n"]
    ok, errors, not_found = 0, 0, 0

    for i, key in enumerate(keys, 1):
        pid = find_pid_by_citekey(bibdesk, key)
        if pid is None:
            log.append(f"- {key}: NOT FOUND in BibDesk, skipped")
            not_found += 1
            continue
        try:
            bibdesk("auto file", pid)
            ok += 1
        except Exception as exc:
            log.append(f"- {key}: ERROR - {exc}")
            errors += 1
        if i % 200 == 0:
            print(f"  ... {i}/{len(keys)} processed ({ok} ok, {errors} errors)")

    log.insert(1, f"Total: {len(keys)}, ok: {ok}, errors: {errors}, not found: {not_found}\n")
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")

    print(f"\nDone. ok={ok} errors={errors} not_found={not_found}")
    print(f"Log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
