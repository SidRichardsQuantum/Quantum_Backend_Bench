"""Reference result fixture tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = ROOT / "examples" / "reference_results"
VOLATILE_METRICS = {
    "runtime_seconds",
    "runtime_seconds_mean",
    "runtime_seconds_min",
    "runtime_seconds_max",
    "runtime_seconds_stddev",
    "compile_seconds",
    "compile_seconds_stddev",
}


def test_reference_json_artifacts_are_scrubbed() -> None:
    json_files = _benchmark_reference_files("*.json")
    assert json_files
    for path in json_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, list), path
        for result in payload:
            metrics = result.get("metrics", {})
            for key in VOLATILE_METRICS:
                assert metrics.get(key) is None, f"{path} has volatile metric {key}"

            metadata = result.get("metadata", {})
            assert metadata.get("environment", {}).get("reference_result") is True
            assert metadata.get("backend_package_versions") == {}
            assert metadata.get("runtime_seconds_samples") == []
            if "compile_seconds_samples" in metadata:
                assert metadata.get("compile_seconds_samples") == []


def test_reference_csv_artifacts_have_blank_runtime_columns() -> None:
    csv_files = _benchmark_reference_files("*.csv")
    assert csv_files
    for path in csv_files:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows, path
        for row in rows:
            assert row["runtime_seconds"] == ""
            assert row["runtime_seconds_stddev"] == ""


def test_sdk_audit_reference_artifacts_are_valid() -> None:
    audit_dir = REFERENCE_ROOT / "sdk_audits_2026-06-05"
    expected = {"sdk_parity", "noise_matrix", "roundtrip_audit"}

    for stem in expected:
        assert (audit_dir / f"{stem}.json").exists()
        assert (audit_dir / f"{stem}.csv").exists()
        assert (audit_dir / f"{stem}.md").exists()

    roundtrip = json.loads((audit_dir / "roundtrip_audit.json").read_text(encoding="utf-8"))
    assert roundtrip
    assert all(row["status"] == "passed" for row in roundtrip)
    assert {"circuit_roundtrip", "hamiltonian_roundtrip", "workflow_roundtrip"} <= {
        row["audit"] for row in roundtrip
    }


def _benchmark_reference_files(pattern: str) -> list[Path]:
    return sorted(
        path
        for path in REFERENCE_ROOT.glob(f"*/{pattern}")
        if path.parent.name != "sdk_audits_2026-06-05"
    )
