"""Analyze raw runtime samples from a repeated benchmark result."""

from __future__ import annotations

from quantum_backend_bench.benchmarks.qft import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark


def main() -> None:
    result = run_benchmark(
        build_benchmark(n_qubits=4),
        ["cirq"],
        shots=128,
        repeats=5,
    )[0]
    samples = result["metadata"]["runtime_seconds_samples"]
    metrics = result["metrics"]
    print("runtime samples:", ", ".join(f"{sample:.6f}" for sample in samples))
    print(f"mean: {metrics['runtime_seconds_mean']:.6f}")
    print(f"stddev: {metrics['runtime_seconds_stddev']:.6f}")
    print(f"min/max: {metrics['runtime_seconds_min']:.6f} / {metrics['runtime_seconds_max']:.6f}")


if __name__ == "__main__":
    main()
