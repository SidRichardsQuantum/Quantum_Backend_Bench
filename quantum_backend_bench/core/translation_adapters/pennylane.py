"""PennyLane circuit translation adapter."""

from __future__ import annotations

import ast

from quantum_backend_bench.core.benchmark_spec import CircuitOperation, InternalCircuit
from quantum_backend_bench.core.circuit_translate import TranslationDiagnostic


class PennyLaneCircuitAdapter:
    """Adapter hooks for static PennyLane snippets and PennyLane output."""

    input_format = "pennylane"
    output_format = "pennylane"

    def parse_ast(self, tree: ast.AST) -> InternalCircuit:
        from quantum_backend_bench.core import circuit_translate as circuit_translation

        return circuit_translation._parse_pennylane_ast(tree)

    def emit(
        self,
        circuit: InternalCircuit,
        *,
        include_runner: bool = False,
        runner_shots: int = 1024,
    ) -> str:
        lines = [
            "import pennylane as qml",
            "",
            f'dev = qml.device("default.qubit", wires={circuit.n_qubits})',
            "",
            "",
            "@qml.qnode(dev)",
            "def circuit():",
        ]
        for operation in circuit.operations:
            for line in _pennylane_lines(operation):
                lines.append(f"    {line}")
        for line in _pennylane_noise_lines(circuit):
            lines.append(f"    {line}")
        measurements = ", ".join(str(qubit) for qubit in circuit.measurements)
        lines.append(f"    return qml.sample(wires=[{measurements}])")
        if include_runner:
            lines.extend(_pennylane_runner_lines(runner_shots))
        return "\n".join(lines) + "\n"

    def capabilities(self) -> dict[str, object]:
        return {
            "sdk": self.output_format,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "import_hook": "static QNode-style AST",
            "emit_hook": "PennyLane QNode source",
            "diagnostic_hooks": ["sampling caveats", "provider/runtime calls"],
        }

    def diagnostics(self) -> list[TranslationDiagnostic]:
        return [
            TranslationDiagnostic(
                "warning",
                "translation.caveat.pennylane_sampling",
                "PennyLane output is a QNode returning qml.sample; runner output wraps it with qml.set_shots.",
            )
        ]


def _pennylane_lines(operation: CircuitOperation) -> list[str]:
    gate = operation.gate
    q = operation.qubits
    one_qubit = {
        "H": "Hadamard",
        "X": "PauliX",
        "Y": "PauliY",
        "Z": "PauliZ",
        "S": "S",
        "T": "T",
    }
    if gate in one_qubit:
        return [f"qml.{one_qubit[gate]}(wires={q[0]})"]
    if gate == "SX":
        return [f"qml.SX(wires={q[0]})"]
    if gate in {"P", "PHASE"}:
        return [f"qml.PhaseShift({_format_number(operation.params['theta'])}, wires={q[0]})"]
    if gate in {"RX", "RY", "RZ"}:
        return [f"qml.{gate}({_format_number(operation.params['theta'])}, wires={q[0]})"]
    if gate == "U":
        return [
            "qml.U3("
            f"{_format_number(operation.params['theta'])}, "
            f"{_format_number(operation.params['phi'])}, "
            f"{_format_number(operation.params['lambda'])}, wires={q[0]})"
        ]
    if gate in {"CNOT", "CZ", "SWAP"}:
        return [f"qml.{gate}(wires=[{q[0]}, {q[1]}])"]
    if gate == "CCX":
        return [f"qml.Toffoli(wires=[{q[0]}, {q[1]}, {q[2]}])"]
    if gate in {"CRX", "CRY", "CRZ"}:
        return [f"qml.{gate}({_format_number(operation.params['theta'])}, wires=[{q[0]}, {q[1]}])"]
    if gate == "CPHASE":
        return [
            f"qml.ControlledPhaseShift({_format_number(operation.params['theta'])}, wires=[{q[0]}, {q[1]}])"
        ]
    raise ValueError(f"Unsupported PennyLane emit gate: {gate}")


def _pennylane_noise_lines(circuit: InternalCircuit) -> list[str]:
    channel_map = {
        "depolarizing": "DepolarizingChannel",
        "bit_flip": "BitFlip",
        "phase_flip": "PhaseFlip",
        "amplitude_damping": "AmplitudeDamping",
    }
    lines = []
    for item in circuit.noise:
        channel = channel_map.get(item.channel)
        if channel is None:
            lines.append(
                f"# neutral_noise channel={item.channel} targets={list(item.targets)!r} probability={item.probability!r}"
            )
            continue
        for target in item.targets:
            lines.append(f"qml.{channel}({_format_number(item.probability)}, wires={target})")
    return lines


def _pennylane_runner_lines(shots: int) -> list[str]:
    return [
        "",
        'if __name__ == "__main__":',
        "    from collections import Counter",
        "",
        f"    samples = qml.set_shots(circuit, shots={shots})()",
        "    counts = Counter(''.join(str(int(bit)) for bit in row) for row in samples)",
        "    print(dict(sorted(counts.items())))",
    ]


def _format_number(value: object) -> str:
    if not isinstance(value, int | float):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")
    return repr(float(value))
