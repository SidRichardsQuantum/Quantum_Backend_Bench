"""Quantum-volume-style random layered benchmark."""

from __future__ import annotations

import math
import random

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 4, depth: int | None = None, seed: int = 42) -> BenchmarkSpec:
    """Build a square, random, layered circuit inspired by quantum volume.

    This is not a formal quantum volume certification routine. It is a portable workload
    with shuffled pair layers and randomized one-qubit rotations.
    """

    if n_qubits < 2:
        raise ValueError("quantum_volume requires at least 2 qubits.")

    layers = depth if depth is not None else n_qubits
    if layers < 1:
        raise ValueError("quantum_volume depth must be at least 1.")
    rng = random.Random(seed)
    operations: list[CircuitOperation] = []

    for _ in range(layers):
        qubits = list(range(n_qubits))
        rng.shuffle(qubits)
        for left, right in zip(qubits[0::2], qubits[1::2], strict=False):
            operations.extend(
                [
                    CircuitOperation("RY", (left,), {"theta": rng.uniform(0.0, 2.0 * math.pi)}),
                    CircuitOperation("RZ", (left,), {"theta": rng.uniform(0.0, 2.0 * math.pi)}),
                    CircuitOperation("RY", (right,), {"theta": rng.uniform(0.0, 2.0 * math.pi)}),
                    CircuitOperation("RZ", (right,), {"theta": rng.uniform(0.0, 2.0 * math.pi)}),
                    CircuitOperation("CNOT", (left, right)),
                    CircuitOperation("RZ", (right,), {"theta": rng.uniform(0.0, 2.0 * math.pi)}),
                    CircuitOperation("CNOT", (left, right)),
                ]
            )

    return BenchmarkSpec(
        name="quantum_volume",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "depth": layers, "seed": seed},
        circuit_data=InternalCircuit(
            n_qubits=n_qubits,
            operations=operations,
            measurements=list(range(n_qubits)),
        ),
        metadata={"family": "synthetic", "style": "quantum_volume"},
    )
