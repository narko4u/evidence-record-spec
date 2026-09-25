#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Validate evidence records against evidence-record-0.1.schema.json, and
evidence appraisals against evidence-appraisal-0.1.schema.json.

Three layers:

1. Schema conformance (JSON Schema, draft 2020-12).
2. Semantic consistency (things the schema cannot express): basis must match
   vantage/method composition, derived records must carry provenance, and
   receipt claims must cite supporting evidence.
3. Derived grade ceiling. This is the important one. The evidence grade is an
   OUTPUT OF APPRAISAL, never a property a producer can assert into existence
   (see VERIFIABILITY-OVERVIEW.md, discipline rule 1). A record cannot reach a
   rung its own observation does not support, no matter what integrity markers
   it declares about itself. The ceiling is derived from:

     - observation.source           (what origin the observation came from)
     - observation.relationship     (direct, corroborating, contradictory, derived)
     - reconciliation.state         (agreement, contradiction, no independent evidence)
     - reconciliation.boundary_observation
                                   (a recorded boundary fact: the alternative
                                    path into E3 when engines are not listed)
     - verification.basis_engines   (how many independent engines the basis rests on)
     - integrity.*                  (presence of anchoring markers, for E4 only)

   `verification.vantage` is NOT one of them. Vantage is read one level up, as
   the first half of the `basis == {vantage}_{method}` composition that semantic
   check 1 enforces. The ceiling is a function of WHERE the observation came
   from and HOW INDEPENDENTLY it is corroborated, not of which vantage the
   verifier stood at.

   Integrity markers are a NECESSARY condition for the anchored rungs and are
   never a sufficient one. Declaring `signed` and `timestamped` on a
   self-report does not promote a self-report.

The validator is deliberately strict: an unrecognised value is a failure, not a
new rung, matching the closed-vocabulary rule established in the standards
discussion for verification basis derivation.

The appraisal layer is checked too, and its citation is a binding rather than a
label. Three things must hold, beyond schema conformance:

  1. `subject_record.digest` must BE the content address of the record actually
     named. Without this the ceiling below can be computed over a different
     artifact than the one the appraisal pins, which makes the cap dodgeable.
  2. `claim_type` must name a receipt claim the subject record makes, whenever
     the subject makes any. An appraisal may appraise a claim the subject does
     not yet assert — that is how a low grade is recorded honestly — but it may
     not attribute a claim the subject never made.
  3. the concluded `e_grade` may never exceed the ceiling derived from the
     subject record, so a verifier cannot record a depth it did not execute.

A fourth rule is about scope rather than content. The three checks above are
only meaningful once the subject record is actually in hand, so an appraisal
whose subject was not supplied is reported UNRESOLVED and counts as a failure.
It must never quietly pass with no semantic check performed, because then a pass
would mean "we happened not to load the subject" rather than "the citation
binds". Schema-only validation remains available, but it has to be asked for
explicitly with `--schema-only`, so the weaker guarantee can never be the
accidental one.

Note what is deliberately NOT enforced here: the appraisal path does not apply
`CLAIM_MIN_GRADE`. Concluding a grade BELOW a claim's floor is the whole point of
appraisal (see samples/ea-00002: an honest E0 against an emission-conformant
claim). Flooring belongs to the producer's claim in the record layer, where a
record cannot assert a claim its own observation does not support.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.stderr.write("Requires jsonschema: pip install jsonschema\n")
    sys.exit(2)

try:
    import rfc8785
except ImportError:
    sys.stderr.write("Requires rfc8785: pip install rfc8785\n")
    sys.exit(2)

HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE / "evidence-record-0.1.schema.json"
DEFAULT_APPRAISAL_SCHEMA = HERE / "evidence-appraisal-0.1.schema.json"

GRADE_ORDER = ["E0", "E1", "E2", "E3", "E4"]

# What an observation source can support at most, on its own, before the
# corroboration and anchoring gates are applied.
#
#   E0  the actor's own account, nothing more
#   E1  observed by the framework hosting the agent, with no boundary or
#       external corroboration
#   E4  a boundary, sensor or external authority. The gates below then decide
#       how much of that headroom the record actually earns: the top rung stays
#       out of reach without anchoring, and E3 stays out of reach without
#       corroboration that is not the actor's own account.
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


def _min_grade(a: str, b: str) -> str:
    return a if GRADE_ORDER.index(a) <= GRADE_ORDER.index(b) else b


