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

def run(paths, extra=()):
    r = subprocess.run(
        [sys.executable, str(HERE / "validate_evidence.py"), *extra] + [str(p) for p in paths],
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

# --- paired regression: the same appraisal, with and without its subject ------
# Whether a defect is caught must not depend on which files happened to be
# passed. A subject-absent appraisal is reported UNRESOLVED and rejected, and
# supplying the subject must not be what decides the outcome.
print()
print("paired regression: same appraisal, subject supplied vs absent")

PAIRED = [
    # (appraisal, subject id, subject-absent must be rejected, present must be rejected)
    (FIXTURES / "nr-07-appraisal-subject-digest-does-not-bind.json", "er-00003", True, True),
    (SAMPLES / "ea-00001-e4-agreement.json", "er-00003", True, False),
]

for appraisal, rid, absent_rejects, present_rejects in PAIRED:
    subjects = sorted(SAMPLES.glob(f"{rid}-*.json"))
    if not subjects:
        print(f"FAIL {appraisal.name}: no subject record '{rid}' to pair with")
        failures.append(appraisal)
        continue

    rc_absent, out_absent = run([appraisal])
    rc_present, _ = run([appraisal] + subjects)

    absent_bad = (rc_absent == 0) if absent_rejects else (rc_absent != 0)
    silent_pass = absent_rejects and rc_absent != 0 and "UNRESOLVED" not in out_absent
    verdict_absent = "ACCEPTED" if rc_absent == 0 else "rejected"
    print(f"{'FAIL' if (absent_bad or silent_pass) else 'ok  '} {appraisal.name} alone"
          f" -> rc={rc_absent} ({verdict_absent}"
          f"{', not reported UNRESOLVED' if silent_pass else ''})")
    if absent_bad or silent_pass:
        failures.append(appraisal)

    present_bad = (rc_present == 0) if present_rejects else (rc_present != 0)
    verdict_present = "ACCEPTED" if rc_present == 0 else "rejected"
    print(f"{'FAIL' if present_bad else 'ok  '} {appraisal.name} + {rid}"
          f" -> rc={rc_present} ({verdict_present})")
    if present_bad:
        failures.append(appraisal)

    # --schema-only is the explicit, intentional weaker mode: schema-valid on
    # its own with no semantics attempted. It must be reachable, and it must be
    # the only way to get a pass out of a subject-absent appraisal.
    rc_schema, _ = run([appraisal], extra=["--schema-only"])
    print(f"{'ok  ' if rc_schema == 0 else 'FAIL'} {appraisal.name} alone --schema-only"
          f" -> rc={rc_schema}")
    if rc_schema != 0:
        failures.append(appraisal)

print()
if failures:
    print(f"{len(failures)} fixture problem(s)")
    sys.exit(1)
print("all negative fixtures rejected, positive samples pass")
