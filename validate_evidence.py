#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Validate evidence records against evidence-record-0.1.schema.json.

Two layers:
1. Schema conformance (JSON Schema, draft 2020-12).
2. Semantic consistency (things the schema cannot express): basis must
   match vantage/method composition, derived records must carry provenance,
   E-grades require matching integrity markers, and receipt claims must be
   supported by records that could plausibly back them.

The validator is deliberately strict: an unrecognised value is a failure,
not a new rung, matching the closed-vocabulary rule established in the
standards discussion for verification basis derivation.
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.stderr.write("Requires jsonschema: pip install jsonschema\n")
    sys.exit(2)

HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE / "evidence-record-0.1.schema.json"

# Grade requires at least this much integrity presence.
GRADE_MIN_INTEGRITY = {
    "E0": 0,
    "E1": 1,
    "E2": 2,
    "E3": 3,
    "E4": 3,
}

# Claims that require an E-grade at or above this floor.
CLAIM_MIN_GRADE = {
    "emission-conformant": "E1",
    "operationally-conformant": "E3",
}

GRADE_ORDER = ["E0", "E1", "E2", "E3", "E4"]


def semantic_errors(record: dict) -> list[str]:
    errors = []

    # 1. basis must equal {vantage}_{method}
    vantage = record.get("verification", {}).get("vantage")
    method = record.get("verification", {}).get("method")
    basis = record.get("verification", {}).get("basis")
    if vantage and method and basis:
        expected = f"{vantage}_{method}"
        if basis != expected:
            errors.append(
                f"verification.basis '{basis}' does not match composed "
                f"'{expected}' from vantage+method"
            )

    # 2. derived observations must carry provenance
    obs = record.get("observation", {})
    if obs.get("relationship") == "derived":
        if not record.get("provenance"):
            errors.append("observation.relationship=derived requires non-empty provenance")

    # 3. grade vs integrity markers
    grade = record.get("grade")
    integrity = record.get("integrity", {})
    if grade:
        markers = sum(1 for m in ("signed", "chain_linked", "timestamped") if integrity.get(m))
        min_markers = GRADE_MIN_INTEGRITY.get(grade, 0)
        if markers < min_markers:
            errors.append(
                f"grade {grade} requires at least {min_markers} integrity "
                f"marker(s), record has {markers}"
            )
        if grade == "E4":
            if not integrity.get("timestamped"):
                errors.append("E4 requires an external trusted timestamp marker")
            if not integrity.get("chain_linked"):
                errors.append("E4 requires chain-linking marker")
            if not integrity.get("verifiable_by"):
                errors.append("E4 requires at least one independent verifier identifier")

    # 4. receipt claims vs grade floor
    claims = record.get("claims") or []
    for c in claims:
        claim = c.get("claim")
        floor = CLAIM_MIN_GRADE.get(claim)
        if floor and grade and GRADE_ORDER.index(grade) < GRADE_ORDER.index(floor):
            errors.append(
                f"claim '{claim}' requires grade >= {floor}, record is {grade}"
            )
        if not c.get("evidence"):
            errors.append(f"claim '{claim}' must cite supporting evidence record IDs")

    # 5. reconciliation state is explicit when both claim and observation present
    rec = record.get("reconciliation") or {}
    if rec and rec.get("state") not in ("agreement", "contradiction", "no_independent_evidence"):
        errors.append(f"reconciliation.state '{rec.get('state')}' is not a valid state")

    return errors


def validate_file(path: Path, schema: dict, verbose: bool = False) -> tuple[bool, list[str]]:
    try:
        record = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return False, [f"invalid JSON: {e}"]

    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.ValidationError as e:
        return False, [f"schema: {e.message} (at {'/'.join(str(p) for p in e.path) or '$'})"]

    sem = semantic_errors(record)
    return (not sem), sem


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate evidence records against the evidence-record schema."
    )
    parser.add_argument("paths", nargs="+", help="record JSON files, or a directory")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="path to schema JSON")
    args = parser.parse_args(argv)

    schema = json.loads(Path(args.schema).read_text())

    files: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)

    failed = 0
    for f in files:
        ok, errors = validate_file(f, schema)
        if ok:
            print(f"OK   {f.name}")
        else:
            failed += 1
            print(f"FAIL {f.name}")
            for e in errors:
                print(f"     - {e}")

    print(f"\n{len(files) - failed}/{len(files)} records valid")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
