#!/usr/bin/env python3
"""Reject state JSON that contains duplicate keys (the Oct 14 ledger failure)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "data" / "state" / "portfolio.json",
    ROOT / "public" / "data" / "portfolio.json",
]


def _pairs(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(key)
        seen[key] = value
    return seen


def main() -> int:
    failed = False
    for path in FILES:
        if not path.exists():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
        except ValueError as exc:
            print(f"DUPLICATE JSON KEY in {path}: {exc}", file=sys.stderr)
            failed = True
        except json.JSONDecodeError as exc:
            print(f"INVALID JSON {path}: {exc}", file=sys.stderr)
            failed = True
    if failed:
        return 1
    print("State JSON keys OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
