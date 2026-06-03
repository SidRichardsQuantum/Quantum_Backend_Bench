"""Compact phase-estimation-style benchmark."""

from __future__ import annotations

import math

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 4, phase: float = 0.25) -> BenchmarkSpec:
    """Build a small phase-kickback workload with inverse-QFT-like structure."""

    if n_qubits < 2:
        raise ValueError("phase-estimation requires at least 2 qubits.")
    controls = n_qubits - 1
    target = n_qubits - 1
    operations: list[CircuitOperation] = [CircuitOperation("X", (target,))]
    for qubit in range(controls):
        operations.append(CircuitOperation("H", (qubit,)))
        operations.append(
            CircuitOperation("CPHASE", (qubit, target), {"theta": 2 * math.pi * phase * 2**qubit})
        )
    for left in reversed(range(controls)):
        for right in reversed(range(left + 1, controls)):
            operations.append(
                CircuitOperation("CPHASE", (right, left), {"theta": -math.pi / 2 ** (right - left)})
            )
        operations.append(CircuitOperation("H", (left,)))

    return BenchmarkSpec(
        name="phase_estimation",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "phase": phase},
        circuit_data=InternalCircuit(n_qubits, operations, list(range(controls))),
        metadata={"family": "estimation", "algorithm": "phase_estimation"},
    )
