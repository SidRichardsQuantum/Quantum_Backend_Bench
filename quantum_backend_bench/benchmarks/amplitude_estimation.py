"""Amplitude-estimation-style benchmark."""

from __future__ import annotations

import math

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(
    n_qubits: int = 3, probability: float = 0.25, iterations: int = 1
) -> BenchmarkSpec:
    """Build a small amplitude amplification workload."""

    if n_qubits < 1:
        raise ValueError("amplitude-estimation requires at least 1 qubit.")
    if probability < 0.0 or probability > 1.0:
        raise ValueError("probability must be between 0 and 1.")
    if iterations < 0:
        raise ValueError("iterations must be non-negative.")

    theta = 2.0 * math.asin(math.sqrt(probability))
    operations = [CircuitOperation("RY", (0,), {"theta": theta})]
    for _ in range(iterations):
        operations.extend(
            [
                CircuitOperation("Z", (0,)),
                CircuitOperation("RY", (0,), {"theta": -theta}),
                CircuitOperation("Z", (0,)),
                CircuitOperation("RY", (0,), {"theta": theta}),
            ]
        )
    for qubit in range(1, n_qubits):
        operations.append(CircuitOperation("H", (qubit,)))

    return BenchmarkSpec(
        name="amplitude_estimation",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "probability": probability, "iterations": iterations},
        circuit_data=InternalCircuit(n_qubits, operations, list(range(n_qubits))),
        metadata={
            "family": "estimation",
            "algorithm": "amplitude_estimation",
            "target_state": "1" + "0" * (n_qubits - 1),
        },
    )
