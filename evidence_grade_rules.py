#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""The grade floor, as one rule set with no third-party imports.

This module holds the derivation that both entry points share:

  - ``validate_evidence.py`` uses it to cap a record's claim against its own
    observation.
  - ``grade_floor.py`` uses it to appraise a corpus of records and report the
    rung each one reaches.

There is exactly one definition of the floor. A checker and a validator that
disagree about a rung make the rung meaningless, so the rules are not
reimplemented anywhere else.

The floor is DERIVED from the record. It is never read from the record, and a
value the producer declares never raises it.
"""

GRADE_ORDER = ["E0", "E1", "E2", "E3", "E4"]

# What an observation source can support at most, on its own, before the
# corroboration and anchoring gates are applied.
#
#   E0  the actor's own account, nothing more
#   E1  observed by the framework hosting the agent, with no boundary or
#       external corroboration
#   E4  a boundary, sensor or external authority. The gates below then decide
#       how much of that headroom the record actually earns.
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

# engine name meaning "the actor told us so", which is not corroboration
SELF_REPORT_ENGINE = "self_report"


def min_grade(a: str, b: str) -> str:
    return a if GRADE_ORDER.index(a) <= GRADE_ORDER.index(b) else b


def derive_grade_ceiling(record: dict) -> str:
    """The highest rung the record's own observation can support.

    Derived, never read from the record. Returns one of E0..E4.
    """
    obs = record.get("observation") or {}
    ver = record.get("verification") or {}
    rec = record.get("reconciliation") or {}
    integrity = record.get("integrity") or {}

    source = str(obs.get("source") or "")
    ceiling = GRADE_BASE_BY_SOURCE.get(source, "E0")

    # No independent evidence is exactly a self-report: it caps at E0 whatever
    # else the record claims.
    if rec.get("state") == "no_independent_evidence":
        ceiling = min_grade(ceiling, "E0")

    # E3 requires corroboration by something other than the actor.
    engines = [e for e in (ver.get("basis_engines") or []) if isinstance(e, str)]
    distinct = sorted(set(engines))
    rests_on_self_report = any(e == SELF_REPORT_ENGINE for e in distinct)
    boundary = str(rec.get("boundary_observation") or "").strip()
    relationship = obs.get("relationship")
    corroborated = (
        not rests_on_self_report
        and (
            len(distinct) >= 2
            or (relationship in ("corroborating", "contradictory") and bool(boundary))
        )
    )
    if not corroborated:
        ceiling = min_grade(ceiling, "E2")

    # E4 requires an anchorable origin plus every anchoring marker actually
    # present. Markers can only gate E4; they never raise anything below it.
    verifiable_by = [v for v in (integrity.get("verifiable_by") or []) if isinstance(v, str)]
    independent_verifier = [v for v in verifiable_by if v and v != record.get("agent_id")]
    anchorable = (
        source not in NON_ANCHORABLE_SOURCES
        and bool(integrity.get("timestamped"))
        and bool(integrity.get("chain_linked"))
        and bool(independent_verifier)
    )
    if not anchorable:
        ceiling = min_grade(ceiling, "E3")

    return ceiling
