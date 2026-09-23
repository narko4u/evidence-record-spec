#!/usr/bin/env python3
"""Regenerate the CPB-registry appraisal vector artifact.

The appraisal KATs went stale when the record samples changed. Dropping the
producer-stamped `grade` member changed every record digest, and each appraisal
pins its subject by that digest, so every appraisal's canonical form and content
address moved with it. Regenerate from the files themselves so the artifact is a
true content address again.

The negative vectors are re-pointed at current content addresses on purpose. The
validator now enforces the citation binding (subject_record.digest must BE the
JCS SHA-256 of the record named), so a negative vector carrying a stale citation
would fail on the binding rather than on the defect it exists to pin, and would
quietly stop testing what it says it tests.
"""
import json, hashlib, collections
from pathlib import Path
import rfc8785

ROOT = Path(".")
P = ROOT / "vectors/cpb-registry/evidence-appraisal-vectors-v0.1.json"
d = json.loads(P.read_text(), object_pairs_hook=collections.OrderedDict)


def dig(path):
    return hashlib.sha256(rfc8785.dumps(json.loads(Path(path).read_text()))).hexdigest()


# current content address of the record the negative vectors cite
er3 = dig("samples/er-00003-e4-operationally-conformant.json")
print(f"current er-00003 digest: {er3}")

print("\n=== positives ===")
for e in d["positive"]:
    raw = json.loads((ROOT / e["input_file"]).read_text())
    canonical = rfc8785.dumps(raw)
    digest = hashlib.sha256(canonical).hexdigest()
    print(f"  {e['id']}")
    print(f"     len {e.get('canonical_length_bytes')} -> {len(canonical)}")
    print(f"     dig {str(e.get('expected_digest_bare_hex'))[:16]}... -> {digest[:16]}...")
    e["canonical_length_bytes"] = len(canonical)
    e["canonical_bytes_hex"] = canonical.hex()
    e["expected_digest_bare_hex"] = digest

print("\n=== negatives citing a record digest ===")
for e in d["negative"]:
    inp = e.get("input")
    if not isinstance(inp, dict):
        continue
    s = inp.get("subject_record") or {}
    old = s.get("digest")
    if s.get("record_id") != "er-00003" or not isinstance(old, str):
        continue
    if old.startswith("sha256:"):
        # the defect is the prefix, not the hex
        new = "sha256:" + er3
    elif old != old.lower():
        # the defect is the uppercase form, not the hex
        new = er3.upper()
    else:
        new = er3
    s["digest"] = new
    print(f"  {e['id']}: {old[:26]}... -> {new[:26]}...")

P.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(f"\nwrote {P}")

print("\n=== verify every positive digest reproduces ===")
bad = 0
for e in d["positive"]:
    raw = json.loads((ROOT / e["input_file"]).read_text())
    got = hashlib.sha256(rfc8785.dumps(raw)).hexdigest()
    ok = got == e["expected_digest_bare_hex"]
    bad += 0 if ok else 1
    print(f"  {'OK ' if ok else 'BAD'} {e['id']}")
print("all reproduce" if not bad else f"{bad} MISMATCH")

print("\n=== cross-check: every positive pins its subject's true digest ===")
for e in d["positive"]:
    a = json.loads((ROOT / e["input_file"]).read_text())
    s = a["subject_record"]
    matches = sorted((ROOT / "samples").glob(f"{s['record_id']}-*.json"))
    true = dig(matches[0])
    print(f"  {'OK ' if s['digest'] == true else 'BAD'} {e['id']} -> {s['record_id']}")