def content_digest(doc: dict) -> str:
    """The derived identifier of a record or appraisal.

    SHA-256 over the JCS (RFC 8785) canonical form of the FULL document, bare
    64-char lowercase hex, no exclusion set. Same derivation the CPB-registry
    vectors pin, so a vector digest and this function agree by construction.
    """
    return hashlib.sha256(rfc8785.dumps(doc)).hexdigest()


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
        ceiling = _min_grade(ceiling, "E0")

    # E3 requires corroboration by something other than the actor. A basis that
    # includes the actor's own account is not independent corroboration, however
    # many other engines are listed beside it. Beyond independence, the record
    # needs either two independent engines or a recorded boundary observation
    # that is not the agent's own claim.
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
        ceiling = _min_grade(ceiling, "E2")

    # E4 requires an anchorable origin plus every anchoring marker actually
    # present. Markers can only gate E4; they never raise anything below it.
    verifiable_by = [v for v in (integrity.get("verifiable_by") or []) if isinstance(v, str)]
    independent_verifier = [
        v for v in verifiable_by if v and v != record.get("agent_id")
    ]
    anchorable = (
        source not in NON_ANCHORABLE_SOURCES
        and bool(integrity.get("timestamped"))
        and bool(integrity.get("chain_linked"))
        and bool(independent_verifier)
    )
    if not anchorable:
        ceiling = _min_grade(ceiling, "E3")

    return ceiling


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

    # 3. the grade ceiling is DERIVED, never stamped
    ceiling = derive_grade_ceiling(record)
    declared = record.get("grade")
    if declared:
        # Not schema-permitted any more; if a caller supplies a looser schema,
        # a stamped grade may never exceed what the observation supports.
        if GRADE_ORDER.index(declared) > GRADE_ORDER.index(ceiling):
            errors.append(
                f"declared grade {declared} exceeds the ceiling {ceiling} derived "
                f"from observation.source, relationship, reconciliation.state, "
                f"basis_engines and integrity markers"
            )

    # 4. receipt claims versus the derived ceiling
    claims = record.get("claims") or []
    for c in claims:
        claim = c.get("claim")
        floor = CLAIM_MIN_GRADE.get(claim)
        if floor and GRADE_ORDER.index(ceiling) < GRADE_ORDER.index(floor):
            errors.append(
                f"claim '{claim}' requires grade >= {floor}, but the derived "
                f"ceiling for this record is {ceiling}"
            )
        if not c.get("evidence"):
            errors.append(f"claim '{claim}' must cite supporting evidence record IDs")
        if claim == "operationally-conformant":
            state = (record.get("reconciliation") or {}).get("state")
            if state != "agreement":
                errors.append(
                    f"claim 'operationally-conformant' requires "
                    f"reconciliation.state=agreement, record is '{state}'"
                )

    # 5. reconciliation state is explicit when both claim and observation present
    rec = record.get("reconciliation") or {}
    if rec and rec.get("state") not in ("agreement", "contradiction", "no_independent_evidence"):
        errors.append(f"reconciliation.state '{rec.get('state')}' is not a valid state")

    return errors


def validate_record(record: dict, schema: dict) -> tuple[bool, list[str]]:
    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.ValidationError as e:
        return False, [f"schema: {e.message} (at {'/'.join(str(p) for p in e.path) or '$'})"]
    sem = semantic_errors(record)
    return (not sem), sem


