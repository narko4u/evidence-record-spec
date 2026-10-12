# Crosswalk: this ladder and provenance-level schemes

The E0-E4 ladder is published in this repository. Other projects publish
provenance schemes that grade the same records on a different axis. This page
states how the two kinds of grade relate and how to report a mapping you
derive yourself.

## They grade different things

A **provenance level** grades the record: where the signing key lived and
whether the runtime that produced the record is the one it names.

An **E-grade** grades the observation path of the action: who or what saw the
action happen and what would have to be true for the record to be missing it.

A record can be strong on one axis and weak on the other and the two failures
look different:

- a hardware-attested, transparency-anchored record can describe an action that
  no independent party ever observed at its destination
- a destination-corroborated, externally anchored chain can be produced by a
  runtime with no attestation at all

Neither kind of grade is a substitute for the other. A level read as an
E-grade or an E-grade read as a level, is the assurance overclaim both kinds
of scheme exist to prevent: a conclusion written stronger than the evidence
behind it.

## The ladder, one line per rung

| Grade | Name | The observation it needs |
|---|---|---|
| E0 | Declared | The agent claims it acted. No independent observation. |
| E1 | Observed | An instrumented component saw the action. Gaps are possible. |
| E2 | Enforced | The action could not have occurred without the authorising step, because the only path to the effect ran through it. |
| E3 | Corroborated | A party that is not the deployment confirmed the effect. |
| E4 | Anchored | The chain is externally timestamped and checkpointed, so alteration and backdating are detectable. |

Definitions, the assignment rule and the public provenance of the ladder are in
[`VERIFIABILITY-OVERVIEW.md`](VERIFIABILITY-OVERVIEW.md).

## Provenance levels, one line each

| Level | What it binds |
|---|---|
| Level 0 | The record is software-signed. |
| Level 1 | The record is bound to hardware evidence, so the producing workload was measured in silicon. |
| Level 2 | Transparency anchoring is added, so the record's existence is publicly provable by a time boundary. |

TRACE v0.2 is one such scheme, published as "TRACE Specification, a Series of
LF Projects, LLC". The lines above summarise what that specification publishes.
Where the two documents disagree, each speaks for itself: this page critiques
neither scheme and grades neither of them.

## Where the two axes meet

Anchoring on one axis and E4 on the other answer the same question, whether the
record's existence is externally bounded and later alteration is detectable.
The substrates differ, a transparency log with inclusion proofs on one side
and trusted timestamping plus a published checkpoint on the other. They compose
rather than compete: an E4 chain can anchor its checkpoint in a transparency
log. Everywhere else the axes are separate, so a provenance level does not
raise an E-grade and an E-grade does not raise a level.

## What a consumer should ask for

For any claimed evidence of agent action, ask the vendor:

1. **Observation path** : which grade applies and what would have to be true
   for the record to be missing this action?
2. **Enforcement** : could the action have occurred without the authorising
   step or is the step advisory?
3. **Authorisation evidence** : which system holds it and does its record
   establish who approved, on a basis the approver cannot later repudiate?
4. **Outcome** : did the destination confirm the effect or is the effect
   inferred from the agent's own report?
5. **Origin and anchoring** : was the producing runtime measured and is the
   record's existence provable by an external time boundary?
6. **Bounded verification statement** : at what depth was verification
   performed, what evidence did not resolve and what is the strongest
   statement that verification supports?

A vendor that answers only 5 has a signed record about an unobserved action. A
vendor that answers only 1 has observed an action whose provenance is unknown.
The pairing is the point.

## Report the mapping you derive

This page carries no mapping table. A mapping between two schemes is a claim
about both of them and it should be checkable by whoever reads it rather than
asserted by whichever project writes it down. Derive your own and report it:

- your scheme, with a link to the definitions you publish
- the level definitions you applied, quoted from your own text
- the E-grade you map each level to and the rung of this ladder you mapped
  from
- every point where you disagree with a line on this page, with the reason

Agreement is not the requirement for being listed. A named disagreement is the
more useful contribution, because it is the only thing that tells us which line
of this page is ambiguous. Mappings we receive are listed in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md), at the maintainers' discretion and
without endorsement of either scheme.

Teams that want a mapping built and maintained for them can ask Empire Labs
Pty Ltd for a scoped engagement, which is a paid route.

---

## Provenance of the ladder

The E0-E4 ladder is a published evidence-grading model for agent records:
E0 Declared, E1 Observed, E2 Enforced, E3 Corroborated, E4 Anchored, with E4
requiring external trusted timestamping, Merkle checkpointing and independent
verifiability. It is referenced in the Agentic AI Foundation's Observability
and Traceability working group as prior work in that group's use case document
for tamper-evident evidence
([use case E4](https://github.com/aaif/wg-observability-and-traceability/blob/main/working-documents/USE-CASES.md),
merged 2026-08-18) and in the group's
[prior-work registry](https://github.com/aaif/wg-observability-and-traceability/blob/main/working-documents/PRIOR-WORK.md),
which records the ladder alongside the public material describing it. The rung
names were also published, as concepts, in the Identity and Trust working
group's issue #5 (2026-08-25).

Schemes named on this page belong to their own projects. Statements about a
scheme here are one-line summaries of its published text and that scheme's own
document is authoritative for its own definitions.

---

## License

Documentation on this page: CC-BY-4.0, as with the rest of this repository's
documentation.
