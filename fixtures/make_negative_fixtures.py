#!/usr/bin/env python3
"""Generate the negative regression fixtures derived from the review on
aaif/wg-observability-and-traceability#37 (2026-09-22).

Each fixture starts from a shipped sample and changes only what the attack needs.
Every one of them MUST be rejected.
"""
import json, collections, hashlib
from pathlib import Path
import rfc8785

S = Path("samples")
OUT = Path("fixtures/negative")
OUT.mkdir(parents=True, exist_ok=True)

def load(name):
    return json.loads((S / name).read_text(), object_pairs_hook=collections.OrderedDict)

def dig(name):
    """JCS (RFC 8785) SHA-256 content address of a sample, computed from the file
    itself so a fixture can never pin a digest that has gone stale."""
    return hashlib.sha256(rfc8785.dumps(load(name))).hexdigest()

def dump(doc, name):
    p = OUT / name
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"  wrote {p}")

# nr-01: a self-report declaring its own integrity markers, claiming
# operationally-conformant. The producer asserts E4-grade hygiene about its own
# account. Must reject: ceiling for agent_self_report is E0, and the claim needs E3.
d = load("er-00001-e0-self-report.json")
d["record_id"] = "nr-01"
d["integrity"] = collections.OrderedDict([
    ("signed", True), ("chain_linked", True), ("timestamped", True),
    ("verifiable_by", ["anyone"]),
])
d["claims"] = [collections.OrderedDict([("claim", "operationally-conformant"),
                                        ("evidence", ["nr-01"])])]
dump(d, "nr-01-self-report-claiming-operationally-conformant.json")

# nr-02: a record whose own reconciliation says the agent was contradicted, still
# carrying an operationally-conformant claim. Must reject on the state rule.
d = load("er-00004-e3-contradiction.json")
d["record_id"] = "nr-02"
d["claims"] = [collections.OrderedDict([("claim", "operationally-conformant"),
                                        ("evidence", ["nr-02"])])]
dump(d, "nr-02-contradiction-claiming-operationally-conformant.json")

# nr-03: an E3-stage claim on a boundary observation with no corroboration. Must
# reject on the corroboration gate: one basis engine, a direct relationship and
# no recorded boundary observation caps the record at E2. Source alone would have
# allowed E4, so this fixture isolates the gate rather than the source cap.
d = load("er-00004-e3-contradiction.json")
d["record_id"] = "nr-03"
d["observation"] = collections.OrderedDict([
    ("source", "gateway_proxy"), ("relationship", "direct"),
    ("directness", "direct_observation"),
])
d["reconciliation"]["state"] = "agreement"
d["reconciliation"]["boundary_observation"] = "none recorded"
d["claims"] = [collections.OrderedDict([("claim", "operationally-conformant"),
                                        ("evidence", ["nr-03"])])]
dump(d, "nr-03-E3-claim-without-corroboration.json")

# nr-05: a boundary observation whose basis still rests on the actor's own account.
# Must reject on the self-report-only rule inside the gate: a basis that includes
# the actor's own reporting is not corroboration, whatever else is in the list.
d = load("er-00004-e3-contradiction.json")
d["record_id"] = "nr-05"
d["verification"]["basis_engines"] = ["gateway_proxy", "self_report"]
d["reconciliation"]["state"] = "agreement"
d["claims"] = [collections.OrderedDict([("claim", "operationally-conformant"),
                                        ("evidence", ["nr-05"])])]
dump(d, "nr-05-corroboration-resting-on-self-report.json")

# nr-04: an appraisal concluding a rung above the ceiling its subject supports.
# The digest is the TRUE content address of er-00001 so this fixture isolates the
# ceiling rule and not the citation binding.
d = collections.OrderedDict([
    ("schema_version", "0.1.0"),
    ("appraisal_id", "nr-04"),
    ("subject_record", collections.OrderedDict([("record_id", "er-00001"), ("digest", dig("er-00001-e0-self-report.json"))])),
    ("e_grade", "E4"),
    ("claim_type", "emission-conformant"),
    ("reconciliation_state", "no_independent_evidence"),
    ("verifier_id", "verifier-alpha"),
    ("timestamp", "2026-09-22T00:00:00+00:00"),
    ("signed", True),
])
dump(d, "nr-04-appraisal-above-subject-ceiling.json")

# nr-06: an appraisal attributing a claim the subject never made. er-00004 claims
# emission-conformant only; this appraises operationally-conformant. Must reject
# on the claim_type binding. (This is the shape the shipped ea-00003 sample had.)
d = collections.OrderedDict([
    ("schema_version", "0.1.0"),
    ("appraisal_id", "nr-06"),
    ("subject_record", collections.OrderedDict([("record_id", "er-00004"), ("digest", dig("er-00004-e3-contradiction.json"))])),
    ("e_grade", "E3"),
    ("claim_type", "operationally-conformant"),
    ("reconciliation_state", "contradiction"),
    ("verifier_id", "verifier-beta"),
    ("timestamp", "2026-09-22T00:00:00+00:00"),
    ("signed", True),
])
dump(d, "nr-06-appraisal-claims-what-subject-never-claimed.json")

# nr-07: a well-formed but WRONG subject digest. Passes the schema pattern, so
# only the citation binding can catch it. Must reject, otherwise the ceiling can
# be computed over one record while the appraisal pins another.
d = collections.OrderedDict([
    ("schema_version", "0.1.0"),
    ("appraisal_id", "nr-07"),
    ("subject_record", collections.OrderedDict([("record_id", "er-00003"), ("digest", "0" * 64)])),
    ("e_grade", "E4"),
    ("claim_type", "operationally-conformant"),
    ("reconciliation_state", "agreement"),
    ("verifier_id", "verifier-alpha"),
    ("timestamp", "2026-09-22T00:00:00+00:00"),
    ("signed", True),
])
dump(d, "nr-07-appraisal-subject-digest-does-not-bind.json")

print("\nnegative fixtures written")
