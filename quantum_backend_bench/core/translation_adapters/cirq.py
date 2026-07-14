"""Cirq circuit translation adapter."""

from __future__ import annotations

import ast

from quantum_backend_bench.core.benchmark_spec import CircuitOperation, InternalCircuit
from quantum_backend_bench.core.circuit_translate import TranslationDiagnostic


class CirqCircuitAdapter:
    """Adapter hooks for static Cirq circuit snippets and Cirq output."""

    input_format = "cirq"
    output_format = "cirq"

    def parse_ast(self, tree: ast.AST) -> InternalCircuit:
        from quantum_backend_bench.core import circuit_translate as circuit_translation

        return circuit_translation._parse_cirq_ast(tree)

    def emit(
        self,
        circuit: InternalCircuit,
        *,
        include_runner: bool = False,
        runner_shots: int = 1024,
    ) -> str:
        lines = [
            "import cirq",
            "",
            f"qubits = cirq.LineQubit.range({circuit.n_qubits})",
            "circuit = cirq.Circuit()",
        ]
        for operation in circuit.operations:
            for expression in _cirq_exprs(operation):
                lines.append(f"circuit.append({expression})")
        lines.extend(_cirq_noise_lines(circuit))
        if circuit.measurements:
            qubits = ", ".join(f"qubits[{qubit}]" for qubit in circuit.measurements)
            lines.append(f'circuit.append(cirq.measure({qubits}, key="m"))')
        if include_runner:
            lines.extend(_cirq_runner_lines(runner_shots))
        return "\n".join(lines) + "\n"

    def capabilities(self) -> dict[str, object]:
        return {
            "sdk": self.output_format,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "import_hook": "static cirq.Circuit AST",
            "emit_hook": "cirq.Circuit source",
            "diagnostic_hooks": ["measurement-key caveats", "provider/runtime calls"],
        }

    def diagnostics(self) -> list[TranslationDiagnostic]:
        return []


def _cirq_exprs(operation: CircuitOperation) -> list[str]:
    gate = operation.gate
    q = operation.qubits
    if gate in {"H", "X", "Y", "Z", "S", "T"}:
        return [f"cirq.{gate}(qubits[{q[0]}])"]
    if gate == "SX":
        return [f"cirq.XPowGate(exponent=0.5)(qubits[{q[0]}])"]
    if gate in {"P", "PHASE"}:
        return [
            f"cirq.ZPowGate(exponent={_format_number(operation.params['theta'])} / 3.141592653589793)(qubits[{q[0]}])"
        ]
    if gate in {"RX", "RY", "RZ"}:
        return [f"cirq.{gate.lower()}({_format_number(operation.params['theta'])})(qubits[{q[0]}])"]
    if gate == "U":
        return [
            f"cirq.rz({_format_number(operation.params['phi'])})(qubits[{q[0]}])",
            f"cirq.ry({_format_number(operation.params['theta'])})(qubits[{q[0]}])",
            f"cirq.rz({_format_number(operation.params['lambda'])})(qubits[{q[0]}])",
        ]
    if gate in {"CNOT", "CZ", "SWAP"}:
        return [f"cirq.{gate}(qubits[{q[0]}], qubits[{q[1]}])"]
    if gate == "CCX":
        return [f"cirq.TOFFOLI(qubits[{q[0]}], qubits[{q[1]}], qubits[{q[2]}])"]
    if gate in {"CRX", "CRY", "CRZ"}:
        axis = gate[-1].lower()
        return [
            f"cirq.ControlledGate(cirq.r{axis}({_format_number(operation.params['theta'])}))(qubits[{q[0]}], qubits[{q[1]}])"
        ]
    if gate == "CPHASE":
        return [
            "cirq.CZPowGate(exponent="
            f"{_format_number(operation.params['theta'])} / 3.141592653589793)"
            f"(qubits[{q[0]}], qubits[{q[1]}])"
        ]
    raise ValueError(f"Unsupported Cirq emit gate: {gate}")


def _cirq_noise_lines(circuit: InternalCircuit) -> list[str]:
    channel_map = {
        "depolarizing": "depolarize",
        "bit_flip": "bit_flip",
        "phase_flip": "phase_flip",
        "amplitude_damping": "amplitude_damp",
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
            lines.append(
                f"circuit.append(cirq.{channel}({_format_number(item.probability)})(qubits[{target}]))"
            )
    return lines


def _cirq_runner_lines(shots: int) -> list[str]:
    return [
        "",
        'if __name__ == "__main__":',
        "    simulator = cirq.Simulator()",
        f"    result = simulator.run(circuit, repetitions={shots})",
        "    counts = result.histogram(key=\"m\", fold_func=lambda bits: ''.join(str(int(bit)) for bit in bits))",
        "    print(dict(sorted(counts.items())))",
    ]


def _format_number(value: object) -> str:
    if not isinstance(value, int | float):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")
    return repr(float(value))
