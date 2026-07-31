"""Canonical serialization helpers for the neutral circuit schema."""

from __future__ import annotations

import json
from typing import Any

from quantum_backend_bench.core.benchmark_spec import (
    CircuitOperation,
    InternalCircuit,
    NoiseInstruction,
)
from quantum_backend_bench.core.neutral_schema import NEUTRAL_SCHEMA_VERSION


def internal_circuit_to_payload(circuit: InternalCircuit) -> dict[str, object]:
    """Convert a neutral circuit to its schema-conformant payload."""

    return {
        "schema_version": NEUTRAL_SCHEMA_VERSION,
        "n_qubits": circuit.n_qubits,
        "operations": [
            {"gate": operation.gate, "qubits": list(operation.qubits), "params": operation.params}
            for operation in circuit.operations
        ],
        "measurements": circuit.measurements,
        "quantum_registers": circuit.quantum_registers,
        "classical_registers": circuit.classical_registers,
        "measurement_keys": circuit.measurement_keys,
        "bit_order": circuit.bit_order,
        "global_phase": circuit.global_phase,
        "noise": [
            {
                "channel": instruction.channel,
                "targets": list(instruction.targets),
                "probability": instruction.probability,
            }
            for instruction in circuit.noise
        ],
    }


def internal_circuit_to_json(circuit: InternalCircuit) -> str:
    """Serialize a neutral circuit using the canonical JSON representation."""

    return json.dumps(internal_circuit_to_payload(circuit), indent=2, sort_keys=True) + "\n"


def internal_circuit_from_json(source: str) -> InternalCircuit:
    """Parse the canonical neutral circuit JSON representation."""

    payload = json.loads(source)
    n_qubits = int(payload["n_qubits"])
    operations = [
        CircuitOperation(
            str(item["gate"]).upper(),
            tuple(int(qubit) for qubit in item["qubits"]),
            dict(item.get("params", {})),
        )
        for item in payload.get("operations", [])
    ]
    measurements = [int(qubit) for qubit in payload.get("measurements", [])]
    noise = [
        NoiseInstruction(
            str(item["channel"]).lower(),
            tuple(int(target) for target in item.get("targets", range(n_qubits))),
            float(item.get("probability", item.get("p", 0.0))),
        )
        for item in payload.get("noise", [])
    ]
    return InternalCircuit(
        n_qubits,
        operations,
        measurements or list(range(n_qubits)),
        quantum_registers=_register_payload(payload.get("quantum_registers")),
        classical_registers=_register_payload(payload.get("classical_registers")),
        measurement_keys={
            str(key): str(value) for key, value in payload.get("measurement_keys", {}).items()
        },
        bit_order=str(payload.get("bit_order", "measurement-list")),
        global_phase=float(payload.get("global_phase", 0.0)),
        noise=noise,
    )


def _register_payload(payload: Any) -> dict[str, list[int]]:
    if not isinstance(payload, dict):
        return {}
    return {str(key): [int(item) for item in value] for key, value in payload.items()}
