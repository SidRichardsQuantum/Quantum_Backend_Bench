"""Benchmark builder tests."""

from quantum_backend_bench.benchmarks import ghz, grover, hamiltonian_sim, qft, random_circuit


def test_ghz_builder_sets_ideal_distribution() -> None:
    benchmark = ghz.build_benchmark(n_qubits=3)
    assert benchmark.name == "ghz"
    assert benchmark.ideal_distribution == {"000": 0.5, "111": 0.5}


def test_qft_builder_emits_operations() -> None:
    benchmark = qft.build_benchmark(n_qubits=3)
    assert benchmark.circuit_data.n_qubits == 3
    assert len(benchmark.circuit_data.operations) > 0


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
