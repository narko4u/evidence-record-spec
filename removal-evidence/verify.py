#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Verify a record log that contains removals.

Three questions, in order of what a reader can actually establish:

1. Is every entry in the log unaltered since it was sealed?
   Answered locally. Each entry carries a digest over its own canonical bytes
   and the digest of the entry before it.

2. Is every record that should be in the log still in it, and does every gap
   have a removal record standing in its place?
   Answered locally, but only where the attacker is lazy. A dropped entry leaves
   a sequence gap. An entry dropped together with its neighbours does not.

3. Was a sealed record, or a record and its removal record together, removed and
   the log re-sealed afterwards?
   Not answerable from the log alone. It is answerable against an anchor: a head
   digest published somewhere the log holder does not control.

Usage:
    python3 verify.py <case-dir>                 # local checks only
    python3 verify.py <case-dir> --anchor FILE   # local checks plus witness

Exit code 0 on PASS, 1 on FAIL. Verdict is printed as JSON on one line.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

GENESIS = "GENESIS"


def canonical(obj: dict) -> bytes:
    """Canonical bytes for hashing: sorted keys, no whitespace, utf-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_of(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "digest"}
    return hashlib.sha256(canonical(body)).hexdigest()


def load_log(path: pathlib.Path) -> list[dict]:
    entries = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no} is not JSON: {exc}") from exc
    return entries


def verify(entries: list[dict], anchor: dict | None = None) -> dict:
    codes: list[str] = []
    detail: list[str] = []

    if not entries:
        return {"verdict": "FAIL", "codes": ["E_EMPTY"], "detail": ["log holds no entries"]}

    # R2, own digest
    for entry in entries:
        if entry.get("digest") != digest_of(entry):
            codes.append("E_DIGEST")
            detail.append(f"seq {entry.get('seq')} id {entry.get('id')} does not match its own digest")
            break

    # R1, sequence contiguity and chain linkage
    expected_seq = 1
    prev = GENESIS
    for entry in entries:
        if entry.get("seq") != expected_seq:
            codes.append("E_SEQ_GAP")
            detail.append(f"expected seq {expected_seq}, found {entry.get('seq')}")
            break
        if entry.get("prev") != prev:
            codes.append("E_LINK")
            detail.append(f"seq {entry.get('seq')} does not link to the entry before it")
            break
        prev = entry.get("digest")
        expected_seq += 1

    # R3, ids
    seen: set[str] = set()
    for entry in entries:
        ident = str(entry.get("id"))
        if ident in seen:
            codes.append("E_DUP_ID")
            detail.append(f"id {ident} appears more than once")
            break
        seen.add(ident)

    # R4, removals must not sit beside the record they claim to have removed
    actions = {e["id"] for e in entries if e.get("kind") == "action"}
    for entry in entries:
        if entry.get("kind") != "removal":
            continue
        target = entry.get("removes")
        if target in actions:
            codes.append("E_REMOVAL_INCONSISTENT")
            detail.append(f"removal {entry.get('id')} claims to remove {target}, which is still present")
        if target == entry.get("id"):
            codes.append("E_REMOVAL_SELF")
            detail.append(f"removal {entry.get('id')} removes itself")
        if not entry.get("reason"):
            codes.append("E_REMOVAL_NO_REASON")
            detail.append(f"removal {entry.get('id')} gives no reason")

    # R5, witness
    if anchor is not None:
        observed = {"count": len(entries), "head": entries[-1].get("digest")}
        if anchor.get("count") != observed["count"] or anchor.get("head") != observed["head"]:
            codes.append("E_ANCHOR_MISMATCH")
            detail.append(
                "log does not match the anchored head "
                f"(anchored count {anchor.get('count')} head {str(anchor.get('head'))[:16]}…, "
                f"observed count {observed['count']} head {str(observed['head'])[:16]}…)"
            )
    else:
        codes.append("W_NO_WITNESS")
        detail.append(
            "no anchor supplied: a record and its removal record removed together "
            "and the log re-sealed afterwards is not detectable here"
        )

    hard = [c for c in codes if c.startswith("E_")]
    return {
        "verdict": "FAIL" if hard else "PASS",
        "codes": codes,
        "detail": detail,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a record log with removals.")
    parser.add_argument("case", type=pathlib.Path, help="directory holding log.jsonl and optionally anchor.json")
    parser.add_argument("--anchor", type=pathlib.Path, default=None, help="anchor file (head digest) from outside the log")
    parser.add_argument("--quiet", action="store_true", help="print the verdict only, not the detail")
    args = parser.parse_args(argv)

    log_path = args.case / "log.jsonl"
    if not log_path.exists():
        print(json.dumps({"verdict": "FAIL", "codes": ["E_NO_LOG"], "detail": [f"{log_path} not found"]}))
        return 1

    entries = load_log(log_path)
    anchor = None
    if args.anchor is not None:
        anchor = json.loads(args.anchor.read_text(encoding="utf-8"))

    result = verify(entries, anchor)
    if args.quiet:
        print(result["verdict"])
    else:
        print(json.dumps(result, indent=1, ensure_ascii=False))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
