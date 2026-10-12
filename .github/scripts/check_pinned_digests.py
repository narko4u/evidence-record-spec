#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Verify the pinned digests in EVIDENCE-OF-INDEPENDENCE.md against the shipped bytes.

    python3 .github/scripts/check_pinned_digests.py
    python3 .github/scripts/check_pinned_digests.py --refresh

Exit 0 means every pinned digest reproduces from the working tree. Exit 1 means a
covered file changed, is missing or is pinned without being covered. The record
must then be refreshed in the same commit as the change it describes.

`--refresh` rewrites the hash column only. The date line and the narrative around it
stay a human edit, because a record that rewrites its own story is not a record.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

RECORD = Path("EVIDENCE-OF-INDEPENDENCE.md")
CORPUS = "grade-floor"
CORPUS_ROW = "grade-floor/ (corpus digest)"

# The covered set is a deliberate list, not a directory walk: a file joins the
# record when we decide it carries a claim, so an unrelated new file cannot
# silently enter the provenance record.
COVERED = [
    "README.md",
    "LICENSE",
    "NOTICE",
    "CITATION.cff",
    "VERIFIABILITY-OVERVIEW.md",
    "CROSSWALK.md",
    "IMPLEMENTATIONS.md",
    "AAIF-SUBMISSION-DRAFT.md",
    "evidence-record-0.1.schema.json",
    "evidence-appraisal-0.1.schema.json",
    "validate_evidence.py",
    "evidence_grade_rules.py",
    "grade_floor.py",
    "gen_cases.py",
]

ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*`([0-9a-f]{64})`\s*\|")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_digest() -> str:
    """One digest over the corpus, as its sorted member list.

    A directory is not a byte string, so the corpus is pinned as
    `path<space>digest` per line, in sorted order, then hashed.
    """
    lines = []
    for p in sorted(Path(CORPUS).rglob("*")):
        if p.is_file():
            lines.append(f"{p.as_posix()} {sha256_file(p)}")
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def expected() -> dict[str, str]:
    out: dict[str, str] = {}
    for name in COVERED:
        out[name] = sha256_file(Path(name))
    for p in sorted(Path("samples").glob("*.json")):
        out[p.as_posix()] = sha256_file(p)
    out[CORPUS_ROW] = corpus_digest()
    return out


def pinned_rows(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in text.splitlines():
        m = ROW.match(line)
        if m:
            rows[m.group(1)] = m.group(2)
    return rows


def main() -> int:
    refresh = "--refresh" in sys.argv
    want = expected()
    text = RECORD.read_text(encoding="utf-8")
    rows = pinned_rows(text)

    stale = sorted(n for n, d in want.items() if n in rows and rows[n] != d)
    missing = sorted(n for n in want if n not in rows)
    orphan = sorted(n for n in rows if n not in want)

    if refresh and (stale or missing):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            m = ROW.match(line)
            if not m:
                continue
            name = m.group(1)
            if name in want and rows[name] != want[name]:
                lines[i] = line.replace(rows[name], want[name])
        RECORD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"refresh: rewrote {len(stale)} hash row(s)")
        for n in stale:
            print(f"  {n} -> {want[n]}")
        if missing:
            print("refresh: still unpinned, add the rows by hand:")
            for n in missing:
                print(f"  | {n} | `{want[n]}` |")
        text = RECORD.read_text(encoding="utf-8")
        rows = pinned_rows(text)
        stale = sorted(n for n, d in want.items() if n in rows and rows[n] != d)

    if stale:
        print(f"PIN FAIL: {len(stale)} covered file(s) changed since the record was pinned")
        for n in stale:
            print(f"  {n}: pinned {rows[n][:12]}... actual {want[n][:12]}...")
    if missing:
        print(f"note: {len(missing)} covered file(s) not yet pinned: {', '.join(missing)}")
    if orphan:
        print(f"note: {len(orphan)} pinned row(s) not in the covered set: {', '.join(orphan)}")
    if stale:
        print("run: python3 .github/scripts/check_pinned_digests.py --refresh")
        return 1
    print(f"pinned digests reproduce: {len(rows)} rows over {len(want)} covered artefacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
