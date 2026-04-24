"""Deutsch-Jozsa oracle benchmark."""

from __future__ import annotations

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(
    n_qubits: int = 4,
    oracle_type: str = "balanced",
    bitmask: str | None = None,
    constant_value: int = 0,
) -> BenchmarkSpec:
    """Build a Deutsch-Jozsa circuit for a constant or linear balanced oracle.

    ``n_qubits`` is the total circuit width. The final qubit is the oracle work qubit,
    so the input register has length ``n_qubits - 1``.
    """

    if n_qubits < 2:
        raise ValueError("Deutsch-Jozsa requires at least 2 total qubits.")
    if oracle_type not in {"balanced", "constant"}:
        raise ValueError("oracle_type must be 'balanced' or 'constant'.")
    if constant_value not in {0, 1}:
        raise ValueError("constant_value must be 0 or 1.")

    data_qubits = n_qubits - 1
    mask = bitmask or ("1" + ("0" * (data_qubits - 1)))
    if len(mask) != data_qubits:
        raise ValueError(
            "bitmask must have length n_qubits - 1 "
            f"({data_qubits} for n_qubits={n_qubits}); got length {len(mask)}."
        )
    if any(bit not in {"0", "1"} for bit in mask):
        raise ValueError("bitmask must contain only 0 and 1 characters.")
    if oracle_type == "balanced" and "1" not in mask:
        raise ValueError("balanced Deutsch-Jozsa bitmask must contain at least one 1.")

    work_qubit = n_qubits - 1
    operations = [CircuitOperation("X", (work_qubit,)), CircuitOperation("H", (work_qubit,))]
    operations.extend(CircuitOperation("H", (qubit,)) for qubit in range(data_qubits))

    if oracle_type == "constant":
        if constant_value == 1:
            operations.append(CircuitOperation("X", (work_qubit,)))
        target_state = "0" * data_qubits
    else:
        for qubit, bit in enumerate(mask):
            if bit == "1":
                operations.append(CircuitOperation("CNOT", (qubit, work_qubit)))
        target_state = mask

    operations.extend(CircuitOperation("H", (qubit,)) for qubit in range(data_qubits))

    return BenchmarkSpec(
        name="deutsch_jozsa",
        n_qubits=n_qubits,
        parameters={
            "n_qubits": n_qubits,
            "oracle_type": oracle_type,
            "bitmask": mask,
            "constant_value": constant_value,
        },
        circuit_data=InternalCircuit(
            n_qubits=n_qubits,
            operations=operations,
            measurements=list(range(data_qubits)),
        ),
        ideal_distribution={target_state: 1.0},
        metadata={
            "family": "oracle",
            "target_state": target_state,
            "work_qubits": [work_qubit],
        },
    )
