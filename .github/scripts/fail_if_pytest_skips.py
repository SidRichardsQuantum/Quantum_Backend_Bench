"""Fail a CI step when a pytest smoke run silently skipped selected tests."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fail_if_pytest_skips.py <pytest-output-file>", file=sys.stderr)
        return 2

    output = Path(sys.argv[1]).read_text(encoding="utf-8")
    if "no tests ran" in output or "collected 0 items" in output:
        print("Selected pytest smoke run collected no tests.", file=sys.stderr)
        return 1

    skipped = sum(int(match.group(1)) for match in re.finditer(r"\b(\d+) skipped\b", output))
    if skipped:
        print(f"Selected pytest smoke run skipped {skipped} test(s).", file=sys.stderr)
        return 1

    if not re.search(r"\b(\d+) passed\b", output):
        print("Selected pytest smoke run did not report any passing tests.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
