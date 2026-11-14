# Removal evidence, v0.1

A record set and a verifier for one question that every assurance vocabulary
eventually has to answer: **if a sealed record is deleted, would anyone be able
to tell?**

This is the worked example offered to the AAIF Attestation and Evidence working
group in
[aaif/working-group-proposals#6](https://github.com/aaif/working-group-proposals/issues/6#issuecomment-6870040174).
It is deliberately small. Five entries, one removal, one witness, five cases.

## What the verifier checks

Three questions, and they do not have the same answer.

**1. Is every entry unaltered since it was sealed?**
Yes, locally. Each entry carries a SHA-256 digest over its own canonical JSON and
the digest of the entry before it.

**2. Does every gap have a removal record standing in its place?**
Partly, locally. A record dropped on its own leaves a sequence gap. A record
dropped together with the entries around it does not.

**3. Was a record, or a record and its removal record together, removed and the
log re-sealed afterwards?**
Only against a witness: a head digest published before the removal, held by a
party that does not hold the log.

## The cases

Run `python3 run_cases.py`. Every case is checked twice, once with the log alone
and once against `anchor.json`.

| case | local | anchored | what it is |
|---|---|---|---|
| `intact` | PASS | PASS | the log as sealed |
| `edited_payload` | FAIL | FAIL | a field changed after sealing |
| `deleted_no_removal` | FAIL | FAIL | an entry dropped, numbering left alone |
| `resealed_pair` | **PASS** | **FAIL** | a record and its removal record dropped together, the log renumbered, every digest recomputed |
| `removal_inconsistent` | FAIL | FAIL | a removal note kept beside the record it claims to have removed |

Three guard checks run alongside the cases, because a verifier that fails open is
worse than no verifier. A null anchor, a missing anchor file, and a malformed log
must each produce a `FAIL` verdict with its own code (`E_ANCHOR_UNUSABLE`,
`E_ANCHOR_UNREADABLE`, `E_LOG_UNREADABLE`). None of them may fall back to
local-only checks or answer with a traceback.

The fourth row is the point of the vector. A custodian who deletes a record and
the note that recorded the deletion, then rebuilds the chain, produces a log that
passes every local check. It is indistinguishable from a log where the record
never existed. The only thing that separates the two is a number the custodian
cannot rewrite.

That is why "would a deletion show?" is not answerable by the record alone. The
question has to name the witness.

## What the anchor is and is not

`anchor.json` holds the entry count and the head digest as they stood at seal
time, countersigned by the recipient of the records. It is small enough to be
quoted in an email, printed on a receipt, or published in a repository.

Not covered by this version:

- A witness that colludes with the custodian. The anchor is only as good as its
  independent holder.
- Anything that happened before the first anchor was published. A log can be
  rewritten wholesale up to that moment.
- Confidentiality. This proves what changed, not who was entitled to see it.

Those are the next three sections of a real threat model, and they belong in the
working group's guide rather than in this fixture.

## Run it

```
python3 gen_cases.py     # rewrite the corpus, byte for byte
python3 run_cases.py     # every case, local and anchored
python3 verify.py cases/intact
python3 verify.py cases/resealed_pair --anchor anchor.json
```

`verify.py` prints one JSON verdict and exits 0 on PASS, 1 on FAIL. It has no
dependencies beyond the Python standard library, so anyone can run it against
their own records without asking us for anything.

## Status

v0.1, 14 November 2026. Apache-2.0. Comments and failing cases welcome, and a
case that breaks the verifier is worth more to us than one that passes.
