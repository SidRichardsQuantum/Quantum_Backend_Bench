"""Qibo NumPy circuit translation adapter."""

from __future__ import annotations

import ast

from quantum_backend_bench.core.benchmark_spec import (
    CircuitOperation,
    InternalCircuit,
    NoiseInstruction,
)
from quantum_backend_bench.core.circuit_translate import TranslationDiagnostic
from quantum_backend_bench.core.noise import (
    noise_after_circuit,
    noise_after_operation,
    readout_noise,
)


class QiboCircuitAdapter:
    """Adapter hooks for static Qibo snippets and local NumPy output."""

    input_format = "qibo"
    output_format = "qibo_numpy"

    def parse_ast(self, tree: ast.AST) -> InternalCircuit:
        from quantum_backend_bench.core import circuit_translate as circuit_translation

        return circuit_translation._parse_qibo_ast(tree)

    def emit(
        self,
        circuit: InternalCircuit,
        *,
        include_runner: bool = False,
        runner_shots: int = 1024,
    ) -> str:
        density_matrix = bool(circuit.noise) or any(
            operation.gate == "RESET" for operation in circuit.operations
        )
        lines = [
            "from qibo import Circuit, gates",
            "",
            f"circuit = Circuit({circuit.n_qubits}, density_matrix={density_matrix!r})",
        ]
        for operation_index, operation in enumerate(circuit.operations):
            lines.extend(_qibo_lines(operation))
            lines.extend(
                _qibo_noise_lines(noise_after_operation(circuit.noise, operation_index, operation))
            )
        lines.extend(_qibo_noise_lines(noise_after_circuit(circuit.noise)))
        lines.extend(_qibo_noise_lines(readout_noise(circuit.noise)))
        measured_qubits = circuit.measurements or list(range(circuit.n_qubits))
        measurements = ", ".join(str(qubit) for qubit in measured_qubits)
        lines.append(f'circuit.add(gates.M({measurements}, register_name="m"))')
        if include_runner:
            lines.extend(_qibo_runner_lines(runner_shots))
        return "\n".join(lines) + "\n"

    def capabilities(self) -> dict[str, object]:
        return {
            "sdk": self.output_format,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "import_hook": "static qibo.Circuit/gates AST",
            "emit_hook": "Qibo Circuit source with explicit NumPy runner",
            "diagnostic_hooks": ["local backend selection", "hardware/provider calls"],
            "supported_annotations": ["reset", "delay"],
        }

    def diagnostics(self) -> list[TranslationDiagnostic]:
        return [
            TranslationDiagnostic(
                "info",
                "translation.caveat.qibo_numpy",
                "Qibo runner output explicitly constructs the bundled local NumPy backend.",
            )
        ]


def _qibo_lines(operation: CircuitOperation) -> list[str]:
    gate = operation.gate
    q = operation.qubits
    if gate in {"H", "X", "Y", "Z", "S", "T", "SX"}:
        return [f"circuit.add(gates.{gate}({q[0]}))"]
    if gate == "RESET":
        return [f"circuit.add(gates.ResetChannel({q[0]}, [1.0, 0.0]))"]
    if gate == "BARRIER":
        targets = ",".join(str(qubit) for qubit in q)
        return [f"# neutral_barrier targets=[{targets}]"]
    if gate == "DELAY":
        delay = int(float(operation.params.get("duration", 0)))
        return [f"circuit.add(gates.Align({qubit}, delay={delay}))" for qubit in q]
    if gate in {"P", "PHASE"}:
        return [f"circuit.add(gates.U1({q[0]}, theta={_format_number(operation.params['theta'])}))"]
    if gate in {"RX", "RY", "RZ"}:
        return [
            f"circuit.add(gates.{gate}({q[0]}, theta={_format_number(operation.params['theta'])}))"
        ]
    if gate == "U":
        return [
            "circuit.add(gates.U3("
            f"{q[0]}, theta={_format_number(operation.params['theta'])}, "
            f"phi={_format_number(operation.params['phi'])}, "
            f"lam={_format_number(operation.params['lambda'])}))"
        ]
    if gate == "CNOT":
        return [f"circuit.add(gates.CNOT({q[0]}, {q[1]}))"]
    if gate in {"CZ", "SWAP"}:
        return [f"circuit.add(gates.{gate}({q[0]}, {q[1]}))"]
    if gate == "CCX":
        return [f"circuit.add(gates.TOFFOLI({q[0]}, {q[1]}, {q[2]}))"]
    if gate in {"CRX", "CRY", "CRZ"}:
        return [
            f"circuit.add(gates.{gate}({q[0]}, {q[1]}, theta={_format_number(operation.params['theta'])}))"
        ]
    if gate == "CPHASE":
        return [
            f"circuit.add(gates.CU1({q[0]}, {q[1]}, theta={_format_number(operation.params['theta'])}))"
        ]
    raise ValueError(f"Unsupported Qibo emit gate: {gate}")


def _qibo_noise_lines(noise: list[NoiseInstruction]) -> list[str]:
    lines = []
    for item in noise:
        for target in item.targets:
            probability = _format_number(item.probability)
            if item.channel == "depolarizing":
                qibo_lambda = _format_number(4.0 * item.probability / 3.0)
                lines.append(f"circuit.add(gates.DepolarizingChannel({target}, lam={qibo_lambda}))")
            elif item.channel == "bit_flip":
                lines.append(
                    f"circuit.add(gates.PauliNoiseChannel({target}, [('X', {probability})]))"
                )
            elif item.channel == "phase_flip":
                lines.append(
                    f"circuit.add(gates.PauliNoiseChannel({target}, [('Z', {probability})]))"
                )
            elif item.channel == "amplitude_damping":
                lines.append(
                    f"circuit.add(gates.AmplitudeDampingChannel({target}, gamma={probability}))"
                )
            elif item.channel == "readout_error":
                lines.append(
                    "circuit.add(gates.ReadoutErrorChannel("
                    f"{target}, [[{1.0 - item.probability!r}, {probability}], "
                    f"[{probability}, {1.0 - item.probability!r}]]))"
                )
            else:
                lines.append(
                    f"# neutral_noise channel={item.channel} targets={[target]!r} probability={item.probability!r}"
                )
    return lines


def _qibo_runner_lines(shots: int) -> list[str]:
    return [
        "",
        'if __name__ == "__main__":',
        "    import qibo",
        "",
        "    backend = qibo.construct_backend('numpy')",
        f"    result = backend.execute_circuit(circuit, nshots={shots})",
        "    print(dict(sorted(result.frequencies(binary=True).items())))",
    ]


def _format_number(value: object) -> str:
    if not isinstance(value, int | float):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")
    return repr(float(value))
