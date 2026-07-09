"""Compare a quantum-volume-style workload across installed local backends."""

from __future__ import annotations

from _common import installed_local_backends
from quantum_backend_bench.benchmarks.quantum_volume import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.summary import format_summary, summarize_results
from quantum_backend_bench.utils.formatting import format_results_table


def main() -> None:
    backends = installed_local_backends(limit=2)
    benchmark = build_benchmark(n_qubits=4, depth=4, seed=42)
    results = run_benchmark(benchmark, backends, shots=128)

    print(f"Backends: {', '.join(backends)}")
    print(format_results_table(results))
    print()
    print(format_summary(summarize_results(results)))


if __name__ == "__main__":
    main()
