# Verifiability model overview: evidence record spec (E4 gap)

**For:** OT-WG meeting where Steven Mih discusses the Agent Action Capsule
**From:** Empire Labs (narko4u), written pre-read so the model is in the
room even though we cannot attend
**Related:** AAIF OT-WG use case E4 (tamper-evident evidence), issue #36
(control-plane telemetry as an evidence source), issue #37 (evidence record
spec proposal), public artifact https://github.com/narko4u/evidence-record-spec
**Status:** DRAFT for the WG, not a new standard

## Summary

The evidence record spec is a vendor-neutral data model for labelling and
comparing evidence about what an agent actually did. The point is not a new
format, it is a shared vocabulary: how independently was the evidence
obtained, at what vantage, and what does the record claim about the action.
It was written to give the E4 use case (tamper-evident evidence for audit and
dispute) a testable answer, and it is deliberately implementation-free so any
group can adopt the model without adopting our stack.

## Why this matters

E4 names the gap: vendor traces are mutable and vendor-specific, and there is
no standard for tamper-evident agent evidence. Two systems can both claim to
have "evidence" of an agent action; one is the agent's own self-report, the
other is a gateway record the agent cannot rewrite. They carry very different
evidential weight, but most current formats express them the same way. A
shared vocabulary for evidence strength gives auditors a uniform input and
gives implementers a target for what verification must mean at each layer.

## The model (concepts)

### Axis A: observation source and relationship

Where did the evidence come from, and what does it claim about the action?

1. **Source**: agent self-report, framework, gateway/proxy, identity provider,
   sandbox, operating system, network sensor, security sensor, external
   authority. This is the AAIF "source and trust" distinction: separating
   agent self-reporting from boundary or external evidence.
2. **Relationship**: direct, corroborating, contradictory, or derived. A
   gateway record can agree with an agent self-report, contradict it, or have
   no bearing on it.
3. **Reconciliation**: three states, not two. Agreement, contradiction, or the
   explicit absence of independent evidence. The no-independent-evidence state
   is a real audit finding, not a silent default.

### Axis B: verification strength

How strong is the evidence, independent of where it came from?

1. **Vantage**: substrate (the artifact cannot forge or suppress the record)
   vs artifact (inside the artifact's write path). The weaker of what the
   producer declared and what the engines can reach wins, so a producer cannot
   raise its own basis by assertion.
2. **Method**: intercepted (captured at the time of the action) vs
   reconstructed (established after the fact). Orthogonal to vantage: a
   substrate_reconstructed record is externally verifiable evidence, just
   assembled later.
3. **Basis**: composed as `{vantage}_{method}` (e.g. `substrate_intercepted`),
   the same derivation rule used in verification basis composition.

### The E0-E4 evidence strength ladder

The two axes compose into a grade used to state, in one label, how anchored
the evidence is:

| Grade | Name | What it means | Minimum integrity markers |
|---|---|---|---|
| E0 | Declared | agent self-report, no independent verification | none |
| E1 | Observed | behavior observed by framework/gateway | signed |
| E2 | Enforced | policy enforced at the boundary, denied actions recorded | signed + chained |
| E3 | Corroborated | multiple independent sources agree | signed + chained + timestamped |
| E4 | Anchored | external timestamping, chain-linking, independent verifiability | all of E3 + verifier identifiers |

### Receipt claims: emission-conformant and operationally-conformant

The model separates two claims that are easy to confuse:

- **emission-conformant**: the agent emitted the telemetry the policy expects.
  The records exist and are well-formed.
- **operationally-conformant**: the agent actually performed the permitted
  actions, verified by observation. Stronger claim, requires stronger
  evidence (grade >= E3 in the current validator).

An audit that only checks emission conformance can be fooled by a well-formed
agent that quietly did something else. The operationally-conformant claim is
where the evidence model earns its keep, and it is the claim an auditor can
actually act on.

## Discipline rules (the honest part)

1. **The label is an output of appraisal, not a field the producer stamps.**
   A verifier records the depth it actually checked, never a depth higher
   than it executed.
2. **Closed vocabulary, fail closed.** An unrecognised value is a failure,
   not a new rung. A typo cannot silently raise a record's strength.
3. **Integrity markers record presence, not mechanism.** The schema says a
   record is signed, chained, and timestamped; it does not say how. An
   auditor can verify a record against the format without knowing the system
   that produced it.
4. **Derived records carry provenance.** A derived observation must name the
   records it was derived from, so a reviewer can separate "the derivation
   is wrong" from "the source signal is wrong."

## Relationship to the Agent Action Capsule

This is where we expect the convergence to live. If the Agent Action Capsule
defines what an agent action is (its structure, lifecycle, and state), the
evidence record spec defines how the record of that action can be verified
and graded. The two are complementary: the capsule is the thing being
evidenced, the evidence record is the audit-grade envelope around it. We are
happy to align field names and semantics so a capsule can carry an
evidence-graded envelope without a new format.

## Relationship to existing work

- **RATS (RFC 9334)**: the canonical split between what an Attester asserts
  and what a Verifier concludes. Our appraisal discipline borrows its
  vocabulary: evidence goes in, appraisal policy is the bridge, attestation
  results come out.
- **Record family conventions**: the vantage/method/basis axes and the closed
  vocabulary rule follow the same derivation discipline used in verification
  basis composition.
- **OTel gen_ai.***: call-level telemetry is one observation source; the
  model grades it rather than replacing it.
- **C2PA, Sigstore, RFC 3161**: adjacent integrity primitives, referenced by
  the E4 use case; the model treats them as markers, not as the model itself.

## Open questions for the WG

1. Does the Agent Action Capsule already define an evidence or verification
   component we should map onto, or is the envelope separate?
2. Should the E0-E4 grade be carried inside the capsule envelope, or attached
   as an appraisal result outside it? (Our discipline says the latter, to keep
   producer and verifier roles separate.)
3. Is the two-axis split (source/relationship, vantage/method) the right
   granularity, or should either axis collapse into the other?
4. Which parts of the validator (if any) would the WG want to adopt as a
   shared testbed for the capsule work?

## Suggested next steps

1. Steven shares the Agent Action Capsule docs ahead of the meeting, and we
   map the two models side by side before the session.
2. The WG reviews the validator against the capsule structure in a follow-up
   async thread, so the convergence is testable rather than prose-only.
3. If the capsule carries the evidence envelope, we produce a worked example:
   one capsule instance with an E4-graded, operationally-conformant envelope
   through a full delegation chain.

---

**End of draft. This is a pre-read for the WG meeting, not a new standard.
The engine that would produce these records is out of scope for this model.**
