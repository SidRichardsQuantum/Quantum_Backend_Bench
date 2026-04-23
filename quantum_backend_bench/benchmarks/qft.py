"""Quantum Fourier Transform benchmark."""

from __future__ import annotations

import math

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 3) -> BenchmarkSpec:
    """Build a QFT circuit benchmark."""

    operations: list[CircuitOperation] = []
    for target in range(n_qubits):
        operations.append(CircuitOperation("H", (target,)))
        for control in range(target + 1, n_qubits):
            angle = math.pi / (2 ** (control - target))
            operations.append(CircuitOperation("CPHASE", (control, target), {"theta": angle}))
    for index in range(n_qubits // 2):
        operations.append(CircuitOperation("SWAP", (index, n_qubits - index - 1)))

    return BenchmarkSpec(
        name="qft",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits},
        circuit_data=InternalCircuit(
            n_qubits=n_qubits, operations=operations, measurements=list(range(n_qubits))
        ),
        metadata={"family": "transform"},
    )
