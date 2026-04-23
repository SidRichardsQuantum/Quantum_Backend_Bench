"""Random circuit benchmark."""

from __future__ import annotations

import math
import random

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)

SINGLE_QUBIT_GATES = ("H", "X", "Y", "Z", "RX", "RY", "RZ")
TWO_QUBIT_GATES = ("CNOT", "CZ")


def build_benchmark(n_qubits: int = 4, depth: int = 10, seed: int = 42) -> BenchmarkSpec:
    """Build a reproducible random circuit benchmark."""

    rng = random.Random(seed)
    operations: list[CircuitOperation] = []
    for _ in range(depth):
        if rng.random() < 0.65:
            gate = rng.choice(SINGLE_QUBIT_GATES)
            qubit = rng.randrange(n_qubits)
            params = (
                {"theta": rng.uniform(0.0, 2.0 * math.pi)} if gate in {"RX", "RY", "RZ"} else {}
            )
            operations.append(CircuitOperation(gate, (qubit,), params))
        else:
            control, target = rng.sample(range(n_qubits), 2)
            gate = rng.choice(TWO_QUBIT_GATES)
            operations.append(CircuitOperation(gate, (control, target)))

    return BenchmarkSpec(
        name="random_circuit",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "depth": depth, "seed": seed},
        circuit_data=InternalCircuit(
            n_qubits=n_qubits, operations=operations, measurements=list(range(n_qubits))
        ),
        metadata={"family": "synthetic"},
    )
