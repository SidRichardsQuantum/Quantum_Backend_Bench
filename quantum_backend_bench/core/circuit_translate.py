"""Circuit translation helpers for supported local quantum SDK snippets."""

from __future__ import annotations

import ast
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)
from quantum_backend_bench.core.circuit_export import import_openqasm_circuit
from quantum_backend_bench.core.exact import exact_probabilities
from quantum_backend_bench.core.metrics import normalize_counts, total_variation_distance

FREE_LOCAL_TRANSLATION_SDKS = ("braket_local", "cirq", "pennylane", "qiskit_aer")
TRANSLATION_INPUT_FORMATS = (
    "auto",
    "internal-json",
    "openqasm",
    "braket",
    "cirq",
    "pennylane",
    "qiskit",
)
TRANSLATION_OUTPUT_FORMATS = (*FREE_LOCAL_TRANSLATION_SDKS, "internal-json", "openqasm")
TRANSLATION_VERIFY_MODES = ("none", "exact", "samples")

_OUTPUT_IMPORT_FORMAT = {
    "braket_local": "braket",
    "cirq": "cirq",
    "pennylane": "pennylane",
    "qiskit_aer": "qiskit",
    "internal-json": "internal-json",
    "openqasm": "openqasm",
}


@dataclass(slots=True)
class TranslationDiagnostic:
    """Structured diagnostic emitted by circuit translation."""

    severity: str
    code: str
    message: str


@dataclass(slots=True)
class TranslationVerification:
    """Semantic verification result for a translated circuit."""

    mode: str
    passed: bool
    total_variation_distance: float | None
    tolerance: float
    details: str


@dataclass(slots=True)
class TranslationResult:
    """Translated circuit source plus notes, diagnostics, and verification."""

    source: str
    notes: list[str]
    diagnostics: list[TranslationDiagnostic] = field(default_factory=list)
    verification: TranslationVerification | None = None


class TranslationError(ValueError):
    """Translation failed with structured diagnostics."""

    def __init__(self, diagnostics: Iterable[TranslationDiagnostic]) -> None:
        self.diagnostics = list(diagnostics)
        message = "; ".join(
            f"{diagnostic.code}: {diagnostic.message}" for diagnostic in self.diagnostics
        )
        super().__init__(message)


def translation_result_report(
    result: TranslationResult,
    *,
    source_path: str | None = None,
    from_format: str | None = None,
    to_format: str | None = None,
) -> dict[str, object]:
    """Return a JSON-compatible report for a translation result."""

    report: dict[str, object] = {
        "source_path": source_path,
        "from_format": from_format,
        "to_format": to_format,
        "notes": result.notes,
        "diagnostics": [_diagnostic_payload(diagnostic) for diagnostic in result.diagnostics],
        "verification": _verification_payload(result.verification),
    }
    return report


def translation_check_report(
    benchmark: BenchmarkSpec,
    detected_format: str,
    *,
    source_path: str | None = None,
    diagnostics: list[TranslationDiagnostic] | None = None,
) -> dict[str, object]:
    """Return a JSON-compatible report for a translation preflight check."""

    circuit = _internal_circuit(benchmark)
    gate_counts: dict[str, int] = {}
    for operation in circuit.operations:
        gate_counts[operation.gate] = gate_counts.get(operation.gate, 0) + 1
    return {
        "source_path": source_path,
        "input_format": detected_format,
        "n_qubits": benchmark.n_qubits,
        "operation_count": len(circuit.operations),
        "measurements": list(circuit.measurements),
        "gate_counts": dict(sorted(gate_counts.items())),
        "diagnostics": [
            _diagnostic_payload(diagnostic) for diagnostic in (diagnostics or _caveat_diagnostics())
        ],
        "verification_available": True,
        "supported_outputs": list(TRANSLATION_OUTPUT_FORMATS),
    }


def translation_error_report(
    error: TranslationError,
    *,
    source_path: str | None = None,
    from_format: str | None = None,
) -> dict[str, object]:
    """Return a JSON-compatible report for a failed translation/check."""

    return {
        "source_path": source_path,
        "from_format": from_format,
        "status": "failed",
        "diagnostics": [_diagnostic_payload(diagnostic) for diagnostic in error.diagnostics],
    }


def _diagnostic_payload(diagnostic: TranslationDiagnostic) -> dict[str, str]:
    return {
        "severity": diagnostic.severity,
        "code": diagnostic.code,
        "message": diagnostic.message,
    }


def _verification_payload(verification: TranslationVerification | None) -> dict[str, object] | None:
    if verification is None:
        return None
    return {
        "mode": verification.mode,
        "passed": verification.passed,
        "total_variation_distance": verification.total_variation_distance,
        "tolerance": verification.tolerance,
        "details": verification.details,
    }


