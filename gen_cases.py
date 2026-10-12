#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Generate the grade floor corpus deterministically.

Every case is one record plus the decision the published rules say it earns.
Expectations are authored here from the rule text, never computed from the
implementation, so the corpus can disagree with the runner and that disagreement
is the point. Re-running rewrites every case byte for byte.

This repository ships the floor: one accepted case for each rung and a claim
carried at a rung that supports it. The near-miss cases that decide where the
line falls between adjacent rungs are held outside this repository on purpose,
so the published set describes what each rung means without publishing the edge
decisions.

    python3 gen_cases.py
    python3 grade_floor.py grade-floor/cases/
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES_DIR = HERE / "grade-floor" / "cases"
MANIFEST = HERE / "grade-floor" / "MANIFEST.json"


def sample(name: str) -> dict:
    return json.loads((HERE / "samples" / name).read_text())


def with_claim(record: dict, claim: str) -> dict:
    rec = copy.deepcopy(record)
    rec["claims"] = [{"claim": claim, "evidence": [rec.get("record_id") or "case"]}]
    return rec


def framework_observed() -> dict:
    """A framework observation: the lowest source that is not the actor's own."""
    rec = sample("er-00001-e0-self-report.json")
    rec["record_id"] = "gf-00004"
    rec["observation"] = {"source": "framework", "relationship": "direct", "directness": "direct_observation"}
    rec["verification"] = {
        "vantage": "artifact",
        "method": "intercepted",
        "basis": "artifact_intercepted",
        "basis_engines": ["framework"],
    }
    rec["claims"] = []
    rec["reconciliation"] = {"agent_claim": "agent wrote config file", "boundary_observation": "", "state": "agreement"}
    return rec


def boundary_observed() -> dict:
    """A boundary observation of a permitted action: the effect ran through the gate."""
    rec = sample("er-00001-e0-self-report.json")
    rec["record_id"] = "gf-00005"
    rec["observation"] = {"source": "gateway_proxy", "relationship": "direct", "directness": "direct_observation"}
    rec["verification"] = {
        "vantage": "substrate",
        "method": "intercepted",
        "basis": "substrate_intercepted",
        "basis_engines": ["gateway_proxy"],
    }
    rec["claims"] = []
    rec["reconciliation"] = {"agent_claim": "agent called api.example.com", "boundary_observation": "", "state": "agreement"}
    rec["integrity"] = {"signed": True, "chain_linked": True, "timestamped": False}
    return rec


def contradiction_observed() -> dict:
    """A boundary record that contradicts the agent, with no outside party.

    Still E2: the enforcement point is the deployment's own account, so nothing
    independent has agreed with it. A disagreement is not corroboration either.
    """
    rec = sample("er-00004-e2-contradiction.json")
    rec["record_id"] = "gf-00006"
    rec["claims"] = []
    return rec


def build_cases() -> list[tuple[str, dict, dict]]:
    return [
        ("e0-declared", sample("er-00001-e0-self-report.json"),
         {"decision": "accepted", "derived_grade": "E0",
          "caps": ["no_independent_evidence_caps_at_e0",
                   "e3_requires_an_independent_party",
                   "e4_unreachable_for_this_observation_source"]}),
        ("e1-observed", framework_observed(),
         {"decision": "accepted", "derived_grade": "E1",
          "caps": ["e3_requires_an_independent_party",
                   "e4_unreachable_for_this_observation_source"]}),
        ("e2-enforced", boundary_observed(),
         {"decision": "accepted", "derived_grade": "E2",
          "caps": ["e3_requires_an_independent_party",
                   "e4_requires_timestamp_chain_link_and_independent_verifier"]}),
        ("e2-enforced-emission-conformant", with_claim(boundary_observed(), "emission-conformant"),
         {"decision": "accepted", "derived_grade": "E2", "reason_contains": "grade_derived"}),
        ("e2-contradiction-not-corroboration", with_claim(contradiction_observed(), "emission-conformant"),
         {"decision": "accepted", "derived_grade": "E2",
          "caps": ["e3_requires_an_independent_party"]}),
        ("e3-corroborated", sample("er-00005-e3-derived-reconstructed.json"),
         {"decision": "accepted", "derived_grade": "E3",
          "caps": ["e4_requires_timestamp_chain_link_and_independent_verifier"]}),
        ("e4-anchored", sample("er-00003-e4-operationally-conformant.json"),
         {"decision": "accepted", "derived_grade": "E4"}),
    ]


def main() -> int:
    cases = build_cases()
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    for case_id, record, expect in cases:
        case = {"case_id": case_id, "expect": expect, "record": record}
        target = CASES_DIR / case_id / "case.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(case, indent=2, sort_keys=True) + "\n")
        manifest[case_id] = expect
    MANIFEST.write_text(json.dumps({"suite": "evidence-grade-floor/v1", "cases": manifest}, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(cases)} floor cases to {CASES_DIR.relative_to(HERE)} and {MANIFEST.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
