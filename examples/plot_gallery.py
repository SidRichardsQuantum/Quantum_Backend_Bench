"""Generate distribution, heatmap, noise-quality, and suite plots."""

from __future__ import annotations

from _common import installed_local_backends, installed_noise_backends
from quantum_backend_bench.benchmarks.ghz import build_benchmark as build_ghz
from quantum_backend_bench.benchmarks.grover import build_benchmark as build_grover
from quantum_backend_bench.benchmarks.noise_sensitivity import build_benchmark as build_noise_suite
from quantum_backend_bench.benchmarks.quantum_volume import build_benchmark as build_quantum_volume
from quantum_backend_bench.benchmarks.random_circuit import build_benchmark as build_random_circuit
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.suites import build_suite
from quantum_backend_bench.utils.plotting import (
    save_counts_heatmap,
    save_distribution_plot,
    save_noise_quality_plot,
    save_suite_runtime_plot,
)


def main() -> None:
    comparison_backends = installed_local_backends(limit=2)
    noise_backend = installed_noise_backends(limit=1)[0]

    grover_results = run_benchmark(
        build_grover(n_qubits=3, marked_state="101"),
        comparison_backends,
        shots=128,
    )
    save_distribution_plot(grover_results, "artifacts/grover_distribution.png", top_k=8)

    heatmap_results = []
    heatmap_results.extend(
        run_benchmark(
            build_random_circuit(n_qubits=4, depth=8, seed=11),
            comparison_backends,
            shots=128,
        )
    )
    heatmap_results.extend(
        run_benchmark(
            build_quantum_volume(n_qubits=4, depth=4, seed=17),
            comparison_backends,
            shots=128,
        )
    )
    save_counts_heatmap(heatmap_results, "artifacts/random_workloads_heatmap.png", top_k=12)

    noise_results = []
    for benchmark in build_noise_suite(build_ghz(n_qubits=3), noise_levels=[0.0, 0.005, 0.02]):
        noise_results.extend(run_benchmark(benchmark, [noise_backend], shots=64))
    save_noise_quality_plot(noise_results, "artifacts/ghz_noise_quality.png")

    suite_results = []
    for benchmark in build_suite("smoke"):
        suite_results.extend(run_benchmark(benchmark, comparison_backends, shots=64))
    save_suite_runtime_plot(suite_results, "artifacts/smoke_suite_runtime.png")

    print("Saved plot gallery under artifacts/")
    print(f"Comparison backends: {', '.join(comparison_backends)}")
    print(f"Noise backend: {noise_backend}")


if __name__ == "__main__":
    main()
