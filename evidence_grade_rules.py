#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""The E0-E4 grade floor, as one rule set with no third-party imports.

This module is the single definition of how a rung is derived. Both
``validate_evidence.py`` and ``grade_floor.py`` import it, so a validator and a
checker cannot disagree about a rung.

The rungs are the published ladder in ``VERIFIABILITY-OVERVIEW.md``:

    E0 Declared      agent self-report, no independent verification
    E1 Observed      behavior observed by framework/gateway
    E2 Enforced      policy enforced at the boundary, denied actions recorded
    E3 Corroborated  multiple independent sources agree
    E4 Anchored      external timestamping, chain-linking, independent
                     verifiability

E3 is the rung this module is strict about. "Corroborated" means corroboration
by a party that is not the deployment itself, which is the custody question
Axis C of the overview answers. A record is always the deployment's own
account of itself, so counting engine names is not enough: two engines from the
same deployment are one party agreeing with itself. Independence is decided by
the custody class of the engine, never by how many engines are listed.
"""
from __future__ import annotations

GRADE_ORDER = ["E0", "E1", "E2", "E3", "E4"]

# Axis A: the strongest rung a source can support on its own. Gates below can
# only lower this, never raise it, so a producer cannot promote its own basis
# by assertion.
GRADE_BASE_BY_SOURCE = {
    "agent_self_report": "E0",
    "framework": "E1",
    "identity_provider": "E4",
    "gateway_proxy": "E4",
    "sandbox": "E4",
    "operating_system": "E4",
    "network_sensor": "E4",
    "security_sensor": "E4",
    "external_authority": "E4",
}

# Sources with no independent party for an anchor to bind to: cannot reach E4
# even with every marker present.
NON_ANCHORABLE_SOURCES = {"agent_self_report", "framework"}

# Claims that require the derived ceiling to reach at least this rung.
CLAIM_MIN_GRADE = {
    "emission-conformant": "E1",
    "operationally-conformant": "E3",
}

# Engine name meaning "the actor told us so", which is not corroboration.
SELF_REPORT_ENGINE = "self_report"

# Axis C custody: which party is able to produce each engine's account.
#
#   SELF      the deployment's own account, its enforcement point or its own
#             instrumentation. The deployment can bring itself into agreement,
#             so SELF is solitude, not corroboration.
#   PEER      another party inside the agreement: a counterparty or a peer
#             mediating the same interaction.
#   EXTERNAL  a party outside the trust domain: an auditor, a regulator, a
#             payment processor or any non-trusting third party.
#
# Fail closed: an engine that is not listed here is unknown and an unknown
# engine is never treated as independent.
ENGINE_SCOPE = {
    "self_report": "SELF",
    "framework": "SELF",
    "gateway_proxy": "SELF",
    "sandbox": "SELF",
    "operating_system": "SELF",
    "network_sensor": "SELF",
    "security_sensor": "SELF",
    "identity_provider": "EXTERNAL",
    "external_authority": "EXTERNAL",
}

# Scopes that can corroborate a deployment's account of itself.
INDEPENDENT_SCOPES = {"PEER", "EXTERNAL"}

# Gate names, in the order they are applied.
GATE_UNKNOWN_SOURCE = "unknown_source"
GATE_NO_INDEPENDENT_EVIDENCE = "no_independent_evidence"
GATE_NO_INDEPENDENT_PARTY = "no_independent_party"
GATE_NOT_ANCHORABLE = "not_anchorable"
GATE_SOURCE_NOT_ANCHORABLE = "source_not_anchorable"

# The rung each gate caps a record at, whatever its source allows.
GATE_CEILING = {
    GATE_UNKNOWN_SOURCE: "E0",
    GATE_NO_INDEPENDENT_EVIDENCE: "E0",
    GATE_NO_INDEPENDENT_PARTY: "E2",
    GATE_NOT_ANCHORABLE: "E3",
    GATE_SOURCE_NOT_ANCHORABLE: "E3",
}


def min_grade(a: str, b: str) -> str:
    return a if GRADE_ORDER.index(a) <= GRADE_ORDER.index(b) else b


def engine_scope(engine: str) -> str | None:
    """The custody class of an engine or None when the name is not known."""
    return ENGINE_SCOPE.get(engine)


def independent_engines(record: dict) -> list[str]:
    """The engines behind a record whose party is not the deployment itself."""
    ver = record.get("verification") or {}
    engines = [e for e in (ver.get("basis_engines") or []) if isinstance(e, str)]
    src = str((record.get("observation") or {}).get("source") or "")
    if src and src not in engines:
        engines.append(src)
    return sorted({e for e in engines if engine_scope(e) in INDEPENDENT_SCOPES})


def grade_gates(record: dict) -> list[str]:
    """The gates that actually bite, in the order they are applied.

    Computed once, here, so the derivation and any explanation of it cannot
    drift apart.
    """
    obs = record.get("observation") or {}
    ver = record.get("verification") or {}
    rec = record.get("reconciliation") or {}
    integrity = record.get("integrity") or {}
    gates: list[str] = []

    source = str(obs.get("source") or "")
    if source not in GRADE_BASE_BY_SOURCE:
        gates.append(GATE_UNKNOWN_SOURCE)

    if rec.get("state") == "no_independent_evidence":
        gates.append(GATE_NO_INDEPENDENT_EVIDENCE)

    # E3 requires an independent party, decided by custody and not by count.
    if not independent_engines(record):
        gates.append(GATE_NO_INDEPENDENT_PARTY)

    # E4 requires an anchorable origin plus every anchoring marker present.
    verifiable_by = [v for v in (integrity.get("verifiable_by") or []) if isinstance(v, str)]
    independent_verifier = [v for v in verifiable_by if v and v != record.get("agent_id")]
    if not (
        bool(integrity.get("timestamped"))
        and bool(integrity.get("chain_linked"))
        and bool(independent_verifier)
    ):
        if source in NON_ANCHORABLE_SOURCES:
            gates.append(GATE_SOURCE_NOT_ANCHORABLE)
        else:
            gates.append(GATE_NOT_ANCHORABLE)

    return gates


def derive_grade_ceiling(record: dict) -> str:
    """The highest rung the record's own observation can support.

    Derived, never read from the record. Returns one of E0..E4.
    """
    obs = record.get("observation") or {}
    source = str(obs.get("source") or "")
    ceiling = GRADE_BASE_BY_SOURCE.get(source, "E0")
    for gate in grade_gates(record):
        ceiling = min_grade(ceiling, GATE_CEILING[gate])
    return ceiling
