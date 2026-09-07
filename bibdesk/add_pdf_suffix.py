#!/usr/bin/env python3
"""
Phase D, part 2: fix the ~922 linked PDFs that are missing a ".pdf" suffix.

`auto file` (already run library-wide) turned out NOT to fix this: it derives
its %e (extension) template token from the file's *current* name, so a file
with no extension gets no extension after auto-file either — confirmed by a
live test. What actually works (also tested live): a plain on-disk rename
(same volume, same inode) is enough on its own — BibDesk's linked-file
bookmark resolves by file identity, not by its stored path text, so it picks
up the rename automatically. `auto file` is still called afterward on each
entry purely to refresh the *stored* relativePath text in ioannis.bib to
match reality (our own audit scripts, and BibDesk's own on-disk record, read
that text directly).

Scope: only entries whose current relativePath already resolves directly to
a real, verified-PDF file (confirmed via `file --brief`) are touched. Entries
whose relativePath is already stale/broken (points at a nonexistent path,
e.g. the pre-existing "Copy" folder issue found earlier) are left completely
alone and logged separately — same "skip, don't guess" precedent as the
demaio15a/b cluster in phase C.
"""
import base64
import os
import plistlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from apply_arxiv_updates import find_pid_by_citekey
from ads2bibdesk.bibdesk import BibDesk

BIBDESK_ROOT = os.path.expanduser("~/research/bibdesk")
BIB_PATH = os.path.join(BIBDESK_ROOT, "ioannis.bib")
LOG_PATH = os.path.expanduser("~/research/bibdesk/tools/add_pdf_suffix_log.md")


def find_candidates():
    text = open(BIB_PATH, encoding="utf-8").read()
    entries = [e for e in re.split(r"\n(?=@)", text) if e.startswith("@")]
    clean, stale = [], []
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
        if not rp or rp.lower().endswith(".pdf"):
            continue
        full = os.path.join(BIBDESK_ROOT, rp)
        if os.path.exists(full):
            out = subprocess.run(["file", "--brief", full], capture_output=True, text=True).stdout
            if "PDF" in out:
                clean.append((key, full))
            else:
                stale.append((key, rp, "resolves but not detected as PDF"))
        else:
            stale.append((key, rp, "relativePath does not resolve"))
    return clean, stale


def main():
    clean, stale = find_candidates()
    print(f"{len(clean)} clean candidates to fix, {len(stale)} skipped (stale/non-PDF)")

    bibdesk = BibDesk()
    doc_path = bibdesk('return path of first document of application "BibDesk"').stringValue()
    if os.path.realpath(doc_path) != os.path.realpath(BIB_PATH):
        sys.exit(f"BibDesk's front document ({doc_path}) is not {BIB_PATH} — aborting, nothing changed.")
    print(f"Confirmed BibDesk front document: {doc_path}")

    log = ["# add .pdf suffix log\n",
           f"Total: {len(clean)} to fix, {len(stale)} skipped\n",
           "\n## Skipped (stale link or not detected as PDF)\n"]
    for key, rp, reason in stale:
        log.append(f"- {key}: {reason} (`{rp}`)")
    log.append("\n## Fixed\n")

    ok, errors = 0, 0
    for i, (key, full) in enumerate(clean, 1):
        new_path = full + ".pdf"
        try:
            if os.path.exists(new_path):
                log.append(f"- {key}: ERROR - target already exists, skipped: `{new_path}`")
                errors += 1
                continue
            shutil.move(full, new_path)
            pid = find_pid_by_citekey(bibdesk, key)
            if pid is None:
                log.append(f"- {key}: renamed on disk, but cite key not found in BibDesk to refresh bookmark")
                errors += 1
                continue
            bibdesk("auto file", pid)
            log.append(f"- {key}: OK")
            ok += 1
        except Exception as exc:
            log.append(f"- {key}: ERROR - {exc}")
            errors += 1
        if i % 200 == 0:
            print(f"  ... {i}/{len(clean)} processed ({ok} ok, {errors} errors)")

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"\nDone. ok={ok} errors={errors}")
    print(f"Log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
