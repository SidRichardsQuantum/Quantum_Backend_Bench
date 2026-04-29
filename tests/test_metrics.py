"""Metric tests."""

import pytest

from quantum_backend_bench.core.metrics import (
    normalize_counts,
    success_probability,
    total_variation_distance,
)
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.summary import format_summary, summarize_results
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


def test_run_benchmark_repeats_aggregate_counts_and_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeBackend:
        name = "fake"

        def __init__(self) -> None:
            self.calls = 0

        def run(self, benchmark, shots=1024):  # type: ignore[no-untyped-def]
            self.calls += 1
            return {"counts": {"101": shots}, "runtime_seconds": float(self.calls)}

    backend = FakeBackend()
    monkeypatch.setattr(
        "quantum_backend_bench.core.runner.get_backend",
        lambda _name: backend,
    )
    result = run_benchmark(
        build_grover(n_qubits=3, marked_state="101"),
        ["fake"],
        shots=8,
        repeats=3,
        include_environment=False,
    )[0]
    assert result["counts"] == {"101": 24}
    assert result["repeats"] == 3
    assert result["total_shots"] == 24
    assert result["metrics"]["runtime_seconds"] == pytest.approx(2.0)
    assert result["metrics"]["runtime_seconds_stddev"] == pytest.approx(1.0)
    assert result["metrics"]["success_probability"] == 1.0


def test_run_benchmark_rejects_invalid_shots() -> None:
    with pytest.raises(ValueError, match="shots must be at least 1"):
        run_benchmark(build_grover(n_qubits=3, marked_state="101"), ["fake"], shots=0)


def test_run_benchmark_rejects_invalid_repeats() -> None:
    with pytest.raises(ValueError, match="repeats must be at least 1"):
        run_benchmark(build_grover(n_qubits=3, marked_state="101"), ["fake"], repeats=0)


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


def test_summary_formats_float_values() -> None:
    text = format_summary(
        {
            "groups": [
                {
                    "benchmark": "ghz",
                    "n_qubits": 3,
                    "parameters": {"n_qubits": 3},
                    "fastest_backend": {"backend": "cirq", "value": 0.123456789},
                    "lowest_depth_backend": {"backend": "cirq", "value": 4},
                    "lowest_tvd_backend": {"backend": "cirq", "value": 0.0},
                }
            ]
        }
    )
    assert "0.123457" in text
    assert "lowest_depth_backend=cirq (4)" in text
    assert "0.000000" in text
