"""Small VQE-style ansatz benchmark."""

from __future__ import annotations

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 4, depth: int = 2, theta: float = 0.3) -> BenchmarkSpec:
    """Build a hardware-efficient ansatz often used in VQE examples."""

    if n_qubits < 2:
        raise ValueError("vqe-ansatz requires at least 2 qubits.")
    if depth < 1:
        raise ValueError("depth must be at least 1.")

    operations: list[CircuitOperation] = []
    for layer in range(depth):
        angle = theta * (layer + 1)
        for qubit in range(n_qubits):
            operations.append(CircuitOperation("RY", (qubit,), {"theta": angle}))
            operations.append(CircuitOperation("RZ", (qubit,), {"theta": angle / 2.0}))
        for qubit in range(n_qubits - 1):
            operations.append(CircuitOperation("CNOT", (qubit, qubit + 1)))

    return BenchmarkSpec(
        name="vqe_ansatz",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "depth": depth, "theta": theta},
        circuit_data=InternalCircuit(n_qubits, operations, list(range(n_qubits))),
        metadata={"family": "chemistry", "algorithm": "vqe", "observable": "toy_ising"},
    )
