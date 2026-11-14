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
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify as v  # noqa: E402

CASES = HERE / "cases"
ANCHOR = HERE / "anchor.json"


def run(name: str, anchor: dict | None) -> dict:
    entries = v.load_log(CASES / name / "log.jsonl")
    return v.verify(entries, anchor)


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
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
