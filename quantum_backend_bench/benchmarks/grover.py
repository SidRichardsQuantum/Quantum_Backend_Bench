"""Grover search benchmark."""

from __future__ import annotations

import math

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(
    n_qubits: int = 3, marked_state: str = "101", iterations: int | None = None
) -> BenchmarkSpec:
    """Build a small Grover search circuit."""

    if len(marked_state) != n_qubits or any(bit not in {"0", "1"} for bit in marked_state):
        raise ValueError("marked_state must be a bitstring with length equal to n_qubits.")

    total_states = 2**n_qubits
    suggested_iterations = max(1, round((math.pi / 4.0) * math.sqrt(total_states)))
    rounds = iterations if iterations is not None else min(2, suggested_iterations)

    operations = [CircuitOperation("H", (qubit,)) for qubit in range(n_qubits)]
    for _ in range(rounds):
        operations.extend(_oracle(marked_state))
        operations.extend(_diffuser(n_qubits))

    return BenchmarkSpec(
        name="grover",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "marked_state": marked_state, "iterations": rounds},
        circuit_data=InternalCircuit(
            n_qubits=n_qubits, operations=operations, measurements=list(range(n_qubits))
        ),
        metadata={"family": "search", "target_state": marked_state},
    )


def _oracle(marked_state: str) -> list[CircuitOperation]:
    operations: list[CircuitOperation] = []
    for qubit, bit in enumerate(marked_state):
        if bit == "0":
            operations.append(CircuitOperation("X", (qubit,)))
    if len(marked_state) == 2:
        operations.append(CircuitOperation("CZ", (0, 1)))
    else:
        operations.append(CircuitOperation("H", (len(marked_state) - 1,)))
        for qubit in range(len(marked_state) - 1):
            operations.append(CircuitOperation("CNOT", (qubit, len(marked_state) - 1)))
        operations.append(CircuitOperation("Z", (len(marked_state) - 1,)))
        for qubit in reversed(range(len(marked_state) - 1)):
            operations.append(CircuitOperation("CNOT", (qubit, len(marked_state) - 1)))
        operations.append(CircuitOperation("H", (len(marked_state) - 1,)))
    for qubit, bit in enumerate(marked_state):
        if bit == "0":
            operations.append(CircuitOperation("X", (qubit,)))
    return operations


def _diffuser(n_qubits: int) -> list[CircuitOperation]:
    operations: list[CircuitOperation] = []
    for qubit in range(n_qubits):
        operations.append(CircuitOperation("H", (qubit,)))
        operations.append(CircuitOperation("X", (qubit,)))
    if n_qubits == 2:
        operations.append(CircuitOperation("CZ", (0, 1)))
    else:
        operations.append(CircuitOperation("H", (n_qubits - 1,)))
        for qubit in range(n_qubits - 1):
            operations.append(CircuitOperation("CNOT", (qubit, n_qubits - 1)))
        operations.append(CircuitOperation("Z", (n_qubits - 1,)))
        for qubit in reversed(range(n_qubits - 1)):
            operations.append(CircuitOperation("CNOT", (qubit, n_qubits - 1)))
        operations.append(CircuitOperation("H", (n_qubits - 1,)))
    for qubit in range(n_qubits):
        operations.append(CircuitOperation("X", (qubit,)))
        operations.append(CircuitOperation("H", (qubit,)))
    return operations
