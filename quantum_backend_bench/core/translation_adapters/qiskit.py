"""Qiskit Aer circuit translation adapter."""

from __future__ import annotations

import ast

from quantum_backend_bench.core.benchmark_spec import CircuitOperation, InternalCircuit
from quantum_backend_bench.core.circuit_translate import TranslationDiagnostic


class QiskitCircuitAdapter:
    """Adapter hooks for static Qiskit circuit snippets and Qiskit Aer output."""

    input_format = "qiskit"
    output_format = "qiskit_aer"

    def parse_ast(self, tree: ast.AST) -> InternalCircuit:
        from quantum_backend_bench.core import circuit_translate as circuit_translation

        return circuit_translation._parse_qiskit_ast(tree)

    def emit(
        self,
        circuit: InternalCircuit,
        *,
        include_runner: bool = False,
        runner_shots: int = 1024,
    ) -> str:
        lines = [
            "from qiskit import QuantumCircuit",
            "",
            f"circuit = QuantumCircuit({circuit.n_qubits}, {len(circuit.measurements)})",
        ]
        for operation in circuit.operations:
            lines.append(_qiskit_line(operation))
        for classical_index, qubit in enumerate(circuit.measurements):
            lines.append(
                f"circuit.measure({qubit}, {len(circuit.measurements) - classical_index - 1})"
            )
        if include_runner:
            lines.extend(_qiskit_runner_lines(runner_shots))
        return "\n".join(lines) + "\n"

    def capabilities(self) -> dict[str, object]:
        return {
            "sdk": self.output_format,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "import_hook": "static QuantumCircuit AST",
            "emit_hook": "QuantumCircuit source",
            "diagnostic_hooks": ["custom/composed gates", "provider/runtime calls"],
        }

    def diagnostics(self) -> list[TranslationDiagnostic]:
        return []


def _qiskit_line(operation: CircuitOperation) -> str:
    gate = operation.gate
    q = operation.qubits
    if gate in {"H", "X", "Y", "Z", "S", "T"}:
        return f"circuit.{gate.lower()}({q[0]})"
    if gate in {"RX", "RY", "RZ"}:
        return f"circuit.{gate.lower()}({_format_number(operation.params['theta'])}, {q[0]})"
    if gate == "CNOT":
        return f"circuit.cx({q[0]}, {q[1]})"
    if gate == "CZ":
        return f"circuit.cz({q[0]}, {q[1]})"
    if gate == "SWAP":
        return f"circuit.swap({q[0]}, {q[1]})"
    if gate == "CPHASE":
        return f"circuit.cp({_format_number(operation.params['theta'])}, {q[0]}, {q[1]})"
    raise ValueError(f"Unsupported Qiskit emit gate: {gate}")


def _qiskit_runner_lines(shots: int) -> list[str]:
    return [
        "",
        'if __name__ == "__main__":',
        "    from qiskit import transpile",
        "    from qiskit_aer import AerSimulator",
        "",
        "    simulator = AerSimulator()",
        "    compiled = transpile(circuit, simulator)",
        f"    result = simulator.run(compiled, shots={shots}).result()",
        "    print(result.get_counts(compiled))",
    ]


def _format_number(value: object) -> str:
    if not isinstance(value, int | float):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")
    return repr(float(value))
