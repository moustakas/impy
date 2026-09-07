#!/usr/bin/env python3
"""
Phase E: repair the ~100 entries whose linked-file bookmark is stale,
pointing at "../../Copy/research/bibdesk/..." — a leftover from some past
folder restructuring. In every case checked, the real file is already
sitting at the correct, current location; only the stored bookmark is stale.

No network. For each: link the real (already-present) file via
`add POSIX file ... to beginning of linked files`, then `auto file` to
refresh the stored bookmark text. Same mechanism already proven on
conroy15a in phase 3. The old stale bookmark is left as a harmless,
never-resolving second linked-file entry rather than risking an uncertain
AppleScript element-deletion call.
"""
import base64
import os
import plistlib
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from apply_arxiv_updates import find_pid_by_citekey
from ads2bibdesk.bibdesk import BibDesk

BIBDESK_ROOT = os.path.expanduser("~/research/bibdesk")
BIB_PATH = os.path.join(BIBDESK_ROOT, "ioannis.bib")
LOG_PATH = os.path.expanduser("~/research/bibdesk/tools/repair_copy_links_log.md")
STALE_PREFIX = "../../Copy/research/bibdesk/"


def as_applescript_string(value):
    return value.replace("\\", r"\\").replace('"', r"\"")


def find_candidates():
    text = open(BIB_PATH, encoding="utf-8").read()
    entries = [e for e in re.split(r"\n(?=@)", text) if e.startswith("@")]
    candidates = []
    for e in entries:
        key_m = re.match(r"@\w+\{([^,]+),", e)
        if not key_m:
            continue
        key = key_m.group(1)
        m = re.search(r"bdsk-file-1\s*=\s*\{([^}]+)\}", e)
        if not m:
            continue
        try:
            rp = plistlib.loads(base64.b64decode(m.group(1))).get("relativePath")
        except Exception:
            continue
        if not rp or not rp.startswith(STALE_PREFIX):
            continue
        full_current = os.path.join(BIBDESK_ROOT, rp)
        if os.path.exists(full_current):
            continue  # not actually stale
        stripped = rp[len(STALE_PREFIX):]
        full_real = os.path.join(BIBDESK_ROOT, stripped)
        if os.path.exists(full_real):
            candidates.append((key, full_real))
    return candidates


def main():
    candidates = find_candidates()
    print(f"{len(candidates)} repairable stale-link entries found")

    bibdesk = BibDesk()
    doc_path = bibdesk('return path of first document of application "BibDesk"').stringValue()
    if os.path.realpath(doc_path) != os.path.realpath(BIB_PATH):
        sys.exit(f"BibDesk's front document ({doc_path}) is not {BIB_PATH} — aborting, nothing changed.")
    print(f"Confirmed BibDesk front document: {doc_path}")

    log = ["# repair Copy-links log\n"]
    ok, errors = 0, 0
    for i, (key, full_real) in enumerate(candidates, 1):
        pid = find_pid_by_citekey(bibdesk, key)
        if pid is None:
            log.append(f"- {key}: ERROR - cite key not found in BibDesk")
            errors += 1
            continue
        escaped = as_applescript_string(full_real)
        try:
            result = bibdesk(f'add POSIX file "{escaped}" to beginning of linked files', pid, error=True)
            if result[1] is not None:
                raise RuntimeError(f"AppleScript error: {result[1]}")
            bibdesk("auto file", pid)
        except Exception as exc:
            log.append(f"- {key}: ERROR - {exc}")
            errors += 1
            continue

        # verify: does the entry now actually resolve to a working file?
        after = bibdesk("POSIX path of linked files", pid, strlist=True)
        if any(p and os.path.exists(p) for p in after):
            log.append(f"- {key}: OK -> `{full_real}`")
            ok += 1
        else:
            log.append(f"- {key}: ERROR - add succeeded but no linked file resolves afterward "
                        f"(paths reported: {after})")
            errors += 1
        if i % 25 == 0:
            print(f"  ... {i}/{len(candidates)} ({ok} ok, {errors} errors)")

    log.insert(1, f"Total: {len(candidates)}, ok: {ok}, errors: {errors}\n")
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"\nDone. ok={ok} errors={errors}")
    print(f"Log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
