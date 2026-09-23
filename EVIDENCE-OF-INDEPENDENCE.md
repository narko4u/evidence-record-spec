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
last refreshed 2026-09-22, when the grade-ceiling revision changed
`validate_evidence.py`, `evidence-record-0.1.schema.json` and the sample records.

## 1. Files covered (SHA-256, as of 2026-09-22)

| File | SHA-256 |
|---|---|
| README.md | `21d288eeed086d481187e32706420197fc76058eed9900abe053536c792a28e5` |
| LICENSE | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| evidence-record-0.1.schema.json | `63051fa3d8000768d61a96877edb2fdcbf53a16b3e1a13c6220400ad54fe04a1` |
| validate_evidence.py | `2c1e5e35fc09e5ec67245ac8eadd01f3270c0c39d74e2df85dc813a6ac0c7266` |
| samples/er-00001-e0-self-report.json | `acc3b72c46b52650ec4f31967872089e90440dae266a24aed52bba6e8dea441c` |
| samples/er-00002-e2-emission-conformant.json | `7640db187fd130c446ddcb59c47554d1c1674572d19e51a844abb09ebd8142f4` |
| samples/er-00003-e4-operationally-conformant.json | `72f2c233b71707098ed7e47f257432a9295e68c5142a51a8f015e693d136a129` |
| samples/er-00004-e3-contradiction.json | `a8b60cd6364910fdbc0326840af96f6c36abec74f54819cbfb3cab54a33789b0` |
| samples/er-00005-e3-derived-reconstructed.json | `8c6a35eaad22370008df4be92c9c82b94ddade42a468dd096346bcf6a8f6cd5d` |
| AAIF-SUBMISSION-DRAFT.md | `ff84a37b12bc108aa315270c35dcfa01125a160f4eee0f2ad83dcb7af3d33c00` |

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
- Author identity: narko4u <narko4u@users.noreply.github.com>, DCO signed

## 5. Storage locations of this record

- This file: EVIDENCE-OF-INDEPENDENCE.md (in-repo, travels with the code)
- Copy: held in a private, git-backed vault (never public)
- Verified hashes above pin the exact byte content at this date.
