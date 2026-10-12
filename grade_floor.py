#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Appraise evidence records against the E0-E4 grade floor and report the rung
each one reaches with a named reason.

Standard library only: no install step, no network call, no account, no service.
The grade floor is the one in ``evidence_grade_rules.py``, the same rule set
``validate_evidence.py`` caps records against, so a checker and a validator
cannot disagree about a rung.

Usage:
    python3 grade_floor.py grade-floor/cases/
    python3 grade_floor.py grade-floor/cases/e3-corroborated/case.json
    python3 grade_floor.py --json grade-floor/cases/

A case is a JSON file with a ``record`` and the ``expect``ed decision. Exit code
0 means every case behaved as expected, 1 means at least one did not.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evidence_grade_rules import (
    CLAIM_MIN_GRADE,
    GATE_NO_INDEPENDENT_EVIDENCE,
    GATE_NO_INDEPENDENT_PARTY,
    GATE_NOT_ANCHORABLE,
    GATE_SOURCE_NOT_ANCHORABLE,
    GATE_UNKNOWN_SOURCE,
    GRADE_ORDER,
    derive_grade_ceiling,
    grade_gates,
)

REASON_DERIVED = "grade_derived"
REASON_UNKNOWN_SOURCE = "unknown_observation_source"
REASON_NO_INDEPENDENT_EVIDENCE = "no_independent_evidence_caps_at_e0"
REASON_NO_INDEPENDENT_PARTY = "e3_requires_an_independent_party"
REASON_NO_ANCHOR = "e4_requires_timestamp_chain_link_and_independent_verifier"
REASON_SOURCE_NOT_ANCHORABLE = "e4_unreachable_for_this_observation_source"
REASON_UNKNOWN_CLAIM = "unknown_claim"

# The gate names live in the rules module, so the names a record is refused
# with and the names a corpus expects cannot drift apart.
GATE_REASON = {
    GATE_UNKNOWN_SOURCE: REASON_UNKNOWN_SOURCE,
    GATE_NO_INDEPENDENT_EVIDENCE: REASON_NO_INDEPENDENT_EVIDENCE,
    GATE_NO_INDEPENDENT_PARTY: REASON_NO_INDEPENDENT_PARTY,
    GATE_NOT_ANCHORABLE: REASON_NO_ANCHOR,
    GATE_SOURCE_NOT_ANCHORABLE: REASON_SOURCE_NOT_ANCHORABLE,
}


def explain(record: dict) -> list[str]:
    """The gates that actually bit, in the order they are applied.

    Read from the rules module rather than recomputed here, so an explanation
    of a record cannot disagree with the rung the record was given. An empty
    list means nothing capped the record below the headroom its observation
    source allows.
    """
    return [GATE_REASON[g] for g in grade_gates(record)]


def claim_floor_reasons(record: dict, derived: str) -> tuple[list[str], bool]:
    """Reasons a claim is not supported and whether the claim set is closed.

    The claim floor is what stops a producer asserting more than its own
    observation supports. Returning ``False`` for closure means an unrecognised
    claim was found, which fails closed rather than passing silently.
    """
    reasons: list[str] = []
    closed = True
    for c in record.get("claims") or []:
        claim = c.get("claim") if isinstance(c, dict) else None
        if claim not in CLAIM_MIN_GRADE:
            closed = False
            reasons.append(f"{REASON_UNKNOWN_CLAIM}:{claim}")
            continue
        floor = CLAIM_MIN_GRADE[claim]
        if GRADE_ORDER.index(derived) < GRADE_ORDER.index(floor):
            reasons.append(f"claim_floor_below_{floor.lower()}:{claim}")
        if claim == "operationally-conformant":
            state = (record.get("reconciliation") or {}).get("state")
            if state != "agreement":
                reasons.append(f"claim_requires_agreement:{claim}={state}")
    return reasons, closed


def appraise(record: dict) -> dict:
    """Appraise one record: the rung it reaches and whether it may stand.

    Two different things are reported and they must not be conflated:

      - ``caps``  the gates that bit, each of which caps the record below the
        headroom its observation source allows. A cap is not a refusal: a
        boundary observation with no independent party is a perfectly good E2
        record.
      - ``decision`` whether the record's own claims are supported at the rung
        it reached. This is where a refusal comes from.
    """
    derived = derive_grade_ceiling(record)
    caps = explain(record)
    floor_reasons, closed = claim_floor_reasons(record, derived)
    reasons = list(floor_reasons)
    # Closed vocabulary: an unrecognised observation source is a refusal, not a
    # rung. The validator fails it at the schema layer; here it fails closed too.
    if REASON_UNKNOWN_SOURCE in caps:
        reasons.insert(0, REASON_UNKNOWN_SOURCE)
    rejected = bool(reasons) or not closed
    return {
        "decision": "rejected" if rejected else "accepted",
        "derived_grade": derived,
        "reason": reasons if reasons else [REASON_DERIVED],
        "caps": caps,
        "claim_set_closed": closed,
    }


def load_cases(paths: list[str]) -> list[tuple[str, dict]]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.rglob("case.json")))
        else:
            files.append(path)
    cases = []
    for f in files:
        try:
            doc = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            print(f"FAIL {f} invalid JSON: {e}")
            continue
        cases.append((doc.get("case_id") or f.parent.name, doc))
    return cases


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Appraise records against the E0-E4 grade floor.")
    parser.add_argument("paths", nargs="+", help="case.json files, case directories or a corpus root")
    parser.add_argument("--json", action="store_true", help="print one JSON object per case")
    args = parser.parse_args(argv)

    cases = load_cases(args.paths)
    if not cases:
        print("no cases found: nothing was appraised, which is not a pass")
        return 1

    failed = 0
    for case_id, doc in cases:
        record = doc.get("record") or {}
        got = appraise(record)
        exp = doc.get("expect") or {}
        ok = got["decision"] == exp.get("decision") and (
            not exp.get("derived_grade") or got["derived_grade"] == exp["derived_grade"]
        )
        want_caps = set(exp.get("caps") or [])
        if want_caps and not want_caps.issubset(set(got["caps"])):
            ok = False
        # A refusal must name the rule that refused it, not merely refuse.
        if exp.get("reason_contains") and not any(
            exp["reason_contains"] in r for r in got["reason"]
        ):
            ok = False
        if args.json:
            print(json.dumps({"case_id": case_id, **got, "expect": exp, "ok": ok}, sort_keys=True))
        else:
            print(f"{'OK  ' if ok else 'FAIL'} {case_id}  derived={got['derived_grade']}  {', '.join(got['reason'])}")
            if not ok:
                print(f"     expected {exp.get('decision')} at {exp.get('derived_grade') or 'any rung'}")
                print(f"     caps seen: {', '.join(got['caps']) or 'none'}")
                print(f"     caps wanted: {', '.join(sorted(want_caps)) or 'none'}")
        if not ok:
            failed += 1

    print(f"\n{len(cases) - failed}/{len(cases)} cases behaved as expected")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
