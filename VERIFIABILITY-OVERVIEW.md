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

### Axis C: witness_scope

Who is able to produce the record at all, and can the deployment bring that
party into agreement with itself?

The two axes above describe how evidence was obtained and how strong it is.
This axis answers a different question, the custody question. A record can be
strongly obtained and still held only by the party it describes.

| Scope | Who can observe satisfaction | Evidence comes from |
|---|---|---|
| SELF | The deployment's own reports; the enforcement point is the only party able to produce the evidence | The deployment's own account, with no external path |
| PEER | Another party within an agreement: a counterparty, a peer mediating the same interaction, or a tenant | Artifacts exchanged within the agreement |
| EXTERNAL | A party outside the trust domain: an auditor, a regulator, or any non-trusting third party | Artifacts obtainable and checkable without cooperation from the enforcement point |

**Assignment rule.** A requirement is SELF-scope unless a concrete artifact
path exists that lets the named witness check it without relying on the
enforcement point's own account. Most enforcement requirements are SELF-only
under current wire formats. That is a finding, not a failure, and it is
recorded as such.

**Scope is orthogonal to the strength grade.** A record held by an EXTERNAL
party can still be the emitter's own account of itself, if the external party
holds a symmetric key the emitter also holds. A substrate-vantage record can
be SELF-scope, when only the deployment can produce it. Keeping custody and
forgeability as separate questions is what stops a summary value from letting
a SELF-scope deployment read as externally witnessed.

An enforcement requirement with no EXTERNAL witness basis is a first-class
open item rather than a silent default, so a reader can see which
requirements are only ever checked by the party being checked.

**Provenance.** The term `witness_scope` and the SELF / PEER / EXTERNAL grading
were proposed by Empire Labs and placed on the public record starting
2026-08-26, inside a bounded verdict envelope whose field names are all
snake_case (`verification_basis`, `evidence_refs`, `verifier_signature` and
`witness_scope` among them):

- First written use of the term, 2026-08-26T12:21:56Z, AAIF agentic commerce
  working group, issue #5, body line 32:
  https://github.com/aaif/wg-agentic-commerce/issues/5
- First proposal of the grading in the Agent Control Standard,
  2026-08-28T07:53:31Z:
  https://github.com/GenAI-Security-Project/agent-control-standard/issues/33#issuecomment-5449932104
- Definitions table, 2026-08-28T13:04:26Z:
  https://github.com/GenAI-Security-Project/agent-control-standard/issues/33#issuecomment-5452852355
- Filed as a taxonomy term at AAIF, 2026-08-29:
  https://github.com/aaif/ws-taxonomy-landscape/issues/53

Our spelling is `witness_scope`, matching the snake_case field names it was
first written among. The camelCase token `witnessScope` also exists as a term
of art in an unrelated protocol, where it names a transaction witness's
verification scope, and it appears as a field name in one public evidence
corpus. Neither of those is this. This document defines the grading, not the
spelling, and the uses are unrelated. Cite the definition rather than a token.

### What makes a party independent

E3 rests on a party that is not the deployment, so the definition of an
independent party carries the rung. Custody decides it, never count. The
custody classes are the three in Axis C above and they are a closed set: SELF,
PEER, EXTERNAL.

A party is not independent of a claim when any of the following holds:

- it is operated, owned or paid by the party whose claim is being graded
- it shares an enforcement point with that party, so one change bypasses both
- its statement about the claim is derived from the claim rather than from the
  effect the claim describes
- it is the same custody named twice

The consequences are the ones the runnable corpus already enforces:

- agreement between components of one deployment does not reach E3, at any
  number of components named
- the deployment's own enforcement point grades as SELF custody, so it can
  reach E2 and cannot reach E3 on its own account
- a party that hosts, resells or embeds the deployment without observing the
  effect for itself is SELF custody for the purpose of the rung

E4 adds an anchor rather than a fourth custody class. Anchoring is a property
of the receipt, so an E4 receipt carries a grade and an anchor, never a claim
of an independent custodian.

### The E0-E4 evidence strength ladder

Axes A and B compose into a grade used to state, in one label, how anchored
the evidence is:

| Grade | Name | What it means | What the derivation reads |
|---|---|---|---|
| E0 | Declared | agent self-report, no independent verification | `observation.source` is the agent's own account |
| E1 | Observed | the action observed outside the acting agent | a source outside the agent, with gaps still possible |
| E2 | Enforced | a boundary component of the deployment recorded the action | `observation.source` names a boundary component of the deployment |
| E3 | Corroborated | corroboration by a party that is not the deployment, at PEER or EXTERNAL custody | an engine in Axis C custody, at PEER or EXTERNAL |
| E4 | Anchored | external timestamping, chain-linking, independent verifiability | E3 custody, plus `timestamped`, `chain_linked` and a verifier other than the agent |

**Integrity markers do not cap a rung from E0 to E3.** They record presence,
not mechanism (discipline rule 3) and the derivation reads `timestamped` and
`chain_linked` only for the E4 anchor gate. `signed` is descriptive today and is
read by nothing, so an unsigned record can reach E3 when its corroboration
holds. E4 is the one rung whose markers are constitutive, because an anchor that
is neither timestamped nor chained is not an anchor.

**E2 is bounded by what the format carries.** A record names the party that made
the observation. It carries no field for the route an action took, so an E2 here
says that a boundary component of the deployment recorded the action. It does
not say the action had no other route. A deployment that can demonstrate the
route holds stronger evidence than this format can express. The difference
is recorded as an open item below.

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
   than it executed. The validator enforces this by deriving a ceiling from the
   record's own observation and refusing anything above it. The record carries
   `observation.source`, `relationship`, `basis_engines` and
   `reconciliation.state`, and those facts cap the rung, so a self-report cannot
   be promoted by declaring its own integrity markers. A record cannot carry a
   grade member at all, and an appraisal cannot conclude above the ceiling its
   subject record supports.
2. **Closed vocabulary, fail closed.** An unrecognised value is a failure,
   not a new rung. A typo cannot silently raise a record's strength.
3. **Integrity markers record presence, not mechanism.** The schema says a
   record is signed, chained, and timestamped; it does not say how. An
   auditor can verify a record against the format without knowing the system
   that produced it.
4. **Derived records carry provenance.** A derived observation must name the
   records it was derived from, so a reviewer can separate "the derivation
   is wrong" from "the source signal is wrong."
5. **Independence is custody, not count.** A grade rests on who could have
   produced the evidence, never on how many parties agreed. Two components of
   one deployment are one party, so naming a second engine the deployment
   controls raises no rung. The disqualifiers are stated under Axis C.

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
5. Should the format carry the route an action took? E2 rests on the party that
   observed rather than on the path taken, because no field carries
   reachability.
6. Should the derivation read `declared_vs_observed`? A record whose permitted
   action and observed occurrence disagree derives the same rung as one where
   they agree, because the field is carried and never read.

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
