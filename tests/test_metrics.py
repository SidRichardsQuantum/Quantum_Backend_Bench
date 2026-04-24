"""Metric tests."""

import pytest

from quantum_backend_bench.core.metrics import (
    normalize_counts,
    success_probability,
    total_variation_distance,
)
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.summary import summarize_results
from quantum_backend_bench.benchmarks.grover import build_benchmark as build_grover


def test_normalize_counts() -> None:
    assert normalize_counts({"00": 2, "11": 2}) == {"00": 0.5, "11": 0.5}


def test_success_probability() -> None:
    assert success_probability({"101": 9, "000": 1}, "101") == 0.9


def test_grover_success_probability_uses_marked_state(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeBackend:
        name = "fake"

        def run(self, benchmark, shots=1024):  # type: ignore[no-untyped-def]
            return {"counts": {"101": 7, "000": 1}, "runtime_seconds": 0.1}

    monkeypatch.setattr(
        "quantum_backend_bench.core.runner.get_backend",
        lambda _name: FakeBackend(),
    )
    result = run_benchmark(build_grover(n_qubits=3, marked_state="101"), ["fake"], shots=8)[0]
    assert result["metrics"]["success_probability"] == 0.875


def test_total_variation_distance() -> None:
    distance = total_variation_distance({"00": 6, "11": 4}, {"00": 0.5, "11": 0.5}, shots=10)
    assert distance == pytest.approx(0.1)


def test_summary_ranks_comparable_metrics() -> None:
    summary = summarize_results(
        [
            {
                "benchmark": "ghz",
                "backend": "slow",
                "n_qubits": 3,
                "parameters": {"n_qubits": 3},
                "metrics": {"runtime_seconds": 2.0, "depth": 3},
            },
            {
                "benchmark": "ghz",
                "backend": "fast",
                "n_qubits": 3,
                "parameters": {"n_qubits": 3},
                "metrics": {"runtime_seconds": 1.0, "depth": 4},
            },
        ]
    )
    group = summary["groups"][0]
    assert group["fastest_backend"]["backend"] == "fast"
    assert group["lowest_depth_backend"]["backend"] == "slow"
