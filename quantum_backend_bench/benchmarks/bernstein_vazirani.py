"""Bernstein-Vazirani oracle benchmark."""

from __future__ import annotations

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(n_qubits: int = 4, secret_string: str | None = None) -> BenchmarkSpec:
    """Build a Bernstein-Vazirani circuit.

    ``n_qubits`` is the total circuit width. The final qubit is the oracle work qubit,
    so the secret string has length ``n_qubits - 1``.
    """

    if n_qubits < 2:
        raise ValueError("Bernstein-Vazirani requires at least 2 total qubits.")

    data_qubits = n_qubits - 1
    secret = secret_string or ("1" * data_qubits)
    if len(secret) != data_qubits:
        raise ValueError(
            "secret_string must have length n_qubits - 1 "
            f"({data_qubits} for n_qubits={n_qubits}); got length {len(secret)}."
        )
    if any(bit not in {"0", "1"} for bit in secret):
        raise ValueError("secret_string must contain only 0 and 1 characters.")

    work_qubit = n_qubits - 1
    operations = [CircuitOperation("X", (work_qubit,)), CircuitOperation("H", (work_qubit,))]
    operations.extend(CircuitOperation("H", (qubit,)) for qubit in range(data_qubits))
    for qubit, bit in enumerate(secret):
        if bit == "1":
            operations.append(CircuitOperation("CNOT", (qubit, work_qubit)))
    operations.extend(CircuitOperation("H", (qubit,)) for qubit in range(data_qubits))

    return BenchmarkSpec(
        name="bernstein_vazirani",
        n_qubits=n_qubits,
        parameters={"n_qubits": n_qubits, "secret_string": secret},
        circuit_data=InternalCircuit(
            n_qubits=n_qubits,
            operations=operations,
            measurements=list(range(data_qubits)),
        ),
        ideal_distribution={secret: 1.0},
        metadata={
            "family": "oracle",
            "target_state": secret,
            "work_qubits": [work_qubit],
        },
    )
