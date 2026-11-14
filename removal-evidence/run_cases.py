#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Run every case twice: once with only the log, once against the witness.

The second column is the entire argument. A record and its removal record
removed together, with the log renumbered and every digest recomputed, passes
every local check. It fails the moment the reader holds a head digest published
before the removal happened.

    python3 run_cases.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify as v  # noqa: E402

CASES = HERE / "cases"
ANCHOR = HERE / "anchor.json"


def run(name: str, anchor: dict | None) -> dict:
    entries = v.load_log(CASES / name / "log.jsonl")
    return v.verify(entries, anchor)


def cli(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HERE / "verify.py"), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def guards() -> int:
    """Failures a reader must never get away with: a witness run that silently
    skips the witness, and a crash where a verdict is promised."""
    failures = 0
    rows = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        null_anchor = tmp / "null-anchor.json"
        null_anchor.write_text("null", encoding="utf-8")
        rc, out = cli([str(CASES / "resealed_pair"), "--anchor", str(null_anchor)])
        rows.append(("null anchor rejects", rc == 1 and "E_ANCHOR_UNUSABLE" in out))

        bad_log = tmp / "bad-log"
        bad_log.mkdir()
        (bad_log / "log.jsonl").write_text('{"seq":1,"id":"ev-0001","kind":"action"\n', encoding="utf-8")
        rc, out = cli([str(bad_log)])
        rows.append(("malformed log gives a verdict", rc == 1 and "E_LOG_UNREADABLE" in out and "Traceback" not in out))

        missing_anchor = tmp / "absent.json"
        rc, out = cli([str(CASES / "resealed_pair"), "--anchor", str(missing_anchor)])
        rows.append(("missing anchor file rejects", rc == 1 and "E_ANCHOR_UNREADABLE" in out))

    print("-" * 58)
    for name, ok in rows:
        if not ok:
            failures += 1
        print(f"guard {name:34} {'ok' if ok else 'FAILED'}")
    return failures


def main() -> int:
    expected = json.loads((CASES / "expected.json").read_text(encoding="utf-8"))
    anchor = json.loads(ANCHOR.read_text(encoding="utf-8"))
    failures = 0

    print(f"{'case':24} {'local':6} {'anchored':9} result")
    print("-" * 58)
    for name, want in expected.items():
        local = run(name, None)
        anchored = run(name, anchor)
        ok = (
            local["verdict"] == want["local"]
            and anchored["verdict"] == want["anchored"]
            and all(code in local["codes"] + anchored["codes"] for code in want["codes"])
        )
        if not ok:
            failures += 1
        print(f"{name:24} {local['verdict']:6} {anchored['verdict']:9} {'ok' if ok else 'MISMATCH'}")
        if not ok:
            print(f"  wanted {want}")
            print(f"  local  {local}")
            print(f"  anchor {anchored}")

    print("-" * 58)
    print(f"{len(expected)} cases, {failures} mismatched")
    failures += guards()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
