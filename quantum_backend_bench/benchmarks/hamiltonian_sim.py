"""Simple Ising-style Hamiltonian simulation benchmark."""

from __future__ import annotations

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 2, time: float = 0.5, trotter_steps: int = 1) -> BenchmarkSpec:
    """Build a first-order Trotterized Ising evolution circuit.

    Hamiltonian:
    H = sum_i Z_i Z_{i+1} + 0.5 * sum_i X_i
    """

    delta_t = time / trotter_steps
    operations: list[CircuitOperation] = []
    for _ in range(trotter_steps):
        for qubit in range(n_qubits - 1):
            operations.append(CircuitOperation("CNOT", (qubit, qubit + 1)))
            operations.append(CircuitOperation("RZ", (qubit + 1,), {"theta": 2.0 * delta_t}))
            operations.append(CircuitOperation("CNOT", (qubit, qubit + 1)))
        for qubit in range(n_qubits):
            operations.append(CircuitOperation("RX", (qubit,), {"theta": delta_t}))

    return BenchmarkSpec(
        name="hamiltonian_sim",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "time": time, "trotter_steps": trotter_steps},
        circuit_data=InternalCircuit(
            n_qubits=n_qubits, operations=operations, measurements=list(range(n_qubits))
        ),
        metadata={
            "family": "simulation",
            "hamiltonian": "H = sum_i Z_i Z_{i+1} + 0.5 * sum_i X_i",
        },
    )