def _caveat_diagnostics() -> list[TranslationDiagnostic]:
    return [
        TranslationDiagnostic(
            "warning",
            "translation.caveat.measurement_order",
            "SDKs may display measurement bitstrings with different endian conventions; verification compares neutral measurement probabilities.",
        ),
        TranslationDiagnostic(
            "warning",
            "translation.caveat.braket_probability",
            "Braket output emits probability targets for circuit construction; --include-runner uses LocalSimulator measurement counts.",
        ),
        TranslationDiagnostic(
            "warning",
            "translation.caveat.pennylane_sampling",
            "PennyLane output is a QNode returning qml.sample; runner output wraps it with qml.set_shots.",
        ),
        TranslationDiagnostic(
            "warning",
            "translation.caveat.controlled_phase",
            "Controlled-phase operations are mapped through each SDK's closest native phase convention and should be verified for nontrivial angles.",
        ),
    ]


def translate_circuit_source(
    source: str,
    *,
    from_format: str = "auto",
    to_format: str,
    name: str = "translated_circuit",
    verify: str = "none",
    verification_tolerance: float = 1e-9,
    sample_shots: int = 2048,
    include_runner: bool = False,
    runner_shots: int = 1024,
) -> TranslationResult:
    """Translate a supported circuit source into another supported representation."""

    if verify not in TRANSLATION_VERIFY_MODES:
        raise ValueError(
            f"Unknown verification mode '{verify}'. Available: {', '.join(TRANSLATION_VERIFY_MODES)}"
        )
    benchmark, detected_format = import_circuit_source(source, from_format=from_format, name=name)
    output = emit_circuit_source(
        benchmark, to_format, include_runner=include_runner, runner_shots=runner_shots
    )
    notes = [f"input_format={detected_format}", f"output_format={to_format}"]
    diagnostics = [
        TranslationDiagnostic(
            "info",
            "translation.scope",
            "Static circuit translation preserves supported gates and measurements only.",
        ),
        *_caveat_diagnostics(),
    ]
    verification = None
    if verify != "none":
        verification = verify_translation(
            benchmark,
            output,
            to_format=to_format,
            mode=verify,
            tolerance=verification_tolerance,
            sample_shots=sample_shots,
        )
        status = "passed" if verification.passed else "failed"
        notes.append(f"verification={status}")
        diagnostics.append(
            TranslationDiagnostic(
                "info" if verification.passed else "error",
                f"translation.verify.{status}",
                verification.details,
            )
        )
    return TranslationResult(output, notes, diagnostics, verification)


def import_circuit_source(
    source: str, *, from_format: str = "auto", name: str = "translated_circuit"
) -> tuple[BenchmarkSpec, str]:
    """Import supported circuit source into a BenchmarkSpec with InternalCircuit data."""

    if from_format not in TRANSLATION_INPUT_FORMATS:
        available = ", ".join(TRANSLATION_INPUT_FORMATS)
        raise ValueError(f"Unknown input format '{from_format}'. Available: {available}")

    selected_format = _detect_format(source) if from_format == "auto" else from_format
    try:
        if selected_format == "internal-json":
            return _import_internal_json(source, name=name), selected_format
        if selected_format == "openqasm":
            return import_openqasm_circuit(source, name=name), selected_format
        if selected_format in {"braket", "cirq", "pennylane", "qiskit"}:
            return _import_python_sdk(source, selected_format, name=name), selected_format
    except TranslationError:
        raise
    except ValueError as exc:
        raise TranslationError(
            [TranslationDiagnostic("error", "translation.parse", str(exc))]
        ) from exc
    raise ValueError(f"Unsupported input format: {selected_format}")


def emit_circuit_source(
    benchmark: BenchmarkSpec,
    to_format: str,
    *,
    include_runner: bool = False,
    runner_shots: int = 1024,
) -> str:
    """Emit a supported circuit representation from an InternalCircuit benchmark."""

    if to_format not in TRANSLATION_OUTPUT_FORMATS:
        available = ", ".join(TRANSLATION_OUTPUT_FORMATS)
        raise ValueError(f"Unknown output format '{to_format}'. Available: {available}")
    circuit = _internal_circuit(benchmark)
    if to_format == "internal-json":
        return _emit_internal_json(circuit)
    if to_format == "openqasm":
        from quantum_backend_bench.core.circuit_export import export_benchmark_circuit

        return export_benchmark_circuit(benchmark, "openqasm")
    if to_format == "qiskit_aer":
        return _emit_qiskit(circuit, include_runner=include_runner, runner_shots=runner_shots)
    if to_format == "cirq":
        return _emit_cirq(circuit, include_runner=include_runner, runner_shots=runner_shots)
    if to_format == "pennylane":
        return _emit_pennylane(circuit, include_runner=include_runner, runner_shots=runner_shots)
    if to_format == "braket_local":
        return _emit_braket(circuit, include_runner=include_runner, runner_shots=runner_shots)
    raise ValueError(f"Unsupported output format: {to_format}")


