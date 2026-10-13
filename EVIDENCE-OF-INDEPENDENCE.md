# Evidence of Independent Implementation

**Project:** evidence-record-spec
**Prepared:** 2026-08-29
**Status:** INTERNAL EVIDENCE RECORD (provenance, not marketing)

This file records the evidence that the evidence-record-spec repository
(schema, validator, samples, documentation) is an independent original
implementation, prepared in case the origin of any file is ever questioned.
It is not a substitute for legal advice; it is the raw material a lawyer
would use.

The table below is a point-in-time snapshot and is refreshed on revision. It was
last refreshed 2026-10-13, on two changes. The PEER custody revision gave the
rule that a record reaches E3 on corroboration by a party other than the
deployment a named engine for the peer class (`counterparty_gateway`), which the
rule set grades as PEER under Axis C. It added one sample
(`samples/er-00006-e3-peer-corroboration.json`). The crosswalk publication added
`CROSSWALK.md` and extended the covered set to the appraisal samples, the
appraisal schema and both notice files. The corpus is now pinned as one digest
over its sorted member list. A third change the same day published the
definition of an independent party under Axis C in `VERIFIABILITY-OVERVIEW.md`,
replaced the count-based E3 row with the custody-based one and added discipline
rule 5. A fourth change the same day bounded E2 by what the format carries and
replaced the integrity-marker column, after a reported corpus run disagreed with
the derivation on three E2 cases and named two shipped cases that contradicted
the marker column. The disagreement is recorded as open items in the overview
rather than settled in a thread.

The refresh is no longer a matter of trust.
`.github/scripts/check_pinned_digests.py` recomputes every row below from the
shipped bytes and fails CI when a covered file changes, so the record cannot go
stale behind a commit again.

## 1. Files covered (SHA-256, as of 2026-10-13)

| File | SHA-256 |
|---|---|
| README.md | `7be60244f939b9cb37a2a077cc9b2138d7f215d0e62ad95fcc655e139b805b33` |
| CROSSWALK.md | `5d85b8b9288751fa1e9fa0323ebcc3cbb49924f0ac984f62156b1f4c0e98bbaf` |
| VERIFIABILITY-OVERVIEW.md | `7ee645198c560341edb168ad472406c151eff07d4ac1db5636a02c07c7916e65` |
| IMPLEMENTATIONS.md | `9826bb58becc79e85bc94305c2f655ab28e0e69d4450bfbeb060962e0a46c4c5` |
| AAIF-SUBMISSION-DRAFT.md | `ff84a37b12bc108aa315270c35dcfa01125a160f4eee0f2ad83dcb7af3d33c00` |
| NOTICE | `7070e13284e6402e0dd409cce60b2115b0a51ef50994772e08031e18521494ec` |
| LICENSE | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| CITATION.cff | `6e4b1ea7e1a9043ac33749990dbbbaecae6cc664b9ceb06936c19937a7b1e59b` |
| evidence-record-0.1.schema.json | `63051fa3d8000768d61a96877edb2fdcbf53a16b3e1a13c6220400ad54fe04a1` |
| evidence-appraisal-0.1.schema.json | `9b2fa634b100c4a5c3e54b896fea7fcd60a04937088cdfdc8fae442b442977ca` |
| validate_evidence.py | `b82dfb43177b22bf1f42f52efa829b3bab258c8456ce1537d392c03cf10bd03a` |
| evidence_grade_rules.py | `c88250e2ddf2e68569fafa5c13123613be289810a9ef50732b72be50a0f4d4d2` |
| grade_floor.py | `c9bbefbc18892af3e523739e999250cc5095879432fe1a9475acc9c0fe64e4f0` |
| gen_cases.py | `a83325be6a9691e7c2c5ee6d857123c4fbfc516e9eaca85b6f5998584e97babc` |
| samples/ea-00001-e4-agreement.json | `0f7a33126e93459146c008d7b01e4d847b8756382d2f9cd2277a261db2e2004c` |
| samples/ea-00002-e0-no-independent-evidence.json | `03b5e3ef06ff73fe2d56bc2193476596694525332133cd11703cb8bf7db37473` |
| samples/ea-00003-e2-contradiction.json | `436a401bf9868864bf3afc4e1e60a2d6fe58b63564bcc7df12951c1d4103cb10` |
| samples/er-00001-e0-self-report.json | `acc3b72c46b52650ec4f31967872089e90440dae266a24aed52bba6e8dea441c` |
| samples/er-00002-e2-emission-conformant.json | `7640db187fd130c446ddcb59c47554d1c1674572d19e51a844abb09ebd8142f4` |
| samples/er-00003-e4-operationally-conformant.json | `72f2c233b71707098ed7e47f257432a9295e68c5142a51a8f015e693d136a129` |
| samples/er-00004-e2-contradiction.json | `a8b60cd6364910fdbc0326840af96f6c36abec74f54819cbfb3cab54a33789b0` |
| samples/er-00005-e3-derived-reconstructed.json | `8c6a35eaad22370008df4be92c9c82b94ddade42a468dd096346bcf6a8f6cd5d` |
| samples/er-00006-e3-peer-corroboration.json | `e0f949cd4682313c96fd3134958efc1284b5f4c103caaa33d3bf0f8143348788` |
| grade-floor/ (corpus digest) | `2accb00326fc54b3706b78ba40a1b90605289249738a4c8dd27d43e884241178` |

