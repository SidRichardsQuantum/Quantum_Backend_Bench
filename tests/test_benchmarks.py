"""Benchmark builder tests."""

from collections import Counter

from quantum_backend_bench.benchmarks import ghz, grover, hamiltonian_sim, qft, random_circuit
from quantum_backend_bench.benchmarks.noise_sensitivity import build_benchmark as build_noise_suite
from quantum_backend_bench.core.suites import build_suite


def test_ghz_builder_sets_ideal_distribution() -> None:
    benchmark = ghz.build_benchmark(n_qubits=3)
    assert benchmark.name == "ghz"
    assert benchmark.ideal_distribution == {"000": 0.5, "111": 0.5}


def test_qft_builder_emits_operations() -> None:
    benchmark = qft.build_benchmark(n_qubits=3)
    assert benchmark.circuit_data.n_qubits == 3
    assert len(benchmark.circuit_data.operations) > 0


def test_qft_builder_has_expected_structure() -> None:
    benchmark = qft.build_benchmark(n_qubits=4)
    gates = Counter(operation.gate for operation in benchmark.circuit_data.operations)
    assert gates == {"H": 4, "CPHASE": 6, "SWAP": 2}
    assert benchmark.circuit_data.measurements == [0, 1, 2, 3]


def test_random_circuit_is_reproducible() -> None:
    a = random_circuit.build_benchmark(n_qubits=4, depth=10, seed=42)
    b = random_circuit.build_benchmark(n_qubits=4, depth=10, seed=42)
    assert a.circuit_data.operations == b.circuit_data.operations


def test_grover_tracks_target_state() -> None:
    benchmark = grover.build_benchmark(n_qubits=3, marked_state="101")
    assert benchmark.metadata["target_state"] == "101"


def test_hamiltonian_builder_tracks_parameters() -> None:
    benchmark = hamiltonian_sim.build_benchmark(n_qubits=2, time=1.0, trotter_steps=4)
    assert benchmark.parameters["trotter_steps"] == 4


def test_named_suite_builds_benchmark_specs() -> None:
    suite = build_suite("smoke")
    assert [benchmark.name for benchmark in suite] == ["ghz", "grover"]


def test_noise_suite_preserves_base_metadata_and_parameters() -> None:
    base = ghz.build_benchmark(n_qubits=3)
    noisy = build_noise_suite(base, noise_levels=[0.0, 0.01])
    assert [benchmark.parameters["noise_level"] for benchmark in noisy] == [0.0, 0.01]
    assert noisy[1].metadata["base_circuit"] is base.circuit_data
    assert noisy[1].ideal_distribution == base.ideal_distribution
