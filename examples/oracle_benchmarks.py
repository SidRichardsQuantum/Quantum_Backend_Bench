"""Run deterministic oracle benchmarks with Cirq."""

from quantum_backend_bench.benchmarks.bernstein_vazirani import (
    build_benchmark as build_bernstein_vazirani,
)
from quantum_backend_bench.benchmarks.deutsch_jozsa import build_benchmark as build_deutsch_jozsa
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.summary import format_summary, summarize_results
from quantum_backend_bench.utils.formatting import format_results_table


def main() -> None:
    benchmarks = [
        build_bernstein_vazirani(n_qubits=6, secret_string="10110"),
        build_deutsch_jozsa(n_qubits=6, oracle_type="balanced", bitmask="10110"),
        build_deutsch_jozsa(n_qubits=6, oracle_type="constant", constant_value=1),
    ]

    results = []
    for benchmark in benchmarks:
        results.extend(run_benchmark(benchmark, ["cirq", "pennylane"], shots=256))

    print(format_results_table(results))
    print()
    print(format_summary(summarize_results(results)))


if __name__ == "__main__":
    main()
