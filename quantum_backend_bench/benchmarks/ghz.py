"""GHZ benchmark."""

from __future__ import annotations

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 3) -> BenchmarkSpec:
    """Build a GHZ state preparation benchmark."""

    operations = [CircuitOperation("H", (0,))]
    for index in range(n_qubits - 1):
        operations.append(CircuitOperation("CNOT", (index, index + 1)))
    return BenchmarkSpec(
        name="ghz",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits},
        circuit_data=InternalCircuit(
            n_qubits=n_qubits,
            operations=operations,
            measurements=list(range(n_qubits)),
        ),
        ideal_distribution={
            "0" * n_qubits: 0.5,
            "1" * n_qubits: 0.5,
        },
        metadata={"family": "entanglement"},
    )
