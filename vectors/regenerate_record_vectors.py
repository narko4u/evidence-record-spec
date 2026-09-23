#!/usr/bin/env python3
"""Regenerate the CPB-registry vector artifact after the grade-derivation fix.

The samples changed (the stamped `grade` member is gone), so every pinned
canonical form and digest in the KAT set is stale. Regenerate from the files
themselves so the artifact is a true content address again.
"""
import json, hashlib, collections
from pathlib import Path
import rfc8785

ROOT = Path(".")
p = ROOT / "vectors/cpb-registry/evidence-record-vectors-v0.1.json"
d = json.loads(p.read_text(), object_pairs_hook=collections.OrderedDict)

print("=== positives ===")
for e in d["positive"]:
    f = ROOT / e["input_file"]
    raw = json.loads(f.read_text())
    canonical = rfc8785.dumps(raw)
    digest = hashlib.sha256(canonical).hexdigest()
    old_len = e.get("canonical_length_bytes")
    old_dig = e.get("expected_digest_bare_hex")
    e["canonical_length_bytes"] = len(canonical)
    e["canonical_bytes_hex"] = canonical.hex()
    e["expected_digest_bare_hex"] = digest
    if "description" in e and "14-member" in e["description"]:
        e["description"] = e["description"].replace(
            "14-member closed field set", "13-member closed field set"
        )
    print(f"  {e['id']}")
    print(f"     len {old_len} -> {len(canonical)}")
    print(f"     dig {old_dig[:16]}... -> {digest[:16]}...")

kat03 = next(e for e in d["positive"] if e["id"].startswith("er-kat-03"))
new_dig = kat03["expected_digest_bare_hex"]

print()
print("=== negatives that reference kat03 ===")
for e in d["negative"]:
    if e["id"] == "er-fail-05-representation-confusion":
        e["bare_form_of_kat03"] = new_dig
        e["prefixed_form_of_kat03"] = "sha256:" + new_dig
        print(f"  {e['id']}: bare/prefixed updated")
    if e["id"] == "er-fail-06-uppercase-hex":
        e["input_digest"] = new_dig.upper()
        print(f"  {e['id']}: input_digest updated")

print()
print("=== er-fail-01 (grade is no longer a record member at all) ===")
for e in d["negative"]:
    if e["id"] == "er-fail-01-unregistered-grade":
        e["description"] = (
            "Closed shape: the evidence record has no `grade` member. The grade is an "
            "output of appraisal (VERIFIABILITY-OVERVIEW.md discipline rule 1) and a "
            "producer that stamps one MUST be rejected, not tolerated as an unknown "
            "member. A record carrying `grade` is refused outright, so an asserted rung "
            "can never be read out of a record. This is the deliberate inversion of the "
            "CPB never-reject invariant (Capsule section 4): an unrecognised member is a "
            "failure."
        )
        e["expected"] = "REJECT (additionalProperties: grade is not a record member)"
        print(f"  {e['id']}: reframed")

p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print()
print("wrote", p)

# sanity: the pinned digests must now match the files on disk
print()
print("=== verify every positive digest reproduces ===")
bad = 0
for e in d["positive"]:
    raw = json.loads((ROOT / e["input_file"]).read_text())
    got = hashlib.sha256(rfc8785.dumps(raw)).hexdigest()
    ok = got == e["expected_digest_bare_hex"]
    bad += 0 if ok else 1
    print(f"  {'OK ' if ok else 'BAD'} {e['id']}")
print("all reproduce" if not bad else f"{bad} MISMATCH")
