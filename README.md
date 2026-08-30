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

## Sample records

| File | Grade | Point it demonstrates |
|---|---|---|
| `samples/er-00001-e0-self-report.json` | E0 | Self-report with no independent evidence |
| `samples/er-00002-e2-emission-conformant.json` | E2 | Gateway corroboration, emission-conformant claim |
| `samples/er-00003-e4-operationally-conformant.json` | E4 | Anchored record, both claims, external verifier |
| `samples/er-00004-e3-contradiction.json` | E3 | Agent claim contradicted by gateway observation |
| `samples/er-00005-e3-derived-reconstructed.json` | E3 | Derived record with provenance, reconstructed method |

## Validation

```bash
pip install jsonschema
python validate_evidence.py samples/
python validate_evidence.py path/to/records/*.json
```

The validator checks two layers:

1. **Schema conformance** : structural rules from the JSON Schema.
2. **Semantic consistency** : things the schema cannot express:
   - `basis` must equal the composition of `vantage` + `method`
   - `derived` observations must carry `provenance`
   - grade-to-integrity requirements (E4 requires timestamp + chain-linking +
     independent verifier; lower grades require fewer)
   - `operationally-conformant` claims require grade >= E3
   - unrecognised enum values fail (closed vocabulary, no silent upgrades)

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

## License

- Schema and validator: Apache-2.0
- Documentation and sample records: CC-BY-4.0
