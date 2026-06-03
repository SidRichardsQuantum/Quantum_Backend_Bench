"""Result bundle tests."""

from __future__ import annotations

import json

from quantum_backend_bench.core.bundle import create_result_bundle


def test_create_result_bundle_writes_core_artifacts(tmp_path) -> None:
    results = [
        {
            "benchmark": "ghz",
            "backend": "cirq",
            "n_qubits": 3,
            "shots": 8,
            "repeats": 1,
            "total_shots": 8,
            "parameters": {"n_qubits": 3},
            "metrics": {"runtime_seconds": 0.1, "depth": 4},
            "counts": {"000": 4, "111": 4},
            "metadata": {"case_label": "ghz n=3", "backend_noise_support": "depolarizing"},
        }
    ]
    source = tmp_path / "results.json"
    source.write_text(json.dumps(results), encoding="utf-8")

    paths = create_result_bundle(source, tmp_path / "bundle", include_plots=False)

    assert (tmp_path / "bundle" / "results.json").exists()
    assert (tmp_path / "bundle" / "results.csv").exists()
    assert (tmp_path / "bundle" / "records.json").exists()
    assert "ghz n=3" in (tmp_path / "bundle" / "report.md").read_text(encoding="utf-8")
    assert "README" in paths["readme"]
