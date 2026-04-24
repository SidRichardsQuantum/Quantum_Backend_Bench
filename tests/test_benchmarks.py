"""Benchmark builder tests."""

from collections import Counter

import pytest

from quantum_backend_bench.benchmarks import (
    bernstein_vazirani,
    deutsch_jozsa,
    ghz,
    grover,
    hamiltonian_sim,
    qft,
    quantum_volume,
    random_circuit,
)
from quantum_backend_bench.benchmarks.noise_sensitivity import build_benchmark as build_noise_suite
from quantum_backend_bench.core.suites import build_suite


def test_ghz_builder_sets_ideal_distribution() -> None:
    benchmark = ghz.build_benchmark(n_qubits=3)
    assert benchmark.name == "ghz"
    assert benchmark.ideal_distribution == {"000": 0.5, "111": 0.5}


def test_bernstein_vazirani_tracks_secret_string() -> None:
    benchmark = bernstein_vazirani.build_benchmark(n_qubits=4, secret_string="101")
    assert benchmark.name == "bernstein_vazirani"
    assert benchmark.circuit_data.n_qubits == 4
    assert benchmark.circuit_data.measurements == [0, 1, 2]
    assert benchmark.ideal_distribution == {"101": 1.0}
    assert benchmark.metadata["target_state"] == "101"


def test_bernstein_vazirani_rejects_wrong_secret_length() -> None:
    with pytest.raises(ValueError, match="3 for n_qubits=4"):
        bernstein_vazirani.build_benchmark(n_qubits=4, secret_string="10")


def test_bernstein_vazirani_rejects_non_bit_secret() -> None:
    with pytest.raises(ValueError, match="only 0 and 1"):
        bernstein_vazirani.build_benchmark(n_qubits=4, secret_string="10x")


def test_deutsch_jozsa_balanced_oracle_tracks_bitmask() -> None:
    benchmark = deutsch_jozsa.build_benchmark(n_qubits=4, oracle_type="balanced", bitmask="101")
    assert benchmark.name == "deutsch_jozsa"
    assert benchmark.circuit_data.measurements == [0, 1, 2]
    assert benchmark.ideal_distribution == {"101": 1.0}
    assert benchmark.metadata["target_state"] == "101"


def test_deutsch_jozsa_constant_oracle_targets_zero_string() -> None:
    benchmark = deutsch_jozsa.build_benchmark(n_qubits=4, oracle_type="constant", constant_value=1)
    assert benchmark.ideal_distribution == {"000": 1.0}


def test_deutsch_jozsa_rejects_zero_balanced_bitmask() -> None:
    with pytest.raises(ValueError, match="balanced"):
        deutsch_jozsa.build_benchmark(n_qubits=4, oracle_type="balanced", bitmask="000")


def test_deutsch_jozsa_rejects_wrong_bitmask_length() -> None:
    with pytest.raises(ValueError, match="3 for n_qubits=4"):
        deutsch_jozsa.build_benchmark(n_qubits=4, bitmask="10")


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


def test_quantum_volume_is_reproducible_and_layered() -> None:
    a = quantum_volume.build_benchmark(n_qubits=4, depth=3, seed=7)
    b = quantum_volume.build_benchmark(n_qubits=4, depth=3, seed=7)
    assert a.circuit_data.operations == b.circuit_data.operations
    assert a.parameters == {"n_qubits": 4, "depth": 3, "seed": 7}
    assert Counter(operation.gate for operation in a.circuit_data.operations)["CNOT"] == 12


def test_quantum_volume_rejects_non_positive_depth() -> None:
    with pytest.raises(ValueError, match="depth must be at least 1"):
        quantum_volume.build_benchmark(n_qubits=4, depth=0)


def test_grover_tracks_target_state() -> None:
    benchmark = grover.build_benchmark(n_qubits=3, marked_state="101")
    assert benchmark.metadata["target_state"] == "101"


def test_grover_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="at least 2 qubits"):
        grover.build_benchmark(n_qubits=1, marked_state="1")
    with pytest.raises(ValueError, match="at most 4 qubits"):
        grover.build_benchmark(n_qubits=5, marked_state="11111")
    with pytest.raises(ValueError, match="length equal to n_qubits"):
        grover.build_benchmark(n_qubits=3, marked_state="10")
    with pytest.raises(ValueError, match="iterations must be at least 1"):
        grover.build_benchmark(n_qubits=3, marked_state="101", iterations=0)


def test_hamiltonian_builder_tracks_parameters() -> None:
    benchmark = hamiltonian_sim.build_benchmark(n_qubits=2, time=1.0, trotter_steps=4)
    assert benchmark.parameters["trotter_steps"] == 4


def test_named_suite_builds_benchmark_specs() -> None:
    suite = build_suite("smoke")
    assert [benchmark.name for benchmark in suite] == ["ghz", "bernstein_vazirani", "grover"]


def test_noise_suite_preserves_base_metadata_and_parameters() -> None:
    base = ghz.build_benchmark(n_qubits=3)
    noisy = build_noise_suite(base, noise_levels=[0.0, 0.01])
    assert [benchmark.parameters["noise_level"] for benchmark in noisy] == [0.0, 0.01]
    assert noisy[1].metadata["base_circuit"] is base.circuit_data
    assert noisy[1].ideal_distribution == base.ideal_distribution
