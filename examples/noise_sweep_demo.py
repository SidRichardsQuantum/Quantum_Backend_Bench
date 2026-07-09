"""Run a compact GHZ noise sweep on an installed noise-capable backend."""

from __future__ import annotations

from _common import installed_noise_backends
from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench.benchmarks.noise_sensitivity import build_benchmark as build_noise_suite
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.utils.formatting import format_results_table


def main() -> None:
    backend = installed_noise_backends(limit=1)[0]
    base = build_benchmark(n_qubits=3)
    results = []
    for spec in build_noise_suite(base, noise_levels=[0.0, 0.005, 0.02]):
        results.extend(run_benchmark(spec, [backend], shots=64))
    print(f"Backend: {backend}")
    print(format_results_table(results))


if __name__ == "__main__":
    main()
