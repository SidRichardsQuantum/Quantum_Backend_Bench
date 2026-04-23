"""Experiment presets for repeated benchmark sweeps."""

from __future__ import annotations

from quantum_backend_bench.benchmarks import ghz, grover, hamiltonian_sim, qft, random_circuit
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec


def default_suite() -> list[BenchmarkSpec]:
    """Return a small reproducible default benchmark suite."""

    return [
        ghz.build_benchmark(n_qubits=3),
        qft.build_benchmark(n_qubits=5),
        random_circuit.build_benchmark(n_qubits=4, depth=10, seed=42),
        grover.build_benchmark(n_qubits=3, marked_state="101"),
        hamiltonian_sim.build_benchmark(n_qubits=2, time=0.5, trotter_steps=2),
    ]