def validate_appraisal(
    appraisal: dict, schema: dict, subject: dict | None, *, schema_only: bool = False
) -> tuple[bool, list[str], bool]:
    """Validate an appraisal. Returns (ok, errors, unresolved).

    `unresolved` is True when the appraisal is schema-valid but its subject
    record was not supplied, so none of the semantic checks could run. That is
    reported separately from a plain failure so the caller can say so out loud.
    """
    try:
        jsonschema.validate(instance=appraisal, schema=schema)
    except jsonschema.ValidationError as e:
        return False, [f"schema: {e.message} (at {'/'.join(str(p) for p in e.path) or '$'})"], False

    if schema_only:
        return True, [], False

    if subject is None:
        cited = (appraisal.get("subject_record") or {}).get("record_id") or "<unnamed>"
        return False, [
            f"subject record '{cited}' was not supplied, so the citation cannot be "
            f"resolved and none of the appraisal checks could run; pass the subject "
            f"record alongside the appraisal, or use --schema-only to state "
            f"explicitly that only schema conformance is asserted"
        ], True

    errors = []
    cited = appraisal.get("subject_record") or {}
    subject_id = subject.get("record_id")

    # 1. the citation is a binding, not a label. If the digest does not resolve
    # to the record named, the ceiling below is computed over a different
    # artifact than the one the appraisal pins, and the cap is dodgeable by
    # pointing at a strong record while appraising a weak one.
    actual = content_digest(subject)
    if cited.get("digest") and cited["digest"] != actual:
        errors.append(
            f"subject_record.digest {cited['digest']} does not bind to record "
            f"'{subject_id}' (its JCS SHA-256 is {actual})"
        )

    # 2. claim_type names a receipt claim OF THE SUBJECT. Where the subject
    # asserts claims, the appraised claim must be one of them. Where it asserts
    # none, any claim_type is allowed: appraising a claim the subject does not
    # yet make is how a low grade is recorded honestly (samples/ea-00002).
    claimed = [
        c.get("claim")
        for c in (subject.get("claims") or [])
        if isinstance(c, dict) and c.get("claim")
    ]
    if claimed and appraisal.get("claim_type") not in claimed:
        errors.append(
            f"claim_type '{appraisal.get('claim_type')}' is not a claim subject "
            f"record '{subject_id}' makes (it claims {sorted(claimed)}); an "
            f"appraisal may not attribute a claim the subject never made"
        )

    # 3. the concluded grade may never exceed what the subject's observation
    # can support. Note the floors in CLAIM_MIN_GRADE are deliberately NOT
    # applied: concluding below a claim's floor is the point of appraisal.
    ceiling = derive_grade_ceiling(subject)
    concluded = appraisal.get("e_grade")
    if concluded and GRADE_ORDER.index(concluded) > GRADE_ORDER.index(ceiling):
        errors.append(
            f"appraised e_grade {concluded} exceeds the ceiling {ceiling} derived "
            f"from subject record '{subject_id}'"
        )
    return (not errors), errors, False


def kind_of(doc: dict) -> str:
    if "appraisal_id" in doc:
        return "appraisal"
    if "record_id" in doc:
        return "record"
    return "unknown"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate evidence records and appraisals against the evidence-record schema."
    )
    parser.add_argument("paths", nargs="+", help="record/appraisal JSON files, or a directory")
    parser.add_argument("--schema", default=None, help="path to the record schema JSON")
    parser.add_argument(
        "--appraisal-schema", default=str(DEFAULT_APPRAISAL_SCHEMA),
        help="path to the appraisal schema JSON",
    )
    parser.add_argument(
        "--strict-schema", action="store_true",
        help="force --schema for every file instead of routing by document kind",
    )
    parser.add_argument(
        "--schema-only", action="store_true",
        help="assert schema conformance only and skip every cross-document check. "
             "Without this flag an appraisal whose subject record is not supplied "
             "is reported UNRESOLVED and fails.",
    )
    args = parser.parse_args(argv)

    record_schema = json.loads(Path(args.schema or DEFAULT_SCHEMA).read_text())
    appraisal_schema = json.loads(Path(args.appraisal_schema).read_text())

    files: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)

    docs: dict[Path, dict | None] = {}
    for f in files:
        try:
            docs[f] = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            docs[f] = None
            print(f"FAIL {f.name}")
            print(f"     - invalid JSON: {e}")

    by_record_id = {
        d["record_id"]: d for d in docs.values() if isinstance(d, dict) and "record_id" in d
    }

    failed = 0
    unresolved_count = 0
    for f in files:
        doc = docs.get(f)
        if doc is None:
            failed += 1
            continue

        kind = kind_of(doc)
        unresolved = False
        if kind == "appraisal":
            subject = by_record_id.get((doc.get("subject_record") or {}).get("record_id"))
            ok, errors, unresolved = validate_appraisal(
                doc, appraisal_schema, subject, schema_only=args.schema_only
            )
        elif kind == "record":
            ok, errors = validate_record(doc, record_schema)
        else:
            failed += 1
            print(f"FAIL {f.name}")
            print("     - not an evidence record (record_id) or an appraisal (appraisal_id)")
            continue

        if ok:
            print(f"OK   {f.name}")
        else:
            failed += 1
            label = "UNRESOLVED" if unresolved else "FAIL"
            if unresolved:
                unresolved_count += 1
            print(f"{label} {f.name}")
            for e in errors:
                print(f"     - {e}")

    summary = f"\n{len(files) - failed}/{len(files)} records valid"
    if unresolved_count:
        summary += f", {unresolved_count} unresolved (subject record not supplied)"
    print(summary)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
