"""Amazon Braket LocalSimulator circuit translation adapter."""

from __future__ import annotations

import ast

from quantum_backend_bench.core.benchmark_spec import CircuitOperation, InternalCircuit
from quantum_backend_bench.core.circuit_translate import TranslationDiagnostic


class BraketCircuitAdapter:
    """Adapter hooks for static Braket snippets and Braket LocalSimulator output."""

    input_format = "braket"
    output_format = "braket_local"

    def parse_ast(self, tree: ast.AST) -> InternalCircuit:
        from quantum_backend_bench.core import circuit_translate as circuit_translation

        return circuit_translation._parse_braket_ast(tree)

    def emit(
        self,
        circuit: InternalCircuit,
        *,
        include_runner: bool = False,
        runner_shots: int = 1024,
    ) -> str:
        lines = [
            "from braket.circuits import Circuit, Noise",
            "",
            "circuit = Circuit()",
        ]
        for operation in circuit.operations:
            lines.extend(_braket_lines(operation))
        lines.extend(_braket_noise_lines(circuit))
        measurements = ", ".join(str(qubit) for qubit in circuit.measurements)
        lines.append(f"circuit.probability(target=[{measurements}])")
        if include_runner:
            lines.extend(_braket_runner_lines(runner_shots))
        return "\n".join(lines) + "\n"

    def capabilities(self) -> dict[str, object]:
        return {
            "sdk": self.output_format,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "import_hook": "static braket.circuits.Circuit AST",
            "emit_hook": "Braket Circuit source",
            "diagnostic_hooks": ["probability-target caveats", "provider/runtime calls"],
            "supported_annotations": [],
        }

    def diagnostics(self) -> list[TranslationDiagnostic]:
        return [
            TranslationDiagnostic(
                "warning",
                "translation.caveat.braket_probability",
                "Braket output emits probability targets for circuit construction; --include-runner uses LocalSimulator measurement counts.",
            )
        ]


def _braket_lines(operation: CircuitOperation) -> list[str]:
    gate = operation.gate
    q = operation.qubits
    if gate in {"H", "X", "Y", "Z", "S", "T"}:
        return [f"circuit.{gate.lower()}({q[0]})"]
    if gate == "RESET":
        return [f"# neutral_reset targets=[{q[0]}]"]
    if gate == "BARRIER":
        targets = ",".join(str(qubit) for qubit in q)
        return [f"# neutral_barrier targets=[{targets}]"]
    if gate == "DELAY":
        targets = ",".join(str(qubit) for qubit in q)
        duration = operation.params.get("duration")
        unit = operation.params.get("unit", "")
        return [f"# neutral_delay targets=[{targets}] duration={duration!r} unit={unit!r}"]
    if gate == "SX":
        return [f"circuit.v({q[0]})"]
    if gate in {"P", "PHASE"}:
        return [f"circuit.phaseshift({q[0]}, angle={_format_number(operation.params['theta'])})"]
    if gate in {"RX", "RY", "RZ"}:
        return [
            f"circuit.{gate.lower()}({q[0]}, angle={_format_number(operation.params['theta'])})"
        ]
    if gate == "U":
        return [
            f"circuit.rz({q[0]}, angle={_format_number(operation.params['phi'])})",
            f"circuit.ry({q[0]}, angle={_format_number(operation.params['theta'])})",
            f"circuit.rz({q[0]}, angle={_format_number(operation.params['lambda'])})",
        ]
    if gate == "CNOT":
        return [f"circuit.cnot({q[0]}, {q[1]})"]
    if gate == "CZ":
        return [f"circuit.cz({q[0]}, {q[1]})"]
    if gate == "SWAP":
        return [f"circuit.swap({q[0]}, {q[1]})"]
    if gate == "CCX":
        return [f"circuit.ccnot({q[0]}, {q[1]}, {q[2]})"]
    if gate in {"CRX", "CRY", "CRZ"}:
        return [
            f"circuit.{gate.lower()}({q[0]}, {q[1]}, angle={_format_number(operation.params['theta'])})"
        ]
    if gate == "CPHASE":
        return [
            f"circuit.cphaseshift({q[0]}, {q[1]}, angle={_format_number(operation.params['theta'])})"
        ]
    raise ValueError(f"Unsupported Braket emit gate: {gate}")


def _braket_noise_lines(circuit: InternalCircuit) -> list[str]:
    channel_map = {
        "depolarizing": "Depolarizing",
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
            lines.append(
                f"circuit.apply_gate_noise(Noise.{channel}({_format_number(item.probability)}), target_qubits=[{target}])"
            )
    return lines


def _braket_runner_lines(shots: int) -> list[str]:
    return [
        "",
        'if __name__ == "__main__":',
        "    from braket.devices import LocalSimulator",
        "",
        f"    result = LocalSimulator().run(circuit, shots={shots}).result()",
        "    print(dict(sorted(result.measurement_counts.items())))",
    ]


def _format_number(value: object) -> str:
    if not isinstance(value, int | float):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")
    return repr(float(value))