def verify_translation(
    original: BenchmarkSpec,
    translated_source: str,
    *,
    to_format: str,
    mode: str = "exact",
    tolerance: float = 1e-9,
    sample_shots: int = 2048,
) -> TranslationVerification:
    """Verify translated circuit semantics via the neutral internal simulator."""

    if mode not in {"exact", "samples"}:
        raise ValueError("Verification mode must be 'exact' or 'samples'.")
    imported, _ = import_circuit_source(
        translated_source,
        from_format=_OUTPUT_IMPORT_FORMAT[to_format],
        name=f"{original.name}_translated",
    )
    original_probs = exact_probabilities(original)
    translated_probs = exact_probabilities(imported)
    if mode == "samples":
        from quantum_backend_bench.backends.qutip_backend import _sample_counts

        original_counts = _sample_counts(original_probs, shots=sample_shots, seed=0)
        translated_counts = _sample_counts(translated_probs, shots=sample_shots, seed=0)
        original_distribution = normalize_counts(original_counts, shots=sample_shots)
        translated_distribution = normalize_counts(translated_counts, shots=sample_shots)
        tvd = total_variation_distance(translated_distribution, original_distribution)
        detail_mode = f"sampled distributions with {sample_shots} shots"
    else:
        tvd = total_variation_distance(translated_probs, original_probs)
        detail_mode = "exact probabilities"
    passed = tvd is not None and tvd <= tolerance
    status = "passed" if passed else "failed"
    return TranslationVerification(
        mode=mode,
        passed=passed,
        total_variation_distance=tvd,
        tolerance=tolerance,
        details=(
            f"Semantic verification {status}: {detail_mode} TVD={tvd} "
            f"with tolerance={tolerance}."
        ),
    )


def _detect_format(source: str) -> str:
    stripped = source.lstrip()
    if stripped.startswith("{"):
        return "internal-json"
    if "OPENQASM" in source[:200]:
        return "openqasm"
    if "QuantumCircuit" in source or "qiskit" in source:
        return "qiskit"
    if "cirq." in source:
        return "cirq"
    if "pennylane" in source or "qml." in source:
        return "pennylane"
    if "braket." in source or "Circuit()" in source:
        return "braket"
    raise TranslationError(
        [
            TranslationDiagnostic(
                "error",
                "translation.detect",
                "Could not detect circuit input format. Use --from-format explicitly.",
            )
        ]
    )


def _import_internal_json(source: str, *, name: str) -> BenchmarkSpec:
    payload = json.loads(source)
    operations = [
        CircuitOperation(
            str(item["gate"]),
            tuple(int(qubit) for qubit in item["qubits"]),
            dict(item.get("params", {})),
        )
        for item in payload.get("operations", [])
    ]
    n_qubits = int(payload["n_qubits"])
    measurements = [int(qubit) for qubit in payload.get("measurements", [])]
    return BenchmarkSpec(
        name=name,
        n_qubits=n_qubits,
        parameters={"source": "internal-json"},
        circuit_data=InternalCircuit(n_qubits, operations, measurements or list(range(n_qubits))),
        metadata={"family": "imported", "format": "internal-json"},
    )


def _import_python_sdk(source: str, sdk: str, *, name: str) -> BenchmarkSpec:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise TranslationError(
            [TranslationDiagnostic("error", "translation.python.syntax", str(exc))]
        ) from exc
    _reject_unsupported_constructs(tree, sdk)
    if sdk == "qiskit":
        circuit = _parse_qiskit_ast(tree)
    elif sdk == "cirq":
        circuit = _parse_cirq_ast(tree)
    elif sdk == "pennylane":
        circuit = _parse_pennylane_ast(tree)
    elif sdk == "braket":
        circuit = _parse_braket_ast(tree)
    else:
        raise ValueError(f"Unsupported Python SDK input: {sdk}")
    return BenchmarkSpec(
        name=name,
        n_qubits=circuit.n_qubits,
        parameters={"source": sdk},
        circuit_data=circuit,
        metadata={"family": "imported", "format": sdk},
    )


def _reject_unsupported_constructs(tree: ast.AST, sdk: str) -> None:
    diagnostics: list[TranslationDiagnostic] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if _is_main_guard(node):
                continue
            diagnostics.append(
                TranslationDiagnostic(
                    "error",
                    "python.conditionals",
                    "Conditional circuit construction is unsupported; provide a statically constructed circuit.",
                )
            )
        elif isinstance(node, ast.While):
            diagnostics.append(
                TranslationDiagnostic(
                    "error",
                    "python.dynamic_loop",
                    "while loops are unsupported; use simple for-loops over static range(...).",
                )
            )
        elif isinstance(node, ast.For) and (
            not isinstance(node.iter, ast.Call) or _call_name(node.iter.func) != "range"
        ):
            diagnostics.append(
                TranslationDiagnostic(
                    "error",
                    "python.dynamic_loop",
                    "Only for-loops over static range(...) are supported.",
                )
            )
        elif isinstance(node, ast.FunctionDef) and _function_returns_circuit(node):
            diagnostics.append(
                TranslationDiagnostic(
                    "error",
                    "python.function_built_circuit",
                    "Functions that build and return circuits are unsupported; inline static circuit construction.",
                )
            )
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if _is_provider_or_runtime_call(call_name):
                diagnostics.append(
                    TranslationDiagnostic(
                        "error",
                        "sdk.runtime_call",
                        f"Provider/runtime call '{call_name}' is outside circuit translation scope.",
                    )
                )
            if sdk == "qiskit" and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"to_gate", "append", "compose", "unitary"}:
                    diagnostics.append(
                        TranslationDiagnostic(
                            "error",
                            "qiskit.custom_gate",
                            f"Qiskit custom/composed operation '{node.func.attr}' is unsupported.",
                        )
                    )
    if diagnostics:
        raise TranslationError(diagnostics)


