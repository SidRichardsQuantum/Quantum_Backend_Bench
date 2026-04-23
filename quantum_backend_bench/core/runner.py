"""Benchmark runner implementation."""

from __future__ import annotations

from typing import Any

from quantum_backend_bench.backends import get_backend
from quantum_backend_bench.backends.tket_analysis import analyze_with_tket
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec
from quantum_backend_bench.core.metrics import (
    normalize_counts,
    success_probability,
    total_variation_distance,
)
from quantum_backend_bench.core.results import BenchmarkResult

DEFAULT_METRICS = [
    "depth",
    "gate_count",
    "two_qubit_gate_count",
    "runtime_seconds",
    "measurement_distribution",
    "success_probability",
    "total_variation_distance",
]


def run_benchmark(
    benchmark: BenchmarkSpec,
    backends: list[str],
    metrics: list[str] | None = None,
    shots: int = 1024,
) -> list[dict[str, Any]]:
    """Run a benchmark on one or more backends and return standardized dicts."""

    selected_metrics = set(metrics or DEFAULT_METRICS)
    structural = analyze_with_tket(benchmark)
    results: list[dict[str, Any]] = []

    for backend_name in backends:
        backend = get_backend(backend_name)
        execution = backend.run(benchmark, shots=shots)
        counts = execution.get("counts", {})
        distribution = normalize_counts(counts, shots=shots)

        metric_values: dict[str, Any] = {}
        if "depth" in selected_metrics:
            metric_values["depth"] = structural.get("depth")
        if "gate_count" in selected_metrics:
            metric_values["gate_count"] = structural.get("gate_count")
        if "two_qubit_gate_count" in selected_metrics:
            metric_values["two_qubit_gate_count"] = structural.get("two_qubit_gate_count")
        if "runtime_seconds" in selected_metrics:
            metric_values["runtime_seconds"] = execution.get("runtime_seconds")
        if "measurement_distribution" in selected_metrics:
            metric_values["measurement_distribution"] = distribution
        if "success_probability" in selected_metrics:
            target_state = benchmark.metadata.get("target_state") if benchmark.metadata else None
            metric_values["success_probability"] = (
                success_probability(counts, target_state, shots=shots) if target_state else None
            )
        if "total_variation_distance" in selected_metrics:
            metric_values["total_variation_distance"] = total_variation_distance(
                counts, benchmark.ideal_distribution, shots=shots
            )

        result = BenchmarkResult(
            benchmark=benchmark.name,
            backend=backend.name,
            n_qubits=benchmark.n_qubits,
            shots=shots,
            parameters=benchmark.parameters,
            metrics=metric_values,
            counts=counts,
            metadata={
                "analysis": structural,
                **{
                    key: value
                    for key, value in execution.items()
                    if key not in {"counts", "runtime_seconds"}
                },
            },
        )
        results.append(result.to_dict())
    return results
