"""Compare QFT on installed local backends and save a runtime/depth plot."""

from __future__ import annotations

from _common import installed_local_backends
from quantum_backend_bench.benchmarks.qft import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.utils.formatting import format_results_table
from quantum_backend_bench.utils.plotting import save_runtime_depth_plot


def main() -> None:
    backends = installed_local_backends(limit=2)
    benchmark = build_benchmark(n_qubits=4)
    results = run_benchmark(benchmark, backends, shots=64)
    print(f"Backends: {', '.join(backends)}")
    print(format_results_table(results))
    save_runtime_depth_plot(results, "artifacts/qft_compare.png")


if __name__ == "__main__":
    main()
