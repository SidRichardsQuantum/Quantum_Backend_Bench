"""Benchmark runner implementation."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

from quantum_backend_bench.backends import get_backend
from quantum_backend_bench.backends.tket_analysis import analyze_with_tket
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec
from quantum_backend_bench.core.discovery import case_label
from quantum_backend_bench.core.environment import capture_environment
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
    repeats: int = 1,
    include_environment: bool = True,
) -> list[dict[str, Any]]:
    """Run a benchmark on one or more backends and return standardized dicts."""

    if repeats < 1:
        raise ValueError("repeats must be at least 1.")

    selected_metrics = set(metrics or DEFAULT_METRICS)
    structural = analyze_with_tket(benchmark)
    environment = capture_environment() if include_environment else None
    results: list[dict[str, Any]] = []

    for backend_name in backends:
        backend = get_backend(backend_name)
        executions = [backend.run(benchmark, shots=shots) for _ in range(repeats)]
        counts = _merge_counts(executions)
        total_shots = shots * repeats
        distribution = normalize_counts(counts, shots=total_shots)
        runtime_stats = _runtime_stats(executions)
        execution = executions[-1]

        metric_values: dict[str, Any] = {}
        if "depth" in selected_metrics:
            metric_values["depth"] = structural.get("depth")
        if "gate_count" in selected_metrics:
            metric_values["gate_count"] = structural.get("gate_count")
        if "two_qubit_gate_count" in selected_metrics:
            metric_values["two_qubit_gate_count"] = structural.get("two_qubit_gate_count")
        if "runtime_seconds" in selected_metrics:
            metric_values["runtime_seconds"] = runtime_stats["mean"]
            metric_values["runtime_seconds_mean"] = runtime_stats["mean"]
            metric_values["runtime_seconds_stddev"] = runtime_stats["stddev"]
            metric_values["runtime_seconds_min"] = runtime_stats["min"]
            metric_values["runtime_seconds_max"] = runtime_stats["max"]
        if "measurement_distribution" in selected_metrics:
            metric_values["measurement_distribution"] = distribution
        if "success_probability" in selected_metrics:
            target_state = benchmark.metadata.get("target_state") if benchmark.metadata else None
            metric_values["success_probability"] = (
                success_probability(counts, target_state, shots=total_shots)
                if target_state
                else None
            )
        if "total_variation_distance" in selected_metrics:
            metric_values["total_variation_distance"] = total_variation_distance(
                counts, benchmark.ideal_distribution, shots=total_shots
            )

        result = BenchmarkResult(
            benchmark=benchmark.name,
            backend=backend.name,
            n_qubits=benchmark.n_qubits,
            shots=shots,
            repeats=repeats,
            total_shots=total_shots,
            parameters=benchmark.parameters,
            metrics=metric_values,
            counts=counts,
            metadata={
                "analysis": structural,
                "benchmark_family": (benchmark.metadata or {}).get("family", benchmark.name),
                "case_label": case_label(benchmark.name, benchmark.n_qubits, benchmark.parameters),
                "noise_level": benchmark.parameters.get("noise_level"),
                "oracle_type": benchmark.parameters.get("oracle_type"),
                "seed": benchmark.parameters.get("seed"),
                "depth": benchmark.parameters.get("depth"),
                "repeats": repeats,
                "shots_per_repeat": shots,
                "total_shots": total_shots,
                "runtime_seconds_samples": runtime_stats["samples"],
                "environment": environment,
                **{
                    key: value
                    for key, value in execution.items()
                    if key not in {"counts", "runtime_seconds"}
                },
            },
        )
        results.append(result.to_dict())
    return results


def _merge_counts(executions: list[dict[str, Any]]) -> dict[str, int]:
    merged: Counter[str] = Counter()
    for execution in executions:
        merged.update(execution.get("counts", {}))
    return dict(merged)


def _runtime_stats(executions: list[dict[str, Any]]) -> dict[str, Any]:
    samples = [
        float(execution["runtime_seconds"])
        for execution in executions
        if execution.get("runtime_seconds") is not None
    ]
    if not samples:
        return {"samples": [], "mean": None, "stddev": None, "min": None, "max": None}
    return {
        "samples": samples,
        "mean": statistics.fmean(samples),
        "stddev": statistics.stdev(samples) if len(samples) > 1 else 0.0,
        "min": min(samples),
        "max": max(samples),
    }
