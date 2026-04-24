"""Experiment manifest tests."""

from __future__ import annotations

import json

import pytest

from quantum_backend_bench.core.manifest import load_manifest, run_experiment_manifest


def test_load_json_manifest(tmp_path) -> None:
    manifest_path = tmp_path / "experiment.json"
    manifest_path.write_text(
        json.dumps({"backends": ["fake"], "benchmarks": [{"benchmark": "ghz"}]}),
        encoding="utf-8",
    )
    assert load_manifest(manifest_path)["backends"] == ["fake"]


def test_run_experiment_manifest_writes_outputs(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    output_path = tmp_path / "results.json"
    csv_path = tmp_path / "results.csv"
    manifest_path = tmp_path / "experiment.json"
    manifest_path.write_text(
        json.dumps(
            {
                "backends": ["fake"],
                "shots": 8,
                "repeats": 2,
                "benchmarks": [{"benchmark": "ghz", "n_qubits": 3}],
                "outputs": {"json": str(output_path), "csv": str(csv_path)},
            }
        ),
        encoding="utf-8",
    )

    def fake_run_benchmark(benchmark, backends, shots=1024, repeats=1):  # type: ignore[no-untyped-def]
        return [
            {
                "benchmark": benchmark.name,
                "backend": backends[0],
                "n_qubits": benchmark.n_qubits,
                "shots": shots,
                "repeats": repeats,
                "total_shots": shots * repeats,
                "parameters": benchmark.parameters,
                "metrics": {"runtime_seconds": 0.1},
                "counts": {"000": shots * repeats},
                "metadata": {"case_label": "ghz n=3", "benchmark_family": "entanglement"},
            }
        ]

    monkeypatch.setattr("quantum_backend_bench.core.manifest.run_benchmark", fake_run_benchmark)
    bundle = run_experiment_manifest(manifest_path)
    assert bundle["results"][0]["repeats"] == 2
    assert output_path.exists()
    assert csv_path.exists()


def test_manifest_noise_levels_expand_cases(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    manifest_path = tmp_path / "noise.json"
    manifest_path.write_text(
        json.dumps(
            {
                "backends": ["fake"],
                "benchmarks": [{"benchmark": "ghz", "n_qubits": 3, "noise_levels": [0.0, 0.01]}],
            }
        ),
        encoding="utf-8",
    )
    seen = []

    def fake_run_benchmark(benchmark, backends, shots=1024, repeats=1):  # type: ignore[no-untyped-def]
        seen.append(benchmark.parameters["noise_level"])
        return []

    monkeypatch.setattr("quantum_backend_bench.core.manifest.run_benchmark", fake_run_benchmark)
    run_experiment_manifest(manifest_path)
    assert seen == [0.0, 0.01]
