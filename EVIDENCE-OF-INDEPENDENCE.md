# Evidence of Independent Implementation

**Project:** evidence-record-spec
**Prepared:** 2026-08-29
**Status:** INTERNAL EVIDENCE RECORD (provenance, not marketing)

This file records the evidence that the evidence-record-spec repository
(schema, validator, samples, documentation) is an independent original
implementation, prepared in case the origin of any file is ever questioned.
It is not a substitute for legal advice; it is the raw material a lawyer
would use.

## 1. Files covered (SHA-256, as of 2026-08-29)

| File | SHA-256 |
|---|---|
| README.md | `56a66b5414562fef9bfae5008d7f2b56884f4f9e5e7c131439e09cff9211e863` |
| LICENSE | `e7b9d6c3d44c7f28ce0b4e4836567dd4b69fac6a5e99f51fdb11d0433db519f8` |
| evidence-record-0.1.schema.json | `44f6720f9c5977dca1f0a4a433c37467b248935e9165880b3418fc5b646bfcaf` |
| validate_evidence.py | `fa34405d08a098705cac81b31eb03c9b406894ecab8bc90c7d83f777e9a03566` |
| samples/er-00001-e0-self-report.json | `02049e8fec98fbfd90dc212468166d9a7695ada5bff078d547e4fd5e5dc7ddd5` |
| samples/er-00002-e2-emission-conformant.json | `268ea433346b5c6fb09e4c74eb57bd11e72303141f26161d822a2816256995d4` |
| samples/er-00003-e4-operationally-conformant.json | `cf6e7e0bc69be95408cd0e2a237774c3f62813509508e3cc6bd935e6d78a4da0` |
| samples/er-00004-e3-contradiction.json | `92982a30398644812a35c914f34e7aab904c206997f7333b2d28310caf117c63` |
| samples/er-00005-e3-derived-reconstructed.json | `b2b4c8285f3cb8fb254d1c6b77b29b78ed086841955525ac4e01fea10cb1be6c` |
| AAIF-SUBMISSION-DRAFT.md | `a021573166874a50828768844be1126bc03ad1c9389aafb7dcc0f5d0dd8fc4ff` |

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
