# Proposal: Evidence Record Spec (testable data model for E4)

**WG:** Observability & Traceability
**Type:** proposal build for testing, not a spec-paper
**Related:** use case E4 (tamper-evident evidence), issue #36 (control-plane
telemetry as an evidence source), agent record family
**Status:** DRAFT for review

## Summary

The E4 use case names a gap: no standard for tamper-evident agent evidence,
no evidence-grade trace interchange format. Rather than write another
analysis document, this proposal is a testable artifact: a JSON Schema for an
evidence record, sample records, and a strict validator. The WG can run the
validator, attack the schema, and build against the format the same way it
has been testing record family formats.

## What the format encodes

The record format makes four things explicit, drawing on the vocabulary this
WG has already been converging on:

1. **Observation** : source (agent self-report through external authority) and
   relationship (direct, corroborating, contradictory, derived), matching the
   source-and-trust requirement in the use case catalog and the two-dimension
   model in issue #36.
2. **Verification** : vantage (substrate vs artifact) and method (intercepted
   vs reconstructed), the same axes used in verification_basis composition.
3. **Grade** : the E0-E4 ladder from the E4 use case (Declared, Observed,
   Enforced, Corroborated, Anchored), with grade-to-integrity requirements.
4. **Claims and reconciliation** : emission-conformant and
   operationally-conformant claims, and the three-state reconciliation
   (agreement, contradiction, no independent evidence).

## Why test it here

The format is deliberately implementation-free: integrity markers record
presence, not mechanism. That makes it a shared vocabulary rather than a
vendor artifact. Testing it in this WG means the interchange format, if it
earns adoption, inherits the WG's review of the model, not a single vendor's
implementation.

## What is being asked

- A review pass of the schema and validator (run it, attack it)
- Feedback on the grade-to-integrity requirements and the claim floors
- Whether this is worth developing toward a WG-endorsed interchange format
  alongside the use case catalog

## Repository

Public: `github.com/narko4u/evidence-record-spec`
(README, schema, 5 sample records, validator; Apache-2.0 / CC-BY-4.0)
