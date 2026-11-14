#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Generate the removal-evidence corpus deterministically.

The same five sealed entries are written once as `intact`, then mutated four
ways. Each mutation is a thing an operator might do after the fact, ranging from
careless to deliberate.

The published anchor (`anchor.json`) is the head digest as it stood when the log
was sealed. It is the witness: a party that does not hold the log holds this
number, so any re-seal that changes the head is visible to them and invisible to
everyone who only has the log.

    python3 gen_cases.py
    python3 run_cases.py
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
CASES = HERE / "cases"
GENESIS = "GENESIS"

BASE = [
    {
        "seq": 1,
        "kind": "action",
        "id": "ev-0001",
        "at": "2026-11-01T09:00:00Z",
        "actor": "agent:minutes-bot",
        "action": "approve",
        "payload": {"subject": "invoice-4412", "amount_aud": 1250, "approver": "principal"},
    },
    {
        "kind": "removal",
        "id": "rm-0001",
        "at": "2026-11-02T08:12:00Z",
        "removes": "ev-0002",
        "by": "custodian:school-office",
        "reason": "erasure request from a named recipient",
    },
    {
        "kind": "action",
        "id": "ev-0003",
        "at": "2026-11-03T10:30:00Z",
        "actor": "agent:minutes-bot",
        "action": "record",
        "payload": {"subject": "incident-2026-11-03", "severity": "minor"},
    },
    {
        "kind": "action",
        "id": "ev-0004",
        "at": "2026-11-03T10:35:00Z",
        "actor": "agent:minutes-bot",
        "action": "export",
        "payload": {"subject": "incident-2026-11-03", "as": "docx"},
    },
]


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def seal(entries: list[dict]) -> list[dict]:
    """Number, link and digest a chain. Mutates and returns the list."""
    out = []
    prev = GENESIS
    for seq, entry in enumerate(entries, start=1):
        body = copy.deepcopy(entry)
        body.pop("digest", None)
        body["seq"] = seq
        body["prev"] = prev
        body["digest"] = hashlib.sha256(canonical(body)).hexdigest()
        prev = body["digest"]
        out.append(body)
    return out


def write_case(name: str, entries: list[dict]) -> None:
    path = CASES / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    lines = [json.dumps(e, sort_keys=True, ensure_ascii=False) for e in entries]
    (path / "log.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    CASES.mkdir(exist_ok=True)

    sealed = seal(BASE)

    # The published head, taken when the log was sealed and handed to a party
    # that does not hold the log. Everything below is judged against this.
    anchor = {
        "count": len(sealed),
        "head": sealed[-1]["digest"],
        "published_at": "2026-11-03T11:00:00Z",
        "publisher": "custodian:school-office",
        "note": "head digest countersigned by the audit recipient at seal time",
    }
    (HERE / "anchor.json").write_text(json.dumps(anchor, indent=1) + "\n", encoding="utf-8")

    # 1. Untouched.
    write_case("intact", sealed)

    # 2. A payload edited after sealing, digests left alone.
    edited = copy.deepcopy(sealed)
    edited[3]["payload"]["severity"] = "serious"
    write_case("edited_payload", edited)

    # 3. An entry dropped, numbering left alone. Careless deletion.
    dropped = [e for e in sealed if e["id"] != "ev-0003"]
    write_case("deleted_no_removal", dropped)

    # 4. The removed record's removal record dropped too, the log renumbered,
    #    every digest recomputed. The log now claims the record never existed.
    #    Identical to `intact` under local checks; only the witness separates them.
    resealed = seal([copy.deepcopy(e) for e in sealed if e["kind"] != "removal"])
    write_case("resealed_pair", resealed)

    # 5. The removal record kept beside the record it claims to have removed.
    #    Someone restored a backup without retiring the removal note.
    restored = copy.deepcopy(sealed[0])
    restored.update({
        "kind": "action",
        "id": "ev-0002",
        "at": "2026-11-01T09:04:00Z",
        "actor": "agent:minutes-bot",
        "action": "send",
        "payload": {"subject": "minutes-2026-11-01", "recipients": 2},
    })
    restored.pop("digest", None)
    entries = [copy.deepcopy(e) for e in BASE]
    entries.insert(1, restored)
    write_case("removal_inconsistent", seal(entries))

    expected = {
        "intact": {"local": "PASS", "anchored": "PASS", "codes": []},
        "edited_payload": {"local": "FAIL", "anchored": "FAIL", "codes": ["E_DIGEST"]},
        "deleted_no_removal": {"local": "FAIL", "anchored": "FAIL", "codes": ["E_SEQ_GAP"]},
        "resealed_pair": {"local": "PASS", "anchored": "FAIL", "codes": ["W_NO_WITNESS", "E_ANCHOR_MISMATCH"]},
        "removal_inconsistent": {"local": "FAIL", "anchored": "FAIL", "codes": ["E_REMOVAL_INCONSISTENT"]},
    }
    (CASES / "expected.json").write_text(json.dumps(expected, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
