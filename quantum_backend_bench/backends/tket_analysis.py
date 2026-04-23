"""pytket-based circuit analysis."""

from __future__ import annotations

from collections import Counter
from typing import Any

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def analyze_with_tket(benchmark: BenchmarkSpec) -> dict[str, Any]:
    """Analyze a benchmark circuit with pytket when available."""

    circuit = benchmark.circuit_data
    if not isinstance(circuit, InternalCircuit):
        return {
            "depth": None,
            "gate_count": None,
            "two_qubit_gate_count": None,
            "gate_histogram": None,
        }

    try:
        from pytket import Circuit
    except ImportError:
        gate_histogram = Counter(operation.gate for operation in circuit.operations)
        return {
            "depth": _naive_depth(circuit.operations),
            "gate_count": len(circuit.operations),
            "two_qubit_gate_count": sum(1 for op in circuit.operations if len(op.qubits) == 2),
            "gate_histogram": dict(gate_histogram),
            "compiled": False,
            "compiler_summary": "pytket not installed; using internal structural estimates.",
        }

    tk_circuit = Circuit(circuit.n_qubits, circuit.n_qubits)
    for operation in circuit.operations:
        _apply_tket_op(tk_circuit, operation)
    for qubit in circuit.measurements:
        tk_circuit.Measure(qubit, qubit)

    commands = tk_circuit.get_commands()
    gate_histogram = Counter(
        str(command.op.type) for command in commands if str(command.op.type) != "OpType.Measure"
    )
    return {
        "depth": tk_circuit.depth(),
        "gate_count": len(circuit.operations),
        "two_qubit_gate_count": sum(1 for op in circuit.operations if len(op.qubits) == 2),
        "gate_histogram": dict(gate_histogram),
        "compiled": False,
        "compiler_summary": "Raw circuit analyzed with pytket; no execution backend used.",
    }


def _apply_tket_op(circuit: Any, operation: CircuitOperation) -> None:
    gate = operation.gate
    q = operation.qubits
    params = operation.params

    if gate == "H":
        circuit.H(q[0])
    elif gate == "X":
        circuit.X(q[0])
    elif gate == "Y":
        circuit.Y(q[0])
    elif gate == "Z":
        circuit.Z(q[0])
    elif gate == "S":
        circuit.S(q[0])
    elif gate == "T":
        circuit.T(q[0])
    elif gate == "RX":
        circuit.Rx(params["theta"] / 3.141592653589793, q[0])
    elif gate == "RY":
        circuit.Ry(params["theta"] / 3.141592653589793, q[0])
    elif gate == "RZ":
        circuit.Rz(params["theta"] / 3.141592653589793, q[0])
    elif gate == "CNOT":
        circuit.CX(q[0], q[1])
    elif gate == "CZ":
        circuit.CZ(q[0], q[1])
    elif gate == "SWAP":
        circuit.SWAP(q[0], q[1])
    elif gate == "CPHASE":
        circuit.CRz(params["theta"] / 3.141592653589793, q[0], q[1])
    else:
        raise ValueError(f"Unsupported operation for pytket analysis: {gate}")


def _naive_depth(operations: list[CircuitOperation]) -> int:
    if not operations:
        return 0
    moments: list[set[int]] = []
    for operation in operations:
        qubits = set(operation.qubits)
        for moment in moments:
            if moment.isdisjoint(qubits):
                moment.update(qubits)
                break
        else:
            moments.append(set(qubits))
    return len(moments)
