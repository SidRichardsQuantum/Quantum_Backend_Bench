"""Tabular result helper tests."""

from __future__ import annotations

import json

from quantum_backend_bench.core.dataframe import results_to_dataframe, results_to_records


def _sample_results() -> list[dict]:
    return [
        {
            "benchmark": "ghz",
            "backend": "cirq",
            "n_qubits": 3,
            "shots": 8,
            "repeats": 1,
            "total_shots": 8,
            "parameters": {"n_qubits": 3},
            "metrics": {
                "runtime_seconds": 0.1,
                "runtime_seconds_stddev": 0.0,
                "depth": 4,
                "gate_count": 3,
                "two_qubit_gate_count": 2,
                "success_probability": None,
                "total_variation_distance": 0.0,
            },
            "counts": {"000": 4, "111": 4},
            "metadata": {
                "case_label": "ghz n=3",
                "benchmark_family": "entanglement",
                "local_only": True,
            },
        }
    ]


def test_results_to_records_flattens_result() -> None:
    records = results_to_records(_sample_results())
    assert records[0]["case_label"] == "ghz n=3"
    assert records[0]["runtime_seconds"] == 0.1
    assert records[0]["counts"] == json.dumps({"000": 4, "111": 4}, sort_keys=True)


def test_results_to_dataframe_accepts_saved_json(tmp_path) -> None:
    path = tmp_path / "results.json"
    path.write_text(json.dumps(_sample_results()), encoding="utf-8")
    frame = results_to_dataframe(path)
    assert list(frame["backend"]) == ["cirq"]
    assert list(frame["depth"]) == [4]
