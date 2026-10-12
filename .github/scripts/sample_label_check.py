#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Check that every sample label agrees with the rules that grade it.

A sample file name states the rung the record's own observation supports, so a
stale name is a published claim that the rule set contradicts. That is exactly
what this gate exists to catch: the label and the rules must be derived from
the same place, or a reader cannot trust either.

An appraisal sample states the grade a verifier concluded, which must not be
above the ceiling of the record it cites.

    python3 .github/scripts/sample_label_check.py

Exit 0 when every label agrees, 1 when any does not. Standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

from evidence_grade_rules import GRADE_ORDER, derive_grade_ceiling  # noqa: E402

SAMPLE_LABEL = re.compile(r"^(er|ea)-\d+-e([0-4])-")


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def record_ceiling(record_id: str, records: dict[str, dict]) -> str | None:
    """The ceiling of the record an appraisal cites, by record_id."""
    subject = records.get(record_id)
    return derive_grade_ceiling(subject) if subject else None


def main() -> int:
    samples = sorted((ROOT / "samples").glob("*.json"))
    if not samples:
        print("no samples found: nothing was checked, which is not a pass")
        return 1

    records = {}
    for path in samples:
        doc = load(path)
        if "record_id" in doc:
            records[doc["record_id"]] = doc

    findings: list[str] = []
    checked = 0
    for path in samples:
        match = SAMPLE_LABEL.match(path.name)
        if not match:
            print(f"FAIL {path.name} has no rung in its name, which is not a pass")
            return 1
        family, digit = match.group(1), match.group(2)
        stated = f"E{digit}"
        doc = load(path)
        checked += 1

        if family == "er":
            derived = derive_grade_ceiling(doc)
            if stated != derived:
                findings.append(
                    f"{path.name}: name says {stated}, the rules derive {derived}"
                )
        else:
            concluded = str(doc.get("e_grade") or "")
            subject_id = str((doc.get("subject_record") or {}).get("record_id") or "")
            ceiling = record_ceiling(subject_id, records)
            if stated != concluded:
                findings.append(
                    f"{path.name}: name says {stated}, the appraisal concludes {concluded}"
                )
            if ceiling and concluded and GRADE_ORDER.index(concluded) > GRADE_ORDER.index(ceiling):
                findings.append(
                    f"{path.name}: concludes {concluded} on {subject_id}, above its ceiling {ceiling}"
                )

    if findings:
        print(f"FAIL {len(findings)} label(s) disagree with the rules:")
        for f in findings:
            print(f"  - {f}")
        return 1

    print(f"OK: {checked} sample labels agree with the rules that grade them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
