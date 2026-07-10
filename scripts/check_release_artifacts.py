"""Validate built wheel and source distribution release artifacts."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

MAX_SDIST_BYTES = 15 * 1024 * 1024

EXPECTED_SDIST_SUFFIXES = {
    "README.md",
    "USAGE.md",
    "docs/RELEASE_POLICY.md",
    "docs/schemas/internal-circuit.schema.json",
    "examples/reference_results/cirq_smoke_2026-06-03/smoke_suite_cirq.json",
    "notebooks/01_quickstart_cirq.ipynb",
    "tests/test_packaging.py",
}

EXPECTED_WHEEL_SUFFIXES = {
    "quantum_backend_bench/__init__.py",
    "quantum_backend_bench/cli.py",
    "quantum_backend_bench/presets/runtime.json",
}

FORBIDDEN_WHEEL_PREFIXES = (
    "docs/",
    "examples/",
    "notebooks/",
    "tests/",
)


def main(argv: list[str] | None = None) -> int:
    paths = [Path(value) for value in (argv or sys.argv[1:])]
    wheel = _one(paths, ".whl")
    sdist = _one(paths, ".tar.gz")

    _check_sdist(sdist)
    _check_wheel(wheel)
    return 0


def _one(paths: list[Path], suffix: str) -> Path:
    matches = [path for path in paths if path.name.endswith(suffix)]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one {suffix} artifact, found {len(matches)}.")
    return matches[0]


def _check_sdist(path: Path) -> None:
    size = path.stat().st_size
    if size > MAX_SDIST_BYTES:
        raise SystemExit(
            f"{path} is {size} bytes, above the reviewed sdist budget of {MAX_SDIST_BYTES}."
        )

    with tarfile.open(path, "r:gz") as archive:
        names = archive.getnames()

    _require_suffixes(path, names, EXPECTED_SDIST_SUFFIXES)


def _check_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()

    _require_suffixes(path, names, EXPECTED_WHEEL_SUFFIXES)
    unexpected = [name for name in names if name.startswith(FORBIDDEN_WHEEL_PREFIXES)]
    if unexpected:
        joined = ", ".join(sorted(unexpected)[:10])
        raise SystemExit(f"{path} includes non-package files in the wheel: {joined}")


def _require_suffixes(path: Path, names: list[str], suffixes: set[str]) -> None:
    missing = [
        suffix for suffix in sorted(suffixes) if not any(name.endswith(suffix) for name in names)
    ]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"{path} is missing expected release content: {joined}")


if __name__ == "__main__":
    raise SystemExit(main())
