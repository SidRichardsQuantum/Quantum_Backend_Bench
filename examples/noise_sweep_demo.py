"""Run a Cirq GHZ noise sweep."""

from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench.benchmarks.noise_sensitivity import build_benchmark as build_noise_suite
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.utils.formatting import format_results_table


def main() -> None:
    base = build_benchmark(n_qubits=5)
    results = []
    for spec in build_noise_suite(base):
        results.extend(run_benchmark(spec, ["cirq"], shots=128))
    print(format_results_table(results))


if __name__ == "__main__":
    main()
