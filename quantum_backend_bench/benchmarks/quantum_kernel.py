"""Quantum-kernel feature-map benchmark."""

from __future__ import annotations

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 4, depth: int = 2, feature_scale: float = 0.7) -> BenchmarkSpec:
    """Build a repeated feature-map circuit for kernel-method examples."""

    if n_qubits < 2:
        raise ValueError("quantum-kernel requires at least 2 qubits.")
    if depth < 1:
        raise ValueError("depth must be at least 1.")

    operations: list[CircuitOperation] = []
    for layer in range(depth):
        for qubit in range(n_qubits):
            angle = feature_scale * (qubit + 1) * (layer + 1)
            operations.append(CircuitOperation("H", (qubit,)))
            operations.append(CircuitOperation("RZ", (qubit,), {"theta": angle}))
        for qubit in range(n_qubits - 1):
            operations.append(CircuitOperation("CNOT", (qubit, qubit + 1)))
            operations.append(CircuitOperation("RZ", (qubit + 1,), {"theta": feature_scale}))
            operations.append(CircuitOperation("CNOT", (qubit, qubit + 1)))

    return BenchmarkSpec(
        name="quantum_kernel",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "depth": depth, "feature_scale": feature_scale},
        circuit_data=InternalCircuit(n_qubits, operations, list(range(n_qubits))),
        metadata={"family": "machine_learning", "algorithm": "feature_map"},
    )
