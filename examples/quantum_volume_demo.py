"""Compare a quantum-volume-style workload across local backends."""

from quantum_backend_bench.benchmarks.quantum_volume import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.summary import format_summary, summarize_results
from quantum_backend_bench.utils.formatting import format_results_table


def main() -> None:
    benchmark = build_benchmark(n_qubits=5, depth=6, seed=42)
    results = run_benchmark(benchmark, ["cirq", "pennylane", "braket_local"], shots=512)

    print(format_results_table(results))
    print()
    print(format_summary(summarize_results(results)))


if __name__ == "__main__":
    main()