def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _function_returns_circuit(node: ast.FunctionDef) -> bool:
    assigned: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Assign) and isinstance(child.value, ast.Call):
            call_name = _call_name(child.value.func)
            if call_name.endswith("Circuit") or call_name == "QuantumCircuit":
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assigned.add(target.id)
        if isinstance(child, ast.Return):
            if isinstance(child.value, ast.Name) and child.value.id in assigned:
                return True
            if isinstance(child.value, ast.Call):
                call_name = _call_name(child.value.func)
                if call_name.endswith("Circuit") or call_name == "QuantumCircuit":
                    return True
    return False


def _is_provider_or_runtime_call(call_name: str) -> bool:
    lowered = call_name.lower()
    runtime_tokens = (
        "runtime",
        "service",
        "backend.run",
        "sampler",
        "estimator",
        "local simulator",
        "localsimulator",
        "device.run",
    )
    provider_tokens = ("ibm", "provider", "awsbraket", "azure", "rigetti")
    return any(token in lowered for token in (*runtime_tokens, *provider_tokens))


def _parse_qiskit_ast(tree: ast.AST) -> InternalCircuit:
    register_vars: dict[str, int] = {}
    circuit_vars: dict[str, int] = {}
    operations: list[CircuitOperation] = []
    measurements: list[int] = []

    for node, constants in _iter_static_statements(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call_name = _call_name(node.value.func)
            if call_name in {"QuantumRegister", "ClassicalRegister"} and node.value.args:
                size = _int_expr(node.value.args[0], constants)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        register_vars[target.id] = size
            if call_name == "QuantumCircuit" and node.value.args:
                n_qubits = _qiskit_circuit_size(node.value.args[0], constants, register_vars)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        circuit_vars[target.id] = n_qubits
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        var_name = _name(call.func.value)
        if var_name not in circuit_vars:
            continue
        method = call.func.attr
        if method == "measure_all":
            measurements = list(range(circuit_vars[var_name]))
            continue
        if method == "measure":
            if call.args:
                measurements.append(_qiskit_index_expr(call.args[0], constants, register_vars))
            continue
        operation = _qiskit_operation(method, call, constants, register_vars)
        if operation is not None:
            operations.append(operation)

    if not circuit_vars:
        raise _unsupported(
            "qiskit.no_circuit", "No supported Qiskit QuantumCircuit construction found."
        )
    n_qubits = next(iter(circuit_vars.values()))
    return InternalCircuit(n_qubits, operations, measurements or list(range(n_qubits)))


def _qiskit_circuit_size(
    node: ast.AST, constants: dict[str, object], register_vars: dict[str, int]
) -> int:
    if isinstance(node, ast.Name) and node.id in register_vars:
        return register_vars[node.id]
    return _int_expr(node, constants)


def _qiskit_operation(
    method: str,
    call: ast.Call,
    constants: dict[str, object],
    register_vars: dict[str, int],
) -> CircuitOperation | None:
    one_qubit = {"h": "H", "x": "X", "y": "Y", "z": "Z", "s": "S", "t": "T"}
    rotations = {"rx": "RX", "ry": "RY", "rz": "RZ"}
    two_qubit = {"cx": "CNOT", "cnot": "CNOT", "cz": "CZ", "swap": "SWAP"}
    if method in one_qubit and len(call.args) >= 1:
        return CircuitOperation(
            one_qubit[method], (_qiskit_index_expr(call.args[0], constants, register_vars),)
        )
    if method in rotations and len(call.args) >= 2:
        return CircuitOperation(
            rotations[method],
            (_qiskit_index_expr(call.args[1], constants, register_vars),),
            {"theta": _number_expr(call.args[0], constants)},
        )
    if method in two_qubit and len(call.args) >= 2:
        return CircuitOperation(
            two_qubit[method],
            (
                _qiskit_index_expr(call.args[0], constants, register_vars),
                _qiskit_index_expr(call.args[1], constants, register_vars),
            ),
        )
    if method == "cp" and len(call.args) >= 3:
        return CircuitOperation(
            "CPHASE",
            (
                _qiskit_index_expr(call.args[1], constants, register_vars),
                _qiskit_index_expr(call.args[2], constants, register_vars),
            ),
            {"theta": _number_expr(call.args[0], constants)},
        )
    return None


def _qiskit_index_expr(
    node: ast.AST, constants: dict[str, object], register_vars: dict[str, int]
) -> int:
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in register_vars
    ):
        return _int_expr(node.slice, constants)
    return _int_expr(node, constants)


