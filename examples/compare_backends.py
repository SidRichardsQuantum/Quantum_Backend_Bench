"""Compare QFT and save a plot."""

from quantum_backend_bench.benchmarks.qft import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.utils.formatting import format_results_table
from quantum_backend_bench.utils.plotting import save_runtime_depth_plot


def main() -> None:
    benchmark = build_benchmark(n_qubits=5)
    results = run_benchmark(benchmark, ["cirq", "pennylane", "braket_local"])
    print(format_results_table(results))
    save_runtime_depth_plot(results, "artifacts/qft_compare.png")


if __name__ == "__main__":
    main()
