"""Generate distribution, heatmap, noise-quality, and suite plots."""

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
    grover_results = run_benchmark(
        build_grover(n_qubits=3, marked_state="101"),
        ["cirq", "pennylane", "braket_local"],
        shots=512,
    )
    save_distribution_plot(grover_results, "artifacts/grover_distribution.png", top_k=8)

    heatmap_results = []
    heatmap_results.extend(
        run_benchmark(
            build_random_circuit(n_qubits=5, depth=18, seed=11),
            ["cirq", "pennylane"],
            shots=512,
        )
    )
    heatmap_results.extend(
        run_benchmark(
            build_quantum_volume(n_qubits=5, depth=5, seed=17),
            ["cirq", "pennylane"],
            shots=512,
        )
    )
    save_counts_heatmap(heatmap_results, "artifacts/random_workloads_heatmap.png", top_k=16)

    noise_results = []
    noise_levels = [0.0, 0.005, 0.01, 0.02, 0.035, 0.05]
    for benchmark in build_noise_suite(build_ghz(n_qubits=5), noise_levels=noise_levels):
        noise_results.extend(run_benchmark(benchmark, ["cirq"], shots=256))
    save_noise_quality_plot(noise_results, "artifacts/ghz_noise_quality.png")

    suite_results = []
    for benchmark in build_suite("standard"):
        suite_results.extend(run_benchmark(benchmark, ["cirq", "pennylane"], shots=128))
    save_suite_runtime_plot(suite_results, "artifacts/standard_suite_runtime.png")

    print("Saved plot gallery under artifacts/")


if __name__ == "__main__":
    main()
