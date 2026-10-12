#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Generate the grade floor corpus deterministically.

Every case is one record plus the decision the published rules say it earns.
Expectations are authored here from the rule text, never computed from the
implementation, so the corpus can disagree with the runner and that disagreement
is the point. Re-running rewrites every case byte for byte.

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


def fresh_e0() -> dict:
    return sample("er-00001-e0-self-report.json")


def with_claim(record: dict, claim: str) -> dict:
    rec = copy.deepcopy(record)
    rec["claims"] = [{"claim": claim, "evidence": [rec.get("record_id") or "case"]}]
    return rec


def framework_observed() -> dict:
    """A framework observation: the lowest source that is not the actor's own."""
    rec = fresh_e0()
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


def boundary_without_corroboration() -> dict:
    """A boundary observation of a permitted action, with nothing corroborating it."""
    rec = fresh_e0()
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


def build_cases() -> list[tuple[str, dict, dict]]:
    e0 = fresh_e0()
    e2ish = sample("er-00002-e2-emission-conformant.json")
    e4 = sample("er-00003-e4-operationally-conformant.json")
    contra = sample("er-00004-e3-contradiction.json")

    unanchored = copy.deepcopy(e2ish)
    self_reported_corroboration = copy.deepcopy(e2ish)
    self_reported_corroboration["verification"]["basis_engines"] = ["self_report", "gateway_proxy"]

    no_chain = copy.deepcopy(e4)
    no_chain["integrity"] = {k: v for k, v in no_chain["integrity"].items()}
    no_chain["integrity"]["chain_linked"] = False

    framework_markers = copy.deepcopy(e4)
    framework_markers["observation"]["source"] = "framework"
    framework_markers["verification"]["basis_engines"] = ["framework"]
    framework_markers["claims"] = []

    unknown_source = copy.deepcopy(e0)
    unknown_source["observation"]["source"] = "teapot"

    return [
        ("e0-declared", e0, {"decision": "accepted", "derived_grade": "E0",
                             "caps": ["no_independent_evidence_caps_at_e0", "e3_requires_corroboration_beyond_the_actor"]}),
        ("e0-claims-emission-conformant", with_claim(e0, "emission-conformant"),
         {"decision": "rejected", "derived_grade": "E0", "reason_contains": "claim_floor_below_e1"}),
        ("e0-claims-operationally-conformant", with_claim(e0, "operationally-conformant"),
         {"decision": "rejected", "derived_grade": "E0", "reason_contains": "claim_floor_below_e3"}),
        ("e1-observed", framework_observed(),
         {"decision": "accepted", "derived_grade": "E1",
          "caps": ["e3_requires_corroboration_beyond_the_actor", "e4_unreachable_for_this_observation_source"]}),
        ("e2-enforced", boundary_without_corroboration(),
         {"decision": "accepted", "derived_grade": "E2", "caps": ["e3_requires_corroboration_beyond_the_actor"]}),
        ("e2-enforced-emission-conformant", with_claim(boundary_without_corroboration(), "emission-conformant"),
         {"decision": "accepted", "derived_grade": "E2"}),
        ("e3-corroborated", unanchored,
         {"decision": "accepted", "derived_grade": "E3", "caps": ["e4_requires_timestamp_chain_link_and_independent_verifier"]}),
        ("e3-contradiction-emission-conformant", contra,
         {"decision": "accepted", "derived_grade": "E3"}),
        ("e3-contradiction-claims-operationally-conformant", with_claim(contra, "operationally-conformant"),
         {"decision": "rejected", "derived_grade": "E3", "reason_contains": "claim_requires_agreement"}),
        ("e3-corroboration-rests-on-self-report", with_claim(self_reported_corroboration, "operationally-conformant"),
         {"decision": "rejected", "derived_grade": "E2",
          "reason_contains": "claim_floor_below_e3", "caps": ["e3_requires_corroboration_beyond_the_actor"]}),
        ("e4-anchored", e4, {"decision": "accepted", "derived_grade": "E4"}),
        ("e4-missing-chain-link", no_chain,
         {"decision": "accepted", "derived_grade": "E3",
          "caps": ["e4_requires_timestamp_chain_link_and_independent_verifier"]}),
        ("e4-framework-declares-every-marker", framework_markers,
         {"decision": "accepted", "derived_grade": "E1",
          "caps": ["e4_unreachable_for_this_observation_source"]}),
        ("unknown-observation-source", unknown_source,
         {"decision": "rejected", "derived_grade": "E0", "reason_contains": "unknown_observation_source"}),
        ("unknown-claim", with_claim(e0, "verified-because-we-say-so"),
         {"decision": "rejected", "derived_grade": "E0", "reason_contains": "unknown_claim"}),
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
    print(f"wrote {len(cases)} cases to {CASES_DIR.relative_to(HERE)} and {MANIFEST.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
