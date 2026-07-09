"""Circuit export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantum_backend_bench.backends import get_backend
from quantum_backend_bench.core.neutral_schema import NEUTRAL_SCHEMA_VERSION
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)

EXPORT_FORMATS = ("internal-json", "openqasm", "openqasm2", "openqasm3", "native")


def export_benchmark_circuit(
    benchmark: BenchmarkSpec,
    export_format: str,
    backend: str | None = None,
    save_path: str | Path | None = None,
) -> str:
    """Export a benchmark circuit as text."""

    if export_format == "internal-json":
        output = _internal_json(benchmark)
    elif export_format in {"openqasm", "openqasm2"}:
        output = _openqasm2(benchmark)
    elif export_format == "openqasm3":
        output = _openqasm3(benchmark)
    elif export_format == "native":
        if backend is None:
            raise ValueError("native export requires a backend.")
        output = str(get_backend(backend).build_native_circuit(benchmark))
    else:
        available = ", ".join(EXPORT_FORMATS)
        raise ValueError(f"Unknown export format '{export_format}'. Available: {available}")

    if save_path:
        Path(save_path).write_text(output, encoding="utf-8")
    return output


def _internal_json(benchmark: BenchmarkSpec) -> str:
    circuit = _internal_circuit(benchmark)
    payload: dict[str, Any] = {
        "schema_version": NEUTRAL_SCHEMA_VERSION,
        "benchmark": benchmark.name,
        "n_qubits": benchmark.n_qubits,
        "parameters": benchmark.parameters,
        "operations": [
            {"gate": op.gate, "qubits": list(op.qubits), "params": op.params}
            for op in circuit.operations
        ],
        "measurements": circuit.measurements,
        "metadata": {
            key: value for key, value in (benchmark.metadata or {}).items() if key != "base_circuit"
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _openqasm2(benchmark: BenchmarkSpec) -> str:
    circuit = _internal_circuit(benchmark)
    measurements = circuit.measurements or list(range(circuit.n_qubits))
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{circuit.n_qubits}];",
        f"creg c[{len(measurements)}];",
    ]
    for operation in circuit.operations:
        lines.append(_operation_to_qasm(operation.gate, operation.qubits, operation.params))
    for classical_index, qubit in enumerate(measurements):
        lines.append(f"measure q[{qubit}] -> c[{classical_index}];")
    return "\n".join(lines) + "\n"


def _openqasm3(benchmark: BenchmarkSpec) -> str:
    circuit = _internal_circuit(benchmark)
    measurements = circuit.measurements or list(range(circuit.n_qubits))
    lines = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"qubit[{circuit.n_qubits}] q;",
        f"bit[{len(measurements)}] c;",
    ]
    for operation in circuit.operations:
        lines.append(_operation_to_qasm3(operation.gate, operation.qubits, operation.params))
    for classical_index, qubit in enumerate(measurements):
        lines.append(f"c[{classical_index}] = measure q[{qubit}];")
    return "\n".join(lines) + "\n"


def import_openqasm_circuit(source: str, *, name: str = "imported_openqasm") -> BenchmarkSpec:
    """Import a small OpenQASM 2/3 subset emitted by this project."""

    lines = [line.strip() for line in source.splitlines() if line.strip()]
    n_qubits = None
    measurements: list[int] = []
    operations: list[CircuitOperation] = []
    for line in lines:
        if line.startswith(("OPENQASM", "include")):
            continue
        if line.startswith("qreg q["):
            n_qubits = int(line.split("[", 1)[1].split("]", 1)[0])
            continue
        if line.startswith("qubit["):
            n_qubits = int(line.split("[", 1)[1].split("]", 1)[0])
            continue
        if line.startswith(("creg", "bit[")):
            continue
        if line.startswith("measure q["):
            measurements.append(int(line.split("[", 1)[1].split("]", 1)[0]))
            continue
        if "= measure q[" in line:
            measurements.append(int(line.rsplit("q[", 1)[1].split("]", 1)[0]))
            continue
        operations.append(_qasm_operation(line))
    if n_qubits is None:
        raise ValueError("OpenQASM input does not declare qreg/qubit q.")
    return BenchmarkSpec(
        name=name,
        n_qubits=n_qubits,
        parameters={"source": "openqasm"},
        circuit_data=InternalCircuit(n_qubits, operations, measurements or list(range(n_qubits))),
        metadata={"family": "imported", "format": "openqasm"},
    )


def _qasm_operation(line: str) -> CircuitOperation:
    line = line.rstrip(";")
    if " " not in line:
        raise ValueError(f"Unsupported OpenQASM statement: {line}")
    gate_token, qubit_token = line.split(" ", 1)
    params: dict[str, Any] = {}
    gate = gate_token
    if "(" in gate_token:
        gate, raw_param = gate_token.split("(", 1)
        params["theta"] = float(raw_param.rstrip(")"))
    qubits = tuple(int(part.split("[", 1)[1].split("]", 1)[0]) for part in qubit_token.split(","))
    mapping = {
        "h": "H",
        "x": "X",
        "y": "Y",
        "z": "Z",
        "s": "S",
        "t": "T",
        "rx": "RX",
        "ry": "RY",
        "rz": "RZ",
        "cx": "CNOT",
        "cz": "CZ",
        "swap": "SWAP",
        "cu1": "CPHASE",
        "cp": "CPHASE",
    }
    if gate not in mapping:
        raise ValueError(f"Unsupported OpenQASM gate: {gate}")
    return CircuitOperation(mapping[gate], qubits, params)


def _operation_to_qasm(gate: str, qubits: tuple[int, ...], params: dict[str, Any]) -> str:
    if gate in {"H", "X", "Y", "Z", "S", "T"}:
        return f"{gate.lower()} q[{qubits[0]}];"
    if gate in {"RX", "RY", "RZ"}:
        return f"{gate.lower()}({params['theta']}) q[{qubits[0]}];"
    if gate == "CNOT":
        return f"cx q[{qubits[0]}],q[{qubits[1]}];"
    if gate == "CZ":
        return f"cz q[{qubits[0]}],q[{qubits[1]}];"
    if gate == "SWAP":
        return f"swap q[{qubits[0]}],q[{qubits[1]}];"
    if gate == "CPHASE":
        return f"cu1({params['theta']}) q[{qubits[0]}],q[{qubits[1]}];"
    raise ValueError(f"Unsupported OpenQASM gate: {gate}")


def _operation_to_qasm3(gate: str, qubits: tuple[int, ...], params: dict[str, Any]) -> str:
    if gate in {"H", "X", "Y", "Z", "S", "T"}:
        return f"{gate.lower()} q[{qubits[0]}];"
    if gate in {"RX", "RY", "RZ"}:
        return f"{gate.lower()}({params['theta']}) q[{qubits[0]}];"
    if gate == "CNOT":
        return f"cx q[{qubits[0]}], q[{qubits[1]}];"
    if gate == "CZ":
        return f"cz q[{qubits[0]}], q[{qubits[1]}];"
    if gate == "SWAP":
        return f"swap q[{qubits[0]}], q[{qubits[1]}];"
    if gate == "CPHASE":
        return f"cp({params['theta']}) q[{qubits[0]}], q[{qubits[1]}];"
    raise ValueError(f"Unsupported OpenQASM gate: {gate}")


def _internal_circuit(benchmark: BenchmarkSpec) -> InternalCircuit:
    circuit_data = (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)
    if not isinstance(circuit_data, InternalCircuit):
        raise TypeError("Circuit export requires an InternalCircuit benchmark.")
    return circuit_data
