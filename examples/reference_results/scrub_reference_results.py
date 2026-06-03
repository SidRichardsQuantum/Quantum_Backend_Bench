"""Scrub volatile fields from committed reference result artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REFERENCE_ROOT = Path(__file__).resolve().parent
VOLATILE_METRICS = {
    "runtime_seconds",
    "runtime_seconds_mean",
    "runtime_seconds_min",
    "runtime_seconds_max",
    "runtime_seconds_stddev",
    "compile_seconds",
    "compile_seconds_stddev",
}
VOLATILE_CSV_COLUMNS = {
    "runtime_seconds",
    "runtime_seconds_stddev",
}
VOLATILE_METADATA_KEYS = {
    "backend_package_versions",
    "compile_seconds_samples",
    "runtime_seconds_samples",
}
STABLE_ENVIRONMENT = {
    "reference_result": True,
    "note": "Volatile environment, package, git, runtime, and compile timing fields are scrubbed.",
}


def scrub_reference_directory(directory: str | Path) -> list[Path]:
    """Scrub JSON and CSV reference artifacts below a directory."""

    root = Path(directory)
    changed: list[Path] = []
    for path in sorted(root.glob("*.json")):
        scrub_json_file(path)
        changed.append(path)
    for path in sorted(root.glob("*.csv")):
        scrub_csv_file(path)
        changed.append(path)
    return changed


def scrub_json_file(path: str | Path) -> None:
    """Scrub volatile fields from a JSON result list in place."""

    destination = Path(path)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a result list in {destination}")
    for result in payload:
        _scrub_result(result)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scrub_csv_file(path: str | Path) -> None:
    """Blank volatile timing columns from a CSV result table in place."""

    destination = Path(path)
    with destination.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if fieldnames is None:
        raise ValueError(f"Expected a header row in {destination}")
    for row in rows:
        for column in VOLATILE_CSV_COLUMNS:
            if column in row:
                row[column] = ""
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _scrub_result(result: dict[str, Any]) -> None:
    metrics = result.get("metrics", {})
    for key in VOLATILE_METRICS:
        if key in metrics:
            metrics[key] = None

    metadata = result.get("metadata", {})
    for key in VOLATILE_METADATA_KEYS:
        if key in metadata:
            metadata[key] = [] if key.endswith("_samples") else {}
    if "environment" in metadata:
        metadata["environment"] = dict(STABLE_ENVIRONMENT)


def main() -> int:
    for directory in sorted(path for path in REFERENCE_ROOT.iterdir() if path.is_dir()):
        changed = scrub_reference_directory(directory)
        if changed:
            print(f"Scrubbed {directory.relative_to(REFERENCE_ROOT)}: {len(changed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
