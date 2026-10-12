# Evidence Record Spec

A portable, evidence-grade record format for agent actions. The schema and
validator describe **what an evidence record must contain** so an auditor can
separate what was claimed from what was observed, at what vantage, and with
what assurance.

This is a public specification. It is deliberately independent of any
implementation: it describes the record, not the engine that produces it.

## Why this exists

The AAIF Observability & Traceability WG use case **E4 (Tamper-evident
evidence for audit and dispute resolution)** names the gap this addresses:

> "Vendor traces are mutable and vendor-specific; there is no standard for
> tamper-evident agent evidence. Gap: an evidence-grade trace interchange
> format that preserves integrity guarantees end to end."

This spec is a proposed answer to that gap: a public data model that anyone
can test, attack, and build against.

## The model

Every record carries four things that matter to an auditor:

1. **Observation** : where the evidence came from and what it claims
   - `source`: agent self-report, framework, gateway/proxy, identity provider,
     sandbox, OS, network sensor, security sensor, external authority
     (the AAIF "source and trust" distinction)
   - `relationship`: direct, corroborating, contradictory, or derived
   - `directness`: direct observation vs inferred

2. **Verification** : how strong the evidence is
   - `vantage`: substrate (the artifact cannot forge or suppress it) vs
     artifact (inside the artifact's write path)
   - `method`: intercepted (captured live) vs reconstructed (after the fact)
   - `basis`: composed as `{vantage}_{method}` (e.g. `substrate_intercepted`)
   - `basis_engines`: which engines contributed

3. **Grade** : the evidence strength ladder
   - **E0 Declared** : agent self-report only
   - **E1 Observed** : behavior observed by framework/gateway
   - **E2 Enforced** : policy enforced at the boundary (denied actions recorded)
   - **E3 Corroborated** : multiple independent sources agree
   - **E4 Anchored** : external timestamping, chain-linking, independent
     verifiability

4. **Claims & reconciliation** : what the record asserts
   - `claims`: `emission-conformant` (the agent emitted the telemetry the
     policy expects) or `operationally-conformant` (the agent actually
     performed the permitted actions, verified by observation)
   - `reconciliation`: agreement, contradiction, or the explicit absence of
     independent evidence (three states, not two)

## witness_scope (vocabulary)

A separate vocabulary answers the custody question: who is able to produce a
record at all. Scope is graded SELF (the deployment's own account), PEER (a
counterparty in the same agreement), or EXTERNAL (a party outside the trust
domain). It names custody, not forgeability, and it is deliberately not a
strength value: collapsing it into a summary figure would let a SELF-scope
deployment read as externally witnessed.

The scope name travels alongside the observation and verification axes but is
not one of them, because it describes custody rather than record content.

Definitions, assignment rule, and the public provenance of the grading:
[`VERIFIABILITY-OVERVIEW.md`](VERIFIABILITY-OVERVIEW.md#axis-c-witness_scope).

## Sample records

The record carries the observation. The grade is what that observation
supports and what an appraisal concludes from it, so it is never a member the
record carries (discipline rule 1 in `VERIFIABILITY-OVERVIEW.md`).

| File | Rung the observation supports | Point it demonstrates |
|---|---|---|
| `samples/er-00001-e0-self-report.json` | E0 | Self-report with no independent evidence |
| `samples/er-00002-e2-emission-conformant.json` | E2 | Gateway corroboration, emission-conformant claim |
| `samples/er-00003-e4-operationally-conformant.json` | E4 | Anchored record, both claims, external verifier |
| `samples/er-00004-e2-contradiction.json` | E2 | Agent claim contradicted by the deployment's own gateway |
| `samples/er-00005-e3-derived-reconstructed.json` | E3 | Derived record with provenance, reconstructed method |
| `samples/er-00006-e3-peer-corroboration.json` | E3 | Corroboration by the counterparty's own gateway, a PEER party |

E3 requires corroboration by a party that is not the deployment itself. The
deployment's own enforcement point is its own account, so a boundary record
that contradicts the agent is E2 rather than E3, however damning it is: a party
cannot corroborate itself. A count of engines it owns is not independence.
Corroboration comes from Axis C custody, a PEER or an EXTERNAL party, never
from how many engines are named. A PEER engine names the counterparty's own
enforcement point, so the other side of an interaction can corroborate a
record without an auditor, which is what `counterparty_gateway` does.

## Evidence Appraisal (verifier artifact)

The E-grade is an **output of appraisal**, not a field the producer stamps
(discipline rule 1 in `VERIFIABILITY-OVERVIEW.md`). The `evidence-appraisal`
artifact records what an independent verifier actually checked about an
evidence record and the grade it concluded:

| File | Subject | Concluded grade | Point it demonstrates |
|---|---|---|---|
| `samples/ea-00001-e4-agreement.json` | er-00003 | E4 | Verifier confirms the E4 record, agreement |
| `samples/ea-00002-e0-no-independent-evidence.json` | er-00001 | E0 | Self-report appraised honestly, no independent evidence |
| `samples/ea-00003-e2-contradiction.json` | er-00004 | E2 | Verifier finds agent claim contradicted |

Schema: `evidence-appraisal-0.1.schema.json`. The appraisal cites its subject
by typed digest (`subject_record.digest`, bare 64-char lowercase hex = SHA-256
over the JCS canonical form of the full evidence record) so the grade binds to
a specific record version, never to a floating claim.

## Content addresses (CPB registry contexts)

Each record/appraisal has a derived identifier: SHA-256 over the JCS (RFC 8785)
canonical form of the **full** record (no exclusion set — the field set is the
closed schema member list; records are schema-validated before digesting, so an
unrecognised member or enum value is rejected, never digested). Pinned
conformance vectors for both artifact types live in
[`vectors/cpb-registry/`](vectors/cpb-registry/) in the same format used by the
Action State Group CPB registry (`machine-mandate` precedent): positive KATs
with canonical bytes + digests, negatives with reject semantics and mutation
probes.

## Validation

```bash
pip install jsonschema rfc8785
# Records and appraisals are separate schema families. The schema is selected
# per file automatically, so a directory holding both validates in one call:
python validate_evidence.py samples/
python validate_evidence.py path/to/records/*.json
# An explicit schema still overrides the automatic selection:
python validate_evidence.py --schema evidence-record-0.1.schema.json samples/er-*.json
```

The ceiling rules have their own regression fixtures, asserted to fail:

```bash
python fixtures/check_negative_fixtures.py
```

The validator checks two layers:

1. **Schema conformance** : structural rules from the JSON Schema.
2. **Semantic consistency** : things the schema cannot express:
   - `basis` must equal the composition of `vantage` + `method`
   - `derived` observations must carry `provenance`
   - the grade is **derived** from `observation.source`, `relationship`,
     `reconciliation.state`, `verification.basis_engines` and the `integrity`
     markers, and capped by them. A record cannot reach a rung its own
     observation cannot support, whatever it declares about itself: a
     self-report is E0, a framework observation is E1, and a boundary or
     external observation reaches higher only with corroboration, and for E4
     only with chain-linking, timestamping and a verifier independent of the
     agent. `verification.vantage` is **not** an input to the ceiling: it is
     the first half of the `basis` composition checked above
   - `operationally-conformant` claims require a ceiling of at least E3 and a
     `reconciliation.state` of `agreement`
   - unrecognised enum values fail (closed vocabulary, no silent upgrades)
   - an unrecognised member fails (`additionalProperties: false`), so a
     producer cannot stamp a grade onto a record at all

On the appraisal side the citation is a binding, not a label:

   - `subject_record.digest` must be the JCS (RFC 8785) SHA-256 of the record
     actually named, so the ceiling is computed over the artifact the appraisal
     pins and never over a different one
   - `claim_type` must name a receipt claim the subject makes, wherever the
     subject makes any. An appraisal may appraise a claim the subject does not
     yet assert — that is how a low grade is recorded honestly
     (`samples/ea-00002`) — but it may not attribute a claim the subject never
     made
   - the concluded grade cannot exceed the ceiling derived from its subject
     record

The appraisal path deliberately does **not** apply the claim floors: concluding
a grade *below* a claim's floor is the point of appraisal. Flooring belongs to
the producer's claim in the record layer.

## Grade floor (runnable, no install)

The rungs are the ladder. The floor is what each rung requires, and it is
runnable as shipped:

```bash
python3 grade_floor.py grade-floor/cases/
python3 grade_floor.py --json grade-floor/cases/   # one JSON object per case
```

`grade-floor/` holds one accepted case per rung, written by `gen_cases.py`. The
expectations in it are authored from the rule text and never computed from the
implementation, so the corpus is able to disagree with the runner and a
disagreement is a finding rather than a nuisance. The floor derivation lives in
`evidence_grade_rules.py`, which both `validate_evidence.py` and
`grade_floor.py` import, so a checker and a validator cannot disagree about a
rung. Exit code 0 means every case behaved as published.

A refusal names the rule that refused it, for example
`claim_floor_below_e3:operationally-conformant` or
`unknown_observation_source`. Both entry points are standard library only: no
install step, no network call, no account and no service.

This repository ships the floor. Cases that probe the boundary between
adjacent rungs are not published here.

CI also runs a disclosure firewall
(`.github/scripts/firewall_check.py`): this tree carries the format, never the
mechanism that produces records at these grades.

## Independent implementations

The format is published so that it can be implemented by someone with no
relationship to this project. Everything needed for that is in this tree: the
two schemas, the floor corpus and the checker, all standard library only.

If you implement the format, run the published corpus against your
implementation and report the rungs you derive, including any case where you
disagree with the expected rung. A disagreement that names the case and the
reason is more useful to the format than agreement, because it is the only thing
that tells us the rule text is ambiguous.

Two ways to report it:

- open an issue in this repository with the case list and the rungs you derived
- run your own near-miss cases through this checker and send the results

Related schemes grade the same records on a different axis.
[`CROSSWALK.md`](CROSSWALK.md) states how the two kinds of grade relate. It
carries no mapping table on purpose: derive your own and report it the same
way, because a mapping asserted by the project that wrote one side of it is not
checkable by the reader.

Implementations we know about are listed in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md). Teams that want help integrating the
format can ask Empire Labs Pty Ltd for a scoped engagement, which is a paid
route. The maintainers do not write a third party's implementation for them.

## Scope boundary

**This repo describes the record format only.** It does not describe:

- how records are signed, chained, or timestamped (only whether the record
  carries those markers)
- how observations are collected, correlated, or derived
- how policies are enforced
- any specific product implementation

The integrity markers (`signed`, `chain_linked`, `timestamped`) record
presence, not mechanism. An auditor can verify a record against this format
without any knowledge of the system that produced it, and a producer can
implement the format without adopting any particular stack.

**This repository is also not a service.** It is the specification and
validation layer: it defines what a conforming record contains, and checks
whether a given artifact conforms to that format. It does not anchor, attest,
notarise or hold custody of any record. Validating a record here produces no
anchor and involves no party independent of whoever runs the validator.
Anchoring, replay protection and custody of records are operations carried out
outside the format, and are out of scope here.

A record that validates is a statement about the record's own content. It is
not a warranty about the system that produced it, and it is not evidence that
the operation the record describes actually happened.

## Independent implementation notice

This project is an independent implementation. It shares vocabulary with the
AAIF standards discussions and adjacent projects in the agent observability
and evidence space (vantage, method, basis, substrate, observation source
and relationship), which are common terminology in the agent observability
and evidence space and appear across multiple projects
and working group documents. No code, schema structure, documentation, or
sample records in this repository are copied from any other project. The
signing, chain-linking, and timestamping mechanisms that would produce these
records are out of scope for this repository entirely.

---

## Acknowledgements

The schemas here are written against **[JSON Schema](https://json-schema.org/)**
draft 2020-12, used as the schema language only. JSON Schema is an independent
specification with its own maintainers.

The vocabulary this format shares with adjacent agent-observability work
(`vantage`, `method`, `basis`, `substrate`, observation source and relationship)
is common terminology in that space. No code, schema structure, documentation or
sample records in this repository are copied from any other project - see the
independent implementation notice above.

There are no third-party runtime dependencies.

---

## License

- Schema and validator: Apache-2.0
- Documentation and sample records: CC-BY-4.0
