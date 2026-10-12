#!/usr/bin/env bash
# Repo-specific checks for evidence-record-spec (run by .github/scripts/validate.py)
set -euo pipefail

python3 -c "import jsonschema" 2>/dev/null \
  || python3 -m pip install --quiet --disable-pip-version-check jsonschema

# The appraisal citation is verified, not trusted: subject_record.digest is a
# JCS (RFC 8785) SHA-256 over the named record, so canonicalization is required.
python3 -c "import rfc8785" 2>/dev/null \
  || python3 -m pip install --quiet --disable-pip-version-check rfc8785

# Positive samples: records and appraisals are separate schema families, and the
# schema is selected per file automatically.
python3 validate_evidence.py samples/

# Negative fixtures: each must be REJECTED. A fixture that starts passing means a
# grade-ceiling rule has regressed.
python3 fixtures/check_negative_fixtures.py
