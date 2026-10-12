#!/usr/bin/env python3
# Evidence Record Specification
# Copyright (c) 2026 Empire Labs Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""Disclosure firewall: this repository must carry the format, never the engine.

The published format is the exam. The mechanism that produces records at these
grades is out of scope here and lives in a private repository, so a term that
belongs to the mechanism has no business appearing in a public tree. Run this
before any push; CI runs it on every pull request.

    python3 .github/scripts/firewall_check.py

Exit 0 means clean, 1 means a denied term was found and the push must not happen.
"""
from __future__ import annotations

import re
import subprocess
import sys

# Terms that identify the private mechanism, a private path, or another product
# tree. `witness_scope` is deliberately NOT here: it is the published vocabulary
# term, documented in VERIFIABILITY-OVERVIEW.md by design.
DENIED = [
    r"witnessos",
    r"witness[-_]os",
    r"/home/vault",
    r"/mnt/c/[Vv]aultSentinel",
    r"soverlink",
    r"agentcore",
    r"guildx",
    r"shiftproof",
    r"tethr",
    r"private[- ]repo detail",
    r"discriminator table",
]

ALLOWED_EXCEPTIONS: list[tuple[str, str]] = []

# This file necessarily contains the deny list, so it is exempt from its own
# scan by exact path. Nothing else is exempt: a narrowed exception is how a
# firewall stops being a firewall.
SELF = ".github/scripts/firewall_check.py"


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    return [f for f in out.stdout.splitlines() if f.strip() and f != SELF]


def main() -> int:
    findings: list[str] = []
    patterns = [(t, re.compile(t, re.I)) for t in DENIED]
    for path in tracked_files():
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for term, rx in patterns:
                if rx.search(line):
                    findings.append(f"{path}:{lineno}: /{term}/ {line.strip()[:100]}")

    if findings:
        print("FIREWALL FAIL: private-mechanism terms found in a public tree")
        for f in findings:
            print(f"  {f}")
        return 1
    print(f"firewall clean: {len(tracked_files())} tracked files, {len(DENIED)} denied patterns, 0 findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
