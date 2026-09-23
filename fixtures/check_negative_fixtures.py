#!/usr/bin/env python3
"""Assert that every fixture under fixtures/negative/ is REJECTED.

Positive samples must pass; negative fixtures must fail. A fixture that starts
passing means a ceiling rule has regressed and the validator would once again let
a record assert a grade its own observation does not support.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
FIXTURES = HERE / "fixtures" / "negative"
SAMPLES = HERE / "samples"

def run(paths):
    r = subprocess.run(
        [sys.executable, str(HERE / "validate_evidence.py")] + [str(p) for p in paths],
        cwd=HERE, capture_output=True, text=True,
    )
    return r.returncode, r.stdout + r.stderr

failures = []

# every negative fixture, on its own, must be rejected
for f in sorted(FIXTURES.glob("*.json")):
    rc, out = run([f])
    expected = HERE / "samples" / f"{json.loads(f.read_text()).get('subject_record', {}).get('record_id', '')}-"

    # appraisal fixtures need their subject record beside them to resolve
    extra = []
    if "subject_record" in json.loads(f.read_text()):
        rid = json.loads(f.read_text())["subject_record"]["record_id"]
        matches = sorted(SAMPLES.glob(f"{rid}-*.json"))
        extra = matches

    if extra:
        rc, out = run([f] + extra)

    if rc == 0:
        failures.append(f)
        print(f"FAIL {f.name} was ACCEPTED (it must be rejected)")
    else:
        first = next((l.strip(" -") for l in out.splitlines() if l.strip().startswith("-")), "")
        print(f"ok   {f.name} rejected")
        if first:
            print(f"       reason: {first[:150]}")

# the positive sample set must still pass
rc, out = run([SAMPLES])
if rc != 0:
    print("\nFAIL the positive sample set no longer validates:")
    print(out)
    failures.append(SAMPLES)

print()
if failures:
    print(f"{len(failures)} fixture problem(s)")
    sys.exit(1)
print("all negative fixtures rejected, positive samples pass")
