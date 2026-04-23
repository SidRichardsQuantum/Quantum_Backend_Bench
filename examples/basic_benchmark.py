"""Run GHZ across all backends."""

from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.utils.formatting import format_results_table


def main() -> None:
    benchmark = build_benchmark(n_qubits=5)
    results = run_benchmark(benchmark, ["cirq", "pennylane", "braket_local"])
    print(format_results_table(results))


if __name__ == "__main__":
    main()