def _parse_cirq_ast(tree: ast.AST) -> InternalCircuit:
    qubit_vars: dict[str, int] = {}
    qubit_ranges: dict[str, int] = {}
    circuit_vars: set[str] = set()
    operations: list[CircuitOperation] = []
    measurements: list[int] = []

    for node, constants in _iter_static_statements(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call_name = _call_name(node.value.func)
            if call_name.endswith("LineQubit.range") and node.value.args:
                n_qubits = _int_expr(node.value.args[0], constants)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        qubit_ranges[target.id] = n_qubits
            if call_name.endswith("LineQubit") and node.value.args:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        qubit_vars[target.id] = _int_expr(node.value.args[0], constants)
            if call_name.endswith("Circuit"):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        circuit_vars.add(target.id)
                for arg in node.value.args:
                    _collect_cirq_operation(
                        arg, qubit_ranges, qubit_vars, operations, measurements, constants
                    )

        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "append":
            continue
        if _name(call.func.value) not in circuit_vars:
            continue
        for arg in call.args:
            _collect_cirq_operation(
                arg, qubit_ranges, qubit_vars, operations, measurements, constants
            )

    n_qubits = _inferred_n_qubits(operations, measurements, qubit_ranges, qubit_vars)
    if n_qubits is None:
        raise _unsupported("cirq.no_circuit", "No supported Cirq circuit construction found.")
    return InternalCircuit(n_qubits, operations, measurements or list(range(n_qubits)))


def _collect_cirq_operation(
    node: ast.AST,
    qubit_ranges: dict[str, int],
    qubit_vars: dict[str, int],
    operations: list[CircuitOperation],
    measurements: list[int],
    constants: dict[str, object],
) -> None:
    if isinstance(node, (ast.List, ast.Tuple)):
        for item in node.elts:
            _collect_cirq_operation(
                item, qubit_ranges, qubit_vars, operations, measurements, constants
            )
        return
    if not isinstance(node, ast.Call):
        return
    if isinstance(node.func, ast.Call):
        rotation = _cirq_rotation_operation(node.func, node, qubit_ranges, qubit_vars, constants)
        if rotation is not None:
            operations.append(rotation)
        return
    call_name = _call_name(node.func)
    gate_name = call_name.rsplit(".", 1)[-1]
    if gate_name == "measure":
        measurements.extend(
            _cirq_qubit_index(arg, qubit_ranges, qubit_vars, constants) for arg in node.args
        )
        return
    operation = _cirq_operation(gate_name, node, qubit_ranges, qubit_vars, constants)
    if operation is not None:
        operations.append(operation)


def _cirq_operation(
    gate_name: str,
    call: ast.Call,
    qubit_ranges: dict[str, int],
    qubit_vars: dict[str, int],
    constants: dict[str, object],
) -> CircuitOperation | None:
    one_qubit = {"H": "H", "X": "X", "Y": "Y", "Z": "Z", "S": "S", "T": "T"}
    two_qubit = {"CNOT": "CNOT", "CZ": "CZ", "SWAP": "SWAP"}
    if gate_name in one_qubit and len(call.args) >= 1:
        return CircuitOperation(
            one_qubit[gate_name],
            (_cirq_qubit_index(call.args[0], qubit_ranges, qubit_vars, constants),),
        )
    if gate_name in two_qubit and len(call.args) >= 2:
        return CircuitOperation(
            two_qubit[gate_name],
            (
                _cirq_qubit_index(call.args[0], qubit_ranges, qubit_vars, constants),
                _cirq_qubit_index(call.args[1], qubit_ranges, qubit_vars, constants),
            ),
        )
    return None


def _cirq_rotation_operation(
    gate_call: ast.Call,
    op_call: ast.Call,
    qubit_ranges: dict[str, int],
    qubit_vars: dict[str, int],
    constants: dict[str, object],
) -> CircuitOperation | None:
    gate_name = _call_name(gate_call.func).rsplit(".", 1)[-1]
    rotations = {"rx": "RX", "ry": "RY", "rz": "RZ"}
    if gate_name not in rotations or not gate_call.args or not op_call.args:
        return None
    return CircuitOperation(
        rotations[gate_name],
        (_cirq_qubit_index(op_call.args[0], qubit_ranges, qubit_vars, constants),),
        {"theta": _number_expr(gate_call.args[0], constants)},
    )


def _parse_pennylane_ast(tree: ast.AST) -> InternalCircuit:
    n_qubits: int | None = None
    operations: list[CircuitOperation] = []
    measurements: list[int] = []

    for node, constants in _iter_static_statements(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if _call_name(node.value.func).endswith("device"):
                wires_kw = _keyword(node.value, "wires")
                if wires_kw is not None:
                    n_qubits = _int_expr(wires_kw, constants)
                continue
            operation = _pennylane_operation(node.value, constants)
            if operation is not None:
                operations.append(operation)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
            if _call_name(node.value.func).endswith("sample"):
                wires = _keyword(node.value, "wires")
                if wires is not None:
                    measurements = _wire_list(wires, constants)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            if _call_name(node.value.func).endswith("device"):
                wires_kw = _keyword(node.value, "wires")
                if wires_kw is not None:
                    n_qubits = _int_expr(wires_kw, constants)

    inferred = _inferred_n_qubits(operations, measurements)
    n_qubits = n_qubits or inferred
    if n_qubits is None:
        raise _unsupported(
            "pennylane.no_circuit", "No supported PennyLane circuit operations found."
        )
    return InternalCircuit(n_qubits, operations, measurements or list(range(n_qubits)))


def _pennylane_operation(call: ast.Call, constants: dict[str, object]) -> CircuitOperation | None:
    gate_name = _call_name(call.func).rsplit(".", 1)[-1]
    one_qubit = {
        "Hadamard": "H",
        "PauliX": "X",
        "PauliY": "Y",
        "PauliZ": "Z",
        "S": "S",
        "T": "T",
    }
    rotations = {"RX": "RX", "RY": "RY", "RZ": "RZ"}
    two_qubit = {"CNOT": "CNOT", "CZ": "CZ", "SWAP": "SWAP"}
    wires_node = _pennylane_wires_node(call, gate_name, one_qubit, rotations, two_qubit)
    if wires_node is None:
        return None
    wires = _wire_list(wires_node, constants)
    if gate_name in one_qubit and len(wires) >= 1:
        return CircuitOperation(one_qubit[gate_name], (wires[0],))
    if gate_name in rotations and call.args and len(wires) >= 1:
        return CircuitOperation(
            rotations[gate_name], (wires[0],), {"theta": _number_expr(call.args[0], constants)}
        )
    if gate_name in two_qubit and len(wires) >= 2:
        return CircuitOperation(two_qubit[gate_name], (wires[0], wires[1]))
    if gate_name == "ControlledPhaseShift" and call.args and len(wires) >= 2:
        return CircuitOperation(
            "CPHASE",
            (wires[0], wires[1]),
            {"theta": _number_expr(call.args[0], constants)},
        )
    return None


def _pennylane_wires_node(
    call: ast.Call,
    gate_name: str,
    one_qubit: dict[str, str],
    rotations: dict[str, str],
    two_qubit: dict[str, str],
) -> ast.AST | None:
    keyword_wires = _keyword(call, "wires")
    if keyword_wires is not None:
        return keyword_wires
    if gate_name in one_qubit and call.args:
        return call.args[0]
    if gate_name in rotations and len(call.args) >= 2:
        return call.args[1]
    if gate_name in two_qubit and call.args:
        return call.args[0]
    if gate_name == "ControlledPhaseShift" and len(call.args) >= 2:
        return call.args[1]
    return None


def _parse_braket_ast(tree: ast.AST) -> InternalCircuit:
    circuit_vars: set[str] = set()
    operations: list[CircuitOperation] = []
    measurements: list[int] = []

    for node, constants in _iter_static_statements(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            if _call_name(node.value.func).endswith("Circuit"):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        circuit_vars.add(target.id)
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        var_name = _name(call.func.value)
        if var_name not in circuit_vars:
            continue
        if call.func.attr == "probability":
            target = _keyword(call, "target")
            if target is not None:
                measurements = _wire_list(target, constants)
            continue
        operation = _braket_operation(call.func.attr, call, constants)
        if operation is not None:
            operations.append(operation)

    n_qubits = _inferred_n_qubits(operations, measurements)
    if n_qubits is None:
        raise _unsupported("braket.no_circuit", "No supported Braket Circuit construction found.")
    return InternalCircuit(n_qubits, operations, measurements or list(range(n_qubits)))


def _braket_operation(
    method: str, call: ast.Call, constants: dict[str, object]
) -> CircuitOperation | None:
    one_qubit = {"h": "H", "x": "X", "y": "Y", "z": "Z", "s": "S", "t": "T"}
    rotations = {"rx": "RX", "ry": "RY", "rz": "RZ"}
    two_qubit = {"cnot": "CNOT", "cz": "CZ", "swap": "SWAP"}
    if method in one_qubit and len(call.args) >= 1:
        return CircuitOperation(one_qubit[method], (_int_expr(call.args[0], constants),))
    if method in rotations and len(call.args) >= 1:
        angle = _keyword(call, "angle") or (call.args[1] if len(call.args) >= 2 else None)
        if angle is None:
            return None
        return CircuitOperation(
            rotations[method],
            (_int_expr(call.args[0], constants),),
            {"theta": _number_expr(angle, constants)},
        )
    if method in two_qubit and len(call.args) >= 2:
        return CircuitOperation(
            two_qubit[method],
            (_int_expr(call.args[0], constants), _int_expr(call.args[1], constants)),
        )
    if method == "cphaseshift" and len(call.args) >= 2:
        angle = _keyword(call, "angle") or (call.args[2] if len(call.args) >= 3 else None)
        if angle is None:
            return None
        return CircuitOperation(
            "CPHASE",
            (_int_expr(call.args[0], constants), _int_expr(call.args[1], constants)),
            {"theta": _number_expr(angle, constants)},
        )
    return None


def _iter_static_statements(tree: ast.AST) -> Iterator[tuple[ast.stmt, dict[str, object]]]:
    body = tree.body if isinstance(tree, ast.Module) else []
    yield from _walk_static_body(body, {})


def _walk_static_body(
    body: list[ast.stmt], constants: dict[str, object]
) -> Iterator[tuple[ast.stmt, dict[str, object]]]:
    local_constants = dict(constants)
    for node in body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            value = _literal_constant(node.value, local_constants)
            if value is not None:
                local_constants[node.targets[0].id] = value
        if isinstance(node, ast.For):
            yield from _walk_static_for(node, local_constants)
            continue
        yield node, dict(local_constants)
        if isinstance(node, ast.FunctionDef):
            yield from _walk_static_body(node.body, local_constants)


def _walk_static_for(
    node: ast.For, constants: dict[str, object]
) -> Iterator[tuple[ast.stmt, dict[str, object]]]:
    if not isinstance(node.target, ast.Name):
        raise _unsupported("python.dynamic_loop", "Only simple for-loop targets are supported.")
    values = _range_values(node.iter, constants)
    for value in values:
        loop_constants = dict(constants)
        loop_constants[node.target.id] = value
        yield from _walk_static_body(node.body, loop_constants)


def _range_values(node: ast.AST, constants: dict[str, object]) -> range:
    if not isinstance(node, ast.Call) or _call_name(node.func) != "range":
        raise _unsupported(
            "python.dynamic_loop", "Only for-loops over literal range(...) are supported."
        )
    args = [_int_expr(arg, constants) for arg in node.args]
    if len(args) == 1:
        return range(args[0])
    if len(args) == 2:
        return range(args[0], args[1])
    if len(args) == 3:
        return range(args[0], args[1], args[2])
    raise _unsupported(
        "python.dynamic_loop", "range(...) with more than 3 arguments is unsupported."
    )


def _literal_constant(node: ast.AST, constants: dict[str, object]) -> object | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    try:
        return _number_expr(node, constants)
    except TranslationError:
        return None


def _emit_internal_json(circuit: InternalCircuit) -> str:
    payload = {
        "n_qubits": circuit.n_qubits,
        "operations": [
            {"gate": op.gate, "qubits": list(op.qubits), "params": op.params}
            for op in circuit.operations
        ],
        "measurements": circuit.measurements,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _emit_qiskit(
    circuit: InternalCircuit, *, include_runner: bool = False, runner_shots: int = 1024
) -> str:
    lines = [
        "from qiskit import QuantumCircuit",
        "",
        f"circuit = QuantumCircuit({circuit.n_qubits}, {len(circuit.measurements)})",
    ]
    for operation in circuit.operations:
        lines.append(_qiskit_line(operation))
    for classical_index, qubit in enumerate(circuit.measurements):
        lines.append(f"circuit.measure({qubit}, {len(circuit.measurements) - classical_index - 1})")
    if include_runner:
        lines.extend(_qiskit_runner_lines(runner_shots))
    return "\n".join(lines) + "\n"


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


def _cirq_runner_lines(shots: int) -> list[str]:
    return [
        "",
        'if __name__ == "__main__":',
        "    simulator = cirq.Simulator()",
        f"    result = simulator.run(circuit, repetitions={shots})",
        "    counts = result.histogram(key=\"m\", fold_func=lambda bits: ''.join(str(int(bit)) for bit in bits))",
        "    print(dict(sorted(counts.items())))",
    ]


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


def _braket_runner_lines(shots: int) -> list[str]:
    return [
        "",
        'if __name__ == "__main__":',
        "    from braket.devices import LocalSimulator",
        "",
        f"    result = LocalSimulator().run(circuit, shots={shots}).result()",
        "    print(dict(sorted(result.measurement_counts.items())))",
    ]


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


def _emit_cirq(
    circuit: InternalCircuit, *, include_runner: bool = False, runner_shots: int = 1024
) -> str:
    lines = [
        "import cirq",
        "",
        f"qubits = cirq.LineQubit.range({circuit.n_qubits})",
        "circuit = cirq.Circuit()",
    ]
    for operation in circuit.operations:
        lines.append(f"circuit.append({_cirq_expr(operation)})")
    if circuit.measurements:
        qubits = ", ".join(f"qubits[{qubit}]" for qubit in circuit.measurements)
        lines.append(f'circuit.append(cirq.measure({qubits}, key="m"))')
    if include_runner:
        lines.extend(_cirq_runner_lines(runner_shots))
    return "\n".join(lines) + "\n"


def _cirq_expr(operation: CircuitOperation) -> str:
    gate = operation.gate
    q = operation.qubits
    if gate in {"H", "X", "Y", "Z", "S", "T"}:
        return f"cirq.{gate}(qubits[{q[0]}])"
    if gate in {"RX", "RY", "RZ"}:
        return f"cirq.{gate.lower()}({_format_number(operation.params['theta'])})(qubits[{q[0]}])"
    if gate in {"CNOT", "CZ", "SWAP"}:
        return f"cirq.{gate}(qubits[{q[0]}], qubits[{q[1]}])"
    if gate == "CPHASE":
        return (
            "cirq.CZPowGate(exponent="
            f"{_format_number(operation.params['theta'])} / 3.141592653589793)"
            f"(qubits[{q[0]}], qubits[{q[1]}])"
        )
    raise ValueError(f"Unsupported Cirq emit gate: {gate}")


def _emit_pennylane(
    circuit: InternalCircuit, *, include_runner: bool = False, runner_shots: int = 1024
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
        lines.append(f"    {_pennylane_line(operation)}")
    measurements = ", ".join(str(qubit) for qubit in circuit.measurements)
    lines.append(f"    return qml.sample(wires=[{measurements}])")
    if include_runner:
        lines.extend(_pennylane_runner_lines(runner_shots))
    return "\n".join(lines) + "\n"


def _pennylane_line(operation: CircuitOperation) -> str:
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
        return f"qml.{one_qubit[gate]}(wires={q[0]})"
    if gate in {"RX", "RY", "RZ"}:
        return f"qml.{gate}({_format_number(operation.params['theta'])}, wires={q[0]})"
    if gate in {"CNOT", "CZ", "SWAP"}:
        return f"qml.{gate}(wires=[{q[0]}, {q[1]}])"
    if gate == "CPHASE":
        return f"qml.ControlledPhaseShift({_format_number(operation.params['theta'])}, wires=[{q[0]}, {q[1]}])"
    raise ValueError(f"Unsupported PennyLane emit gate: {gate}")


def _emit_braket(
    circuit: InternalCircuit, *, include_runner: bool = False, runner_shots: int = 1024
) -> str:
    lines = [
        "from braket.circuits import Circuit",
        "",
        "circuit = Circuit()",
    ]
    for operation in circuit.operations:
        lines.append(_braket_line(operation))
    measurements = ", ".join(str(qubit) for qubit in circuit.measurements)
    lines.append(f"circuit.probability(target=[{measurements}])")
    if include_runner:
        lines.extend(_braket_runner_lines(runner_shots))
    return "\n".join(lines) + "\n"


def _braket_line(operation: CircuitOperation) -> str:
    gate = operation.gate
    q = operation.qubits
    if gate in {"H", "X", "Y", "Z", "S", "T"}:
        return f"circuit.{gate.lower()}({q[0]})"
    if gate in {"RX", "RY", "RZ"}:
        return f"circuit.{gate.lower()}({q[0]}, angle={_format_number(operation.params['theta'])})"
    if gate == "CNOT":
        return f"circuit.cnot({q[0]}, {q[1]})"
    if gate == "CZ":
        return f"circuit.cz({q[0]}, {q[1]})"
    if gate == "SWAP":
        return f"circuit.swap({q[0]}, {q[1]})"
    if gate == "CPHASE":
        return f"circuit.cphaseshift({q[0]}, {q[1]}, angle={_format_number(operation.params['theta'])})"
    raise ValueError(f"Unsupported Braket emit gate: {gate}")


def _internal_circuit(benchmark: BenchmarkSpec) -> InternalCircuit:
    if not isinstance(benchmark.circuit_data, InternalCircuit):
        raise TypeError("Circuit translation requires InternalCircuit data.")
    return benchmark.circuit_data


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _name(node: ast.AST) -> str | None:
    return node.id if isinstance(node, ast.Name) else None


def _keyword(call: ast.Call, name: str) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _int_expr(node: ast.AST, constants: dict[str, object]) -> int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Name):
        value = constants.get(node.id)
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
    raise _unsupported(
        "python.dynamic_integer",
        f"Expected integer literal or static integer constant, got: {ast.unparse(node)}",
    )


def _number_expr(node: ast.AST, constants: dict[str, object]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name) and isinstance(constants.get(node.id), (int, float)):
        return float(constants[node.id])
    if _call_name(node) in {"math.pi", "np.pi", "numpy.pi"}:
        return 3.141592653589793
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_number_expr(node.operand, constants)
    if isinstance(node, ast.BinOp):
        left = _number_expr(node.left, constants)
        right = _number_expr(node.right, constants)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    raise _unsupported(
        "python.dynamic_parameter",
        f"Expected numeric literal or static numeric expression, got: {ast.unparse(node)}",
    )


def _wire_list(node: ast.AST, constants: dict[str, object]) -> list[int]:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return [node.value]
    if isinstance(node, ast.Name) and isinstance(constants.get(node.id), int):
        return [int(constants[node.id])]
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_int_expr(item, constants) for item in node.elts]
    raise _unsupported(
        "python.dynamic_wires",
        f"Expected integer wire or static wire list literal, got: {ast.unparse(node)}",
    )


def _cirq_qubit_index(
    node: ast.AST,
    qubit_ranges: dict[str, int],
    qubit_vars: dict[str, int],
    constants: dict[str, object],
) -> int:
    if isinstance(node, ast.Name) and node.id in qubit_vars:
        return qubit_vars[node.id]
    if isinstance(node, ast.Name) and isinstance(constants.get(node.id), int):
        return int(constants[node.id])
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in qubit_ranges
    ):
        return _int_expr(node.slice, constants)
    if isinstance(node, ast.Call) and _call_name(node.func).endswith("LineQubit") and node.args:
        return _int_expr(node.args[0], constants)
    raise _unsupported(
        "cirq.dynamic_qubit",
        f"Expected supported Cirq line qubit reference, got: {ast.unparse(node)}",
    )


def _inferred_n_qubits(
    operations: list[CircuitOperation],
    measurements: list[int],
    qubit_ranges: dict[str, int] | None = None,
    qubit_vars: dict[str, int] | None = None,
) -> int | None:
    candidates = [qubit for op in operations for qubit in op.qubits]
    candidates.extend(measurements)
    if qubit_ranges:
        candidates.extend(size - 1 for size in qubit_ranges.values() if size > 0)
    if qubit_vars:
        candidates.extend(qubit_vars.values())
    return max(candidates) + 1 if candidates else None


def _format_number(value: object) -> str:
    return repr(float(value))


def _unsupported(code: str, message: str) -> TranslationError:
    return TranslationError([TranslationDiagnostic("error", code, message)])