The corpus row is the SHA-256 of the sorted `path digest` lines for every file
under `grade-floor/`, so the corpus is pinned as one value rather than as an archive.

## 2. Similarity audit (run 2026-08-29, vs the reference implementation on disk)

Method: Python `difflib.SequenceMatcher` on stripped source (docstrings and
comments removed, whitespace collapsed) for the validator; raw text
comparison for the schema.

| Comparison | Similarity | Longest shared run | What the shared run is |
|---|---|---|---|
| validate_evidence.py vs check_confidence_signal.py | 0.053 | 65 chars | standard imports: argparse/json/sys/pathlib |
| validate_evidence.py vs write_verification_basis.py | 0.051 | 65 chars | standard imports: argparse/json/sys/pathlib |
| evidence-record-0.1.schema.json vs ave-record-1.1.0.schema.json | 0.026 | 81 chars | `$schema`/`$id` header common to all JSON Schemas |

Interpretation: no copied logic, structure, docstrings, comments, or field
layout. Remaining similarity is boilerplate (imports, schema header).

## 3. Shared vocabulary (concepts, not expression)

The schema uses field names (vantage, method, basis, substrate, observation
source/relationship) that are common terminology in the agent observability
and evidence space. They appear in AAIF WG documents, adjacent record
projects, and our own issue contributions. Vocabulary is not copyrightable
expression; the arrangement and code are original to this project. See
README "Independent implementation notice".

## 4. Creation timeline

- 2026-08-29: repository authored in a private local workspace
- Commit d762c59: schema + validator + samples + README + submission draft
- Commit d87d670: independent implementation notice added
- 2026-10-13: PEER custody class added to the rule set (`counterparty_gateway`),
  with one new sample and two held discriminators, the peer case that must reach
  E3 and its twin, an engine name outside the vocabulary, that must not
- 2026-10-13: `CROSSWALK.md` published with an invitation to report independent
  mappings. The pinned-digest gate was added to CI
- Author identity: narko4u <narko4u@users.noreply.github.com>, DCO signed

## 5. Storage locations of this record

- This file: EVIDENCE-OF-INDEPENDENCE.md (in-repo, travels with the code)
- Copy: held in a private, git-backed vault (never public)
- Verified hashes above pin the exact byte content at this date.
- The pinned digests are rechecked on every push and pull request by
  `.github/scripts/check_pinned_digests.py`, so a covered file cannot change
  without the record being refreshed in the same commit.
