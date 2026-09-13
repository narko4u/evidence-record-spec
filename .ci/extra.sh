#!/usr/bin/env bash
# Repo-specific checks for evidence-record-spec (run by .github/scripts/validate.py)
set -euo pipefail

python3 -c "import jsonschema" 2>/dev/null \
  || python3 -m pip install --quiet --disable-pip-version-check jsonschema

# Evidence-record samples validate against the record schema.
python3 validate_evidence.py --schema evidence-record-0.1.schema.json samples/er-*.json

# Evidence-appraisal samples validate against the appraisal schema.
python3 validate_evidence.py --schema evidence-appraisal-0.1.schema.json samples/ea-*.json
