"""Workflow-level SDK translation helpers.

This module covers the semantic layers that sit around a circuit: symbolic
parameters, parameter bindings, measurement requests, local execution wrappers,
neutral result payloads, and Pauli-term measurement grouping.
"""

from __future__ import annotations

import json
from collections import Counter
import ast
from dataclasses import dataclass, field
from typing import Any

from quantum_backend_bench.core.circuit_translate import (
    TranslationDiagnostic,
    TranslationError,
    TranslationResult,
    TranslationVerification,
)
from quantum_backend_bench.core.observable_translate import (
    PauliHamiltonian,
    PauliTerm,
    canonical_hamiltonian,
    import_hamiltonian_source,
)

WORKFLOW_INPUT_FORMATS = ("workflow-json", "qiskit", "cirq", "pennylane", "braket")
WORKFLOW_OUTPUT_FORMATS = ("qiskit_aer", "cirq", "pennylane", "braket_local", "workflow-json")
WORKFLOW_VERIFY_MODES = ("none", "canonical")
RESULT_INPUT_FORMATS = (
    "result-json",
    "qiskit-counts-json",
    "cirq-counts-json",
    "pennylane-samples-json",
    "braket-counts-json",
)
RESULT_OUTPUT_FORMATS = ("result-json",)
GROUPING_STRATEGIES = ("qubit-wise",)


@dataclass(frozen=True, slots=True)
class WorkflowOperation:
    """One operation in a parameterized workflow circuit."""

    gate: str
    targets: tuple[int, ...]
    controls: tuple[int, ...] = ()
    parameter: str | float | None = None


@dataclass(frozen=True, slots=True)
class MeasurementRequest:
    """A neutral measurement or expectation request."""

    kind: str
    targets: tuple[int, ...] = ()
    observable: PauliHamiltonian | None = None


@dataclass(frozen=True, slots=True)
class ParameterizedWorkflow:
    """Neutral workflow representation for local SDK code generation."""

    name: str
    n_qubits: int
    parameters: tuple[str, ...]
    operations: tuple[WorkflowOperation, ...]
    parameter_bindings: dict[str, float] = field(default_factory=dict)
    measurements: tuple[MeasurementRequest, ...] = ()
    shots: int = 1024
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class NeutralResult:
    """Portable result payload shared across SDK result objects."""

    counts: dict[str, int]
    shots: int
    probabilities: dict[str, float]
    expectations: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)


def translate_workflow_source(
    source: str,
    *,
    from_format: str = "workflow-json",
    to_format: str,
    verify: str = "canonical",
) -> TranslationResult:
    """Translate a neutral parameterized workflow into local SDK code or JSON."""

    if verify not in WORKFLOW_VERIFY_MODES:
        available = ", ".join(WORKFLOW_VERIFY_MODES)
        raise ValueError(f"Unknown workflow verification mode '{verify}'. Available: {available}")
    workflow, detected_format = import_workflow_source(source, from_format=from_format)
    output = emit_workflow_source(workflow, to_format)
    diagnostics = [
        TranslationDiagnostic(
            "info",
            "translation.scope.workflow",
            "Workflow translation preserves supported gates, symbolic parameters, bindings, measurements, local execution settings, and neutral result extraction snippets.",
        ),
        TranslationDiagnostic(
            "warning",
            "translation.caveat.workflow_static_import",
            "Workflow-layer static SDK import supports generated snippets and a small native parameterized subset.",
        ),
    ]
    verification = None
    notes = [f"input_format={detected_format}", f"output_format={to_format}"]
    if verify != "none":
        verification = verify_workflow_translation(workflow, output, to_format=to_format)
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


def import_workflow_source(
    source: str, *, from_format: str = "workflow-json"
) -> tuple[ParameterizedWorkflow, str]:
    """Import a neutral workflow JSON document."""

    if from_format not in WORKFLOW_INPUT_FORMATS:
        available = ", ".join(WORKFLOW_INPUT_FORMATS)
        raise ValueError(f"Unknown workflow input format '{from_format}'. Available: {available}")
    if from_format == "workflow-json":
        try:
            payload = json.loads(source)
        except json.JSONDecodeError as exc:
            raise _workflow_error(
                "workflow.invalid_json", f"Could not parse workflow JSON: {exc}"
            ) from exc
        return _workflow_from_payload(payload), from_format
    return _import_static_workflow_source(source, from_format), from_format


def verify_workflow_translation(
    expected: ParameterizedWorkflow, source: str, *, to_format: str
) -> TranslationVerification:
    """Verify generated workflow source by reimporting neutral workflow semantics."""

    imported, _ = import_workflow_source(
        source, from_format=_workflow_output_import_format(to_format)
    )
    passed = canonical_workflow(expected) == canonical_workflow(imported)
    details = (
        "Canonical workflow verification passed."
        if passed
        else "Canonical workflow verification failed."
    )
    return TranslationVerification("canonical", passed, None, 0.0, details)


def canonical_workflow(workflow: ParameterizedWorkflow) -> dict[str, object]:
    """Return normalized workflow semantics for verification and golden tests."""

    return {
        "n_qubits": workflow.n_qubits,
        "parameters": list(workflow.parameters),
        "parameter_bindings": dict(sorted(workflow.parameter_bindings.items())),
        "operations": [
            {
                "gate": operation.gate,
                "targets": list(operation.targets),
                "controls": list(operation.controls),
                "parameter": operation.parameter,
            }
            for operation in workflow.operations
            if operation.gate != "MEASURE"
        ],
        "measurements": [
            {
                "kind": measurement.kind,
                "targets": list(measurement.targets),
                "observable": (
                    canonical_hamiltonian(measurement.observable)
                    if measurement.observable is not None
                    else None
                ),
            }
            for measurement in workflow.measurements
        ],
        "shots": workflow.shots,
        "seed": workflow.seed,
    }


def _workflow_output_import_format(to_format: str) -> str:
    return {
        "qiskit_aer": "qiskit",
        "cirq": "cirq",
        "pennylane": "pennylane",
        "braket_local": "braket",
        "workflow-json": "workflow-json",
    }[to_format]


def emit_workflow_source(workflow: ParameterizedWorkflow, to_format: str) -> str:
    """Emit a workflow in a supported SDK representation."""

    if to_format not in WORKFLOW_OUTPUT_FORMATS:
        available = ", ".join(WORKFLOW_OUTPUT_FORMATS)
        raise ValueError(f"Unknown workflow output format '{to_format}'. Available: {available}")
    if to_format == "workflow-json":
        return json.dumps(_workflow_payload(workflow), indent=2, sort_keys=True) + "\n"
    if to_format == "qiskit_aer":
        return _format_python_source(_emit_qiskit_workflow(workflow))
    if to_format == "cirq":
        return _format_python_source(_emit_cirq_workflow(workflow))
    if to_format == "pennylane":
        return _format_python_source(_emit_pennylane_workflow(workflow))
    if to_format == "braket_local":
        return _format_python_source(_emit_braket_workflow(workflow))
    raise ValueError(f"Unsupported workflow output format: {to_format}")


def _format_python_source(source: str) -> str:
    try:
        import black
    except ImportError:
        return source
    return black.format_str(source, mode=black.FileMode())


def normalize_result_source(
    source: str,
    *,
    from_format: str = "result-json",
    to_format: str = "result-json",
) -> TranslationResult:
    """Normalize supported SDK-shaped result JSON into a neutral result payload."""

    if to_format not in RESULT_OUTPUT_FORMATS:
        available = ", ".join(RESULT_OUTPUT_FORMATS)
        raise ValueError(f"Unknown result output format '{to_format}'. Available: {available}")
    result = import_result_source(source, from_format=from_format)
    output = json.dumps(_result_payload(result), indent=2, sort_keys=True) + "\n"
    return TranslationResult(
        output,
        [f"input_format={from_format}", f"output_format={to_format}", "normalized=result-json"],
        [
            TranslationDiagnostic(
                "info",
                "translation.scope.result_object",
                "Result translation normalizes counts, shots, probabilities, expectations, and metadata into portable JSON.",
            )
        ],
    )


def import_result_source(source: str, *, from_format: str = "result-json") -> NeutralResult:
    """Import supported result JSON shapes into a neutral result object."""

    if from_format not in RESULT_INPUT_FORMATS:
        available = ", ".join(RESULT_INPUT_FORMATS)
        raise ValueError(f"Unknown result input format '{from_format}'. Available: {available}")
    payload = json.loads(source)
    if from_format == "result-json":
        counts = _counts_from_mapping(payload.get("counts", {}))
        shots = int(payload.get("shots", sum(counts.values())))
        probabilities = _probabilities_from_payload(payload.get("probabilities"), counts, shots)
        expectations = {
            str(key): float(value) for key, value in payload.get("expectations", {}).items()
        }
        metadata = dict(payload.get("metadata", {}))
        return NeutralResult(counts, shots, probabilities, expectations, metadata)
    if from_format in {"qiskit-counts-json", "cirq-counts-json", "braket-counts-json"}:
        counts_payload = _counts_payload_for_format(payload, from_format)
        counts = _counts_from_mapping(counts_payload)
        shots = int(payload.get("shots", sum(counts.values())))
        return NeutralResult(
            counts,
            shots,
            _counts_to_probabilities(counts, shots),
            metadata=_result_metadata(payload, from_format),
        )
    samples = payload.get("samples", payload)
    counts = _counts_from_samples(samples)
    shots = int(payload.get("shots", sum(counts.values())))
    return NeutralResult(
        counts,
        shots,
        _counts_to_probabilities(counts, shots),
        metadata={"source_format": from_format},
    )


def group_pauli_terms_source(
    source: str,
    *,
    from_format: str = "auto",
    strategy: str = "qubit-wise",
) -> TranslationResult:
    """Group Pauli terms into jointly measurable qubit-wise commuting sets."""

    groups = group_pauli_terms(source, from_format=from_format, strategy=strategy)
    output = json.dumps(_grouping_payload(groups), indent=2, sort_keys=True) + "\n"
    return TranslationResult(
        output,
        [f"strategy={strategy}", f"group_count={len(groups)}"],
        [
            TranslationDiagnostic(
                "info",
                "translation.scope.measurement_grouping",
                "Grouping uses qubit-wise commutation for weighted Pauli I/X/Y/Z products.",
            )
        ],
    )


def group_pauli_terms(
    source: str | PauliHamiltonian,
    *,
    from_format: str = "auto",
    strategy: str = "qubit-wise",
) -> list[PauliHamiltonian]:
    """Return Pauli-term groups for measurement reuse."""

    if strategy not in GROUPING_STRATEGIES:
        available = ", ".join(GROUPING_STRATEGIES)
        raise ValueError(f"Unknown grouping strategy '{strategy}'. Available: {available}")
    hamiltonian = (
        source
        if isinstance(source, PauliHamiltonian)
        else import_hamiltonian_source(source, from_format=from_format)[0]
    )
    groups: list[list[PauliTerm]] = []
    signatures: list[dict[int, str]] = []
    for term in hamiltonian.terms:
        term_signature = {wire: pauli for wire, pauli in term.paulis if pauli != "I"}
        for index, signature in enumerate(signatures):
            if _qubit_wise_compatible(signature, term_signature):
                groups[index].append(term)
                signature.update(term_signature)
                break
        else:
            groups.append([term])
            signatures.append(dict(term_signature))
    return [PauliHamiltonian(hamiltonian.n_qubits, tuple(group_terms)) for group_terms in groups]


def workflow_translation_report(
    result: TranslationResult,
    *,
    source_path: str | None = None,
    from_format: str | None = None,
    to_format: str | None = None,
) -> dict[str, object]:
    """Return a JSON-compatible workflow translation report."""

    verification = None
    if result.verification is not None:
        verification = {
            "mode": result.verification.mode,
            "passed": result.verification.passed,
            "details": result.verification.details,
        }
    return {
        "source_path": source_path,
        "from_format": from_format,
        "to_format": to_format,
        "notes": result.notes,
        "diagnostics": [
            {"severity": item.severity, "code": item.code, "message": item.message}
            for item in result.diagnostics
        ],
        "verification": verification,
    }


def _workflow_from_payload(payload: dict[str, Any]) -> ParameterizedWorkflow:
    try:
        name = str(payload.get("name", "translated_workflow"))
        n_qubits = int(payload["n_qubits"])
    except (KeyError, TypeError, ValueError) as exc:
        raise _workflow_error(
            "workflow.invalid_schema", "Workflow JSON requires integer n_qubits."
        ) from exc
    parameters = tuple(str(item) for item in payload.get("parameters", ()))
    bindings = {
        str(key): float(value) for key, value in payload.get("parameter_bindings", {}).items()
    }
    operations = tuple(_operation_from_payload(item) for item in payload.get("operations", ()))
    measurements = tuple(
        _measurement_from_payload(item, n_qubits) for item in payload.get("measurements", ())
    )
    shots = int(payload.get("shots", 1024))
    seed = payload.get("seed")
    seed_value = None if seed is None else int(seed)
    _validate_workflow(n_qubits, parameters, bindings, operations, measurements, shots)
    return ParameterizedWorkflow(
        name, n_qubits, parameters, operations, bindings, measurements, shots, seed_value
    )


def _operation_from_payload(payload: dict[str, Any]) -> WorkflowOperation:
    gate = str(payload.get("gate", "")).upper()
    targets = tuple(int(item) for item in payload.get("targets", ()))
    controls = tuple(int(item) for item in payload.get("controls", ()))
    parameter = payload.get("parameter")
    if isinstance(parameter, int | float):
        parameter = float(parameter)
    elif parameter is not None:
        parameter = str(parameter)
    return WorkflowOperation(gate, targets, controls, parameter)


def _measurement_from_payload(payload: dict[str, Any], n_qubits: int) -> MeasurementRequest:
    kind = str(payload.get("type", payload.get("kind", ""))).lower()
    targets = tuple(int(item) for item in payload.get("targets", range(n_qubits)))
    observable = None
    if kind == "expectation":
        observable_payload = payload.get("observable")
        if not isinstance(observable_payload, dict):
            raise _workflow_error(
                "workflow.measurement.observable",
                "Expectation requests require an observable object.",
            )
        observable = _pauli_hamiltonian_from_payload(observable_payload, n_qubits)
    return MeasurementRequest(kind, targets, observable)


def _pauli_hamiltonian_from_payload(
    payload: dict[str, Any], default_n_qubits: int
) -> PauliHamiltonian:
    observable_payload = dict(payload)
    observable_payload.setdefault("n_qubits", default_n_qubits)
    return import_hamiltonian_source(json.dumps(observable_payload), from_format="pauli-json")[0]


def _validate_workflow(
    n_qubits: int,
    parameters: tuple[str, ...],
    bindings: dict[str, float],
    operations: tuple[WorkflowOperation, ...],
    measurements: tuple[MeasurementRequest, ...],
    shots: int,
) -> None:
    if n_qubits < 1:
        raise _workflow_error("workflow.n_qubits", "Workflow n_qubits must be at least 1.")
    if shots < 1:
        raise _workflow_error("workflow.shots", "Workflow shots must be at least 1.")
    known_parameters = set(parameters)
    for key in bindings:
        if key not in known_parameters:
            raise _workflow_error("workflow.binding.unknown", f"Unknown parameter binding '{key}'.")
    for operation in operations:
        if operation.gate not in {"H", "X", "Y", "Z", "RX", "RY", "RZ", "CNOT", "CX", "MEASURE"}:
            raise _workflow_error(
                "workflow.gate.unsupported", f"Unsupported workflow gate '{operation.gate}'."
            )
        for wire in (*operation.targets, *operation.controls):
            if wire < 0 or wire >= n_qubits:
                raise _workflow_error(
                    "workflow.wire", f"Wire {wire} is outside n_qubits={n_qubits}."
                )
        if operation.gate in {"RX", "RY", "RZ"} and operation.parameter is None:
            raise _workflow_error(
                "workflow.parameter.missing", f"Gate {operation.gate} requires a parameter."
            )
        if isinstance(operation.parameter, str) and operation.parameter not in known_parameters:
            raise _workflow_error(
                "workflow.parameter.unknown",
                f"Unknown operation parameter '{operation.parameter}'.",
            )
    for measurement in measurements:
        if measurement.kind not in {"counts", "probabilities", "samples", "expectation"}:
            raise _workflow_error(
                "workflow.measurement.unsupported",
                f"Unsupported measurement request '{measurement.kind}'.",
            )


def _workflow_payload(workflow: ParameterizedWorkflow) -> dict[str, object]:
    return {
        "name": workflow.name,
        "n_qubits": workflow.n_qubits,
        "parameters": list(workflow.parameters),
        "parameter_bindings": workflow.parameter_bindings,
        "operations": [
            {
                "gate": operation.gate,
                "targets": list(operation.targets),
                "controls": list(operation.controls),
                "parameter": operation.parameter,
            }
            for operation in workflow.operations
        ],
        "measurements": [_measurement_payload(item) for item in workflow.measurements],
        "shots": workflow.shots,
        "seed": workflow.seed,
    }


def _measurement_payload(measurement: MeasurementRequest) -> dict[str, object]:
    payload: dict[str, object] = {"type": measurement.kind, "targets": list(measurement.targets)}
    if measurement.observable is not None:
        payload["observable"] = _hamiltonian_payload(measurement.observable)
    return payload


def _hamiltonian_payload(hamiltonian: PauliHamiltonian) -> dict[str, object]:
    return {
        "n_qubits": hamiltonian.n_qubits,
        "terms": [
            {
                "coefficient": term.coefficient,
                "paulis": {str(wire): pauli for wire, pauli in term.paulis},
            }
            for term in hamiltonian.terms
        ],
    }


def _emit_qiskit_workflow(workflow: ParameterizedWorkflow) -> str:
    lines = [
        "import json",
        "",
        "from qiskit import QuantumCircuit, transpile",
        "from qiskit.circuit import Parameter",
        "from qiskit_aer import AerSimulator",
        "from qiskit.quantum_info import SparsePauliOp",
        "",
        *[f"{parameter} = Parameter({parameter!r})" for parameter in workflow.parameters],
        f"circuit = QuantumCircuit({workflow.n_qubits}, {workflow.n_qubits})",
    ]
    lines.extend(_emit_qiskit_operations(workflow))
    if workflow.parameter_bindings:
        lines.append(f"parameter_bindings = {_python_dict(workflow.parameter_bindings)}")
        lines.append("bound_circuit = circuit.assign_parameters(parameter_bindings)")
    else:
        lines.append("bound_circuit = circuit")
    lines.extend(
        [
            f"shots = {workflow.shots}",
            "simulator = AerSimulator()",
            "compiled_circuit = transpile(bound_circuit, simulator)",
            "result = simulator.run(compiled_circuit, shots=shots).result()",
            "counts = result.get_counts()",
            "probabilities = {state: count / shots for state, count in counts.items()}",
        ]
    )
    lines.extend(_emit_qiskit_measurement_comments(workflow))
    lines.extend(_neutral_result_lines("qiskit_aer"))
    lines.extend(_workflow_spec_lines(workflow))
    lines.append("")
    return "\n".join(lines)


def _emit_qiskit_operations(workflow: ParameterizedWorkflow) -> list[str]:
    lines = []
    measured = False
    for operation in workflow.operations:
        gate = "cx" if operation.gate == "CNOT" else operation.gate.lower()
        if operation.gate in {"H", "X", "Y", "Z"}:
            lines.append(f"circuit.{gate}({operation.targets[0]})")
        elif operation.gate in {"RX", "RY", "RZ"}:
            lines.append(
                f"circuit.{gate}({_parameter_expr(operation.parameter)}, {operation.targets[0]})"
            )
        elif operation.gate in {"CNOT", "CX"}:
            control = operation.controls[0] if operation.controls else operation.targets[0]
            target = operation.targets[-1]
            lines.append(f"circuit.cx({control}, {target})")
        elif operation.gate == "MEASURE":
            measured = True
            lines.append(f"circuit.measure({operation.targets[0]}, {operation.targets[0]})")
    if not measured and any(item.kind in {"counts", "samples"} for item in workflow.measurements):
        lines.append("circuit.measure(range(circuit.num_qubits), range(circuit.num_qubits))")
    return lines


def _emit_qiskit_measurement_comments(workflow: ParameterizedWorkflow) -> list[str]:
    lines = []
    for index, request in enumerate(workflow.measurements):
        if request.kind == "expectation" and request.observable is not None:
            lines.append(
                f"observable_{index} = SparsePauliOp.from_list({_qiskit_pauli_terms(request.observable)})"
            )
            lines.append(
                f"# Evaluate observable_{index} with qiskit.quantum_info estimator tooling when available."
            )
        elif request.kind == "probabilities":
            lines.append(f"probability_targets_{index} = {list(request.targets)!r}")
    return lines


def _emit_cirq_workflow(workflow: ParameterizedWorkflow) -> str:
    lines = [
        "import json",
        "",
        "import cirq",
        "import sympy",
        "",
        f"qubits = cirq.LineQubit.range({workflow.n_qubits})",
        "circuit = cirq.Circuit()",
        *[f"{parameter} = sympy.Symbol({parameter!r})" for parameter in workflow.parameters],
    ]
    for operation in workflow.operations:
        lines.append(_cirq_operation_line(operation))
    if any(item.kind in {"counts", "samples"} for item in workflow.measurements):
        lines.append("circuit.append(cirq.measure(*qubits, key='m'))")
    lines.extend(
        [
            f"parameter_resolver = {_python_dict(workflow.parameter_bindings)}",
            f"shots = {workflow.shots}",
            "simulator = cirq.Simulator()",
            "result = simulator.run(circuit, repetitions=shots, param_resolver=parameter_resolver)",
            "histogram = result.histogram(key='m') if 'm' in result.measurements else {}",
            f"counts = {{format(key, '0{workflow.n_qubits}b'): value for key, value in histogram.items()}}",
            "probabilities = {state: count / shots for state, count in counts.items()}",
        ]
    )
    lines.extend(_emit_cirq_measurement_comments(workflow))
    lines.extend(_neutral_result_lines("cirq"))
    lines.extend(_workflow_spec_lines(workflow))
    lines.append("")
    return "\n".join(lines)


def _cirq_operation_line(operation: WorkflowOperation) -> str:
    target = operation.targets[0]
    if operation.gate in {"H", "X", "Y", "Z"}:
        return f"circuit.append(cirq.{operation.gate}(qubits[{target}]))"
    if operation.gate in {"RX", "RY", "RZ"}:
        axis = operation.gate[-1].lower()
        return f"circuit.append(cirq.r{axis}({_parameter_expr(operation.parameter)})(qubits[{target}]))"
    if operation.gate in {"CNOT", "CX"}:
        control = operation.controls[0] if operation.controls else operation.targets[0]
        target = operation.targets[-1]
        return f"circuit.append(cirq.CNOT(qubits[{control}], qubits[{target}]))"
    if operation.gate == "MEASURE":
        return f"circuit.append(cirq.measure(qubits[{target}], key='m{target}'))"
    raise AssertionError(operation.gate)


def _emit_cirq_measurement_comments(workflow: ParameterizedWorkflow) -> list[str]:
    lines = []
    for index, request in enumerate(workflow.measurements):
        if request.kind == "expectation" and request.observable is not None:
            lines.append(f"observable_{index} = {_cirq_observable_expr(request.observable)}")
            lines.append(
                f"# simulator.simulate_expectation_values can evaluate observable_{index}."
            )
        elif request.kind == "probabilities":
            lines.append(f"probability_targets_{index} = {list(request.targets)!r}")
    return lines


def _emit_pennylane_workflow(workflow: ParameterizedWorkflow) -> str:
    args = ", ".join(
        f"{parameter}=parameter_bindings[{parameter!r}]" for parameter in workflow.parameters
    )
    lines = [
        "import json",
        "",
        "import pennylane as qml",
        "",
        f"shots = {workflow.shots}",
        f"parameter_bindings = {_python_dict(workflow.parameter_bindings)}",
        f"dev = qml.device('default.qubit', wires={workflow.n_qubits}, shots=shots)",
        "",
        "@qml.qnode(dev)",
        f"def circuit({args}):",
    ]
    lines.extend(_emit_pennylane_operations(workflow))
    lines.append(f"    return {_pennylane_return_expr(workflow)}")
    lines.extend(
        [
            "",
            "raw_result = circuit()",
            "counts = {}",
            "probabilities = {}",
        ]
    )
    lines.extend(_neutral_result_lines("pennylane"))
    lines.extend(_workflow_spec_lines(workflow))
    lines.append("")
    return "\n".join(lines)


def _emit_pennylane_operations(workflow: ParameterizedWorkflow) -> list[str]:
    lines = []
    for operation in workflow.operations:
        target = operation.targets[0]
        if operation.gate in {"H", "X", "Y", "Z"}:
            names = {"H": "Hadamard", "X": "PauliX", "Y": "PauliY", "Z": "PauliZ"}
            lines.append(f"    qml.{names[operation.gate]}(wires={target})")
        elif operation.gate in {"RX", "RY", "RZ"}:
            lines.append(
                f"    qml.{operation.gate}({_parameter_expr(operation.parameter)}, wires={target})"
            )
        elif operation.gate in {"CNOT", "CX"}:
            control = operation.controls[0] if operation.controls else operation.targets[0]
            target = operation.targets[-1]
            lines.append(f"    qml.CNOT(wires=[{control}, {target}])")
    return lines or ["    pass"]


def _pennylane_return_expr(workflow: ParameterizedWorkflow) -> str:
    requests = workflow.measurements or (
        MeasurementRequest("samples", tuple(range(workflow.n_qubits))),
    )
    expressions = []
    for request in requests:
        if request.kind == "expectation" and request.observable is not None:
            expressions.append(f"qml.expval({_pennylane_hamiltonian_expr(request.observable)})")
        elif request.kind == "probabilities":
            expressions.append(f"qml.probs(wires={list(request.targets)!r})")
        else:
            expressions.append(f"qml.sample(wires={list(request.targets)!r})")
    return expressions[0] if len(expressions) == 1 else "(" + ", ".join(expressions) + ")"


def _emit_braket_workflow(workflow: ParameterizedWorkflow) -> str:
    lines = [
        "import json",
        "",
        "from braket.circuits import Circuit, FreeParameter, Observable",
        "from braket.devices import LocalSimulator",
        "",
        *[f"{parameter} = FreeParameter({parameter!r})" for parameter in workflow.parameters],
        "circuit = Circuit()",
    ]
    for operation in workflow.operations:
        lines.append(_braket_operation_line(operation))
    for request in workflow.measurements:
        if request.kind == "probabilities":
            lines.append(f"circuit.probability(target={list(request.targets)!r})")
        elif request.kind == "expectation" and request.observable is not None:
            for term_index, term in enumerate(request.observable.terms):
                observable, targets = _braket_term_expr(term)
                lines.append(f"expectation_observable_{term_index} = {observable}")
                lines.append(
                    f"circuit.expectation(observable=expectation_observable_{term_index}, target={targets!r})"
                )
    lines.extend(
        [
            f"inputs = {_python_dict(workflow.parameter_bindings)}",
            f"shots = {workflow.shots}",
            "device = LocalSimulator()",
            "task = device.run(circuit, shots=shots, inputs=inputs)",
            "result = task.result()",
            "counts = dict(result.measurement_counts)",
            "probabilities = {state: count / shots for state, count in counts.items()}",
        ]
    )
    lines.extend(_neutral_result_lines("braket_local"))
    lines.extend(_workflow_spec_lines(workflow))
    lines.append("")
    return "\n".join(lines)


def _braket_operation_line(operation: WorkflowOperation) -> str:
    target = operation.targets[0]
    if operation.gate in {"H", "X", "Y", "Z"}:
        return f"circuit.{operation.gate.lower()}({target})"
    if operation.gate in {"RX", "RY", "RZ"}:
        return f"circuit.{operation.gate.lower()}({target}, {_parameter_expr(operation.parameter)})"
    if operation.gate in {"CNOT", "CX"}:
        control = operation.controls[0] if operation.controls else operation.targets[0]
        target = operation.targets[-1]
        return f"circuit.cnot({control}, {target})"
    if operation.gate == "MEASURE":
        return f"# Braket samples all measured qubits; requested measurement target: {target}"
    raise AssertionError(operation.gate)


def _neutral_result_lines(source_format: str) -> list[str]:
    return [
        "neutral_result = {",
        "    'counts': counts,",
        "    'shots': shots,",
        "    'probabilities': probabilities,",
        "    'expectations': {},",
        f"    'metadata': {{'source_format': {source_format!r}}},",
        "}",
        "print(json.dumps(neutral_result, indent=2, sort_keys=True))",
    ]


def _workflow_spec_lines(workflow: ParameterizedWorkflow) -> list[str]:
    payload = json.dumps(_workflow_payload(workflow), indent=2, sort_keys=True)
    return ["", 'workflow_spec = json.loads("""', payload, '""")']


def _parameter_expr(value: str | float | None) -> str:
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return value
    raise AssertionError("parameter expression required")


def _python_dict(values: dict[str, float]) -> str:
    return "{" + ", ".join(f"{key!r}: {value!r}" for key, value in sorted(values.items())) + "}"


def _qiskit_pauli_terms(hamiltonian: PauliHamiltonian) -> str:
    terms = []
    for term in hamiltonian.terms:
        paulis = ["I"] * hamiltonian.n_qubits
        for wire, pauli in term.paulis:
            paulis[hamiltonian.n_qubits - wire - 1] = pauli
        terms.append(("".join(paulis), float(term.coefficient)))
    return repr(terms)


def _cirq_observable_expr(hamiltonian: PauliHamiltonian) -> str:
    parts = []
    for term in hamiltonian.terms:
        factors = [f"cirq.{pauli}(qubits[{wire}])" for wire, pauli in term.paulis if pauli != "I"]
        product = " * ".join(factors) if factors else "1"
        parts.append(f"{term.coefficient!r} * {product}")
    return " + ".join(parts) if parts else "0"


def _pennylane_hamiltonian_expr(hamiltonian: PauliHamiltonian) -> str:
    coeffs = [float(term.coefficient) for term in hamiltonian.terms]
    observables = []
    names = {"X": "PauliX", "Y": "PauliY", "Z": "PauliZ", "I": "Identity"}
    for term in hamiltonian.terms:
        factors = [f"qml.{names[pauli]}({wire})" for wire, pauli in term.paulis]
        observables.append(" @ ".join(factors) if factors else "qml.Identity(0)")
    return f"qml.Hamiltonian({coeffs!r}, [{', '.join(observables)}])"


def _braket_term_expr(term: PauliTerm) -> tuple[str, list[int]]:
    factors = []
    targets = []
    for wire, pauli in term.paulis:
        if pauli == "I":
            continue
        factors.append(f"Observable.{pauli}()")
        targets.append(wire)
    return " @ ".join(factors) if factors else "Observable.I()", targets


def _counts_payload_for_format(payload: dict[str, Any], from_format: str) -> object:
    if from_format == "braket-counts-json":
        return payload.get("measurement_counts", payload.get("counts", payload))
    return payload.get("counts", payload)


def _result_metadata(payload: dict[str, Any], from_format: str) -> dict[str, object]:
    metadata: dict[str, object] = {"source_format": from_format}
    for key in ("measurement_key", "measurement_keys", "result_type", "backend"):
        if key in payload:
            metadata[key] = payload[key]
    return metadata


def _counts_from_mapping(payload: object) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise _workflow_error("result.counts", "Counts payload must be an object.")
    return {str(key).replace(" ", ""): int(value) for key, value in payload.items()}


def _counts_from_samples(samples: object) -> dict[str, int]:
    if not isinstance(samples, list):
        raise _workflow_error("result.samples", "PennyLane sample payload must be a list.")
    counter: Counter[str] = Counter()
    for sample in samples:
        if isinstance(sample, list):
            counter["".join(str(int(bit)) for bit in sample)] += 1
        else:
            counter[str(int(sample))] += 1
    return dict(sorted(counter.items()))


def _probabilities_from_payload(
    payload: object, counts: dict[str, int], shots: int
) -> dict[str, float]:
    if payload is None:
        return _counts_to_probabilities(counts, shots)
    if not isinstance(payload, dict):
        raise _workflow_error("result.probabilities", "Probabilities payload must be an object.")
    return {str(key).replace(" ", ""): float(value) for key, value in payload.items()}


def _counts_to_probabilities(counts: dict[str, int], shots: int) -> dict[str, float]:
    if shots <= 0:
        return {}
    return {state: count / shots for state, count in sorted(counts.items())}


def _result_payload(result: NeutralResult) -> dict[str, object]:
    return {
        "counts": dict(sorted(result.counts.items())),
        "shots": result.shots,
        "probabilities": dict(sorted(result.probabilities.items())),
        "expectations": dict(sorted(result.expectations.items())),
        "metadata": result.metadata,
    }


def _qubit_wise_compatible(left: dict[int, str], right: dict[int, str]) -> bool:
    for wire, pauli in right.items():
        existing = left.get(wire)
        if existing is not None and existing != pauli:
            return False
    return True


def _grouping_payload(groups: list[PauliHamiltonian]) -> dict[str, object]:
    return {
        "strategy": "qubit-wise",
        "group_count": len(groups),
        "groups": [
            {
                "index": index,
                "term_count": len(group.terms),
                "canonical": canonical_hamiltonian(group),
                "hamiltonian": _hamiltonian_payload(group),
            }
            for index, group in enumerate(groups)
        ],
    }


def _import_static_workflow_source(source: str, from_format: str) -> ParameterizedWorkflow:
    tree = ast.parse(source)
    spec = _workflow_spec_from_ast(tree)
    if spec is not None:
        return _workflow_from_payload(spec)
    if from_format == "qiskit":
        return _import_qiskit_workflow_ast(tree)
    if from_format == "cirq":
        return _import_cirq_workflow_ast(tree)
    if from_format == "pennylane":
        return _import_pennylane_workflow_ast(tree)
    if from_format == "braket":
        return _import_braket_workflow_ast(tree)
    raise _workflow_error(
        "workflow.import.unsupported", f"Unsupported workflow input format '{from_format}'."
    )


def _workflow_spec_from_ast(tree: ast.AST) -> dict[str, Any] | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "workflow_spec"
                for target in node.targets
            ):
                if isinstance(node.value, ast.Call) and _is_json_loads_call(node.value):
                    value = json.loads(ast.literal_eval(node.value.args[0]))
                else:
                    value = ast.literal_eval(node.value)
                if not isinstance(value, dict):
                    raise _workflow_error("workflow.spec", "workflow_spec must be a dictionary.")
                return value
    return None


def _is_json_loads_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "json"
        and node.func.attr == "loads"
        and bool(node.args)
    )


def _import_qiskit_workflow_ast(tree: ast.AST) -> ParameterizedWorkflow:
    return _workflow_from_static_ast(
        tree,
        sdk="qiskit",
        circuit_methods={
            "h": "H",
            "x": "X",
            "y": "Y",
            "z": "Z",
            "rx": "RX",
            "ry": "RY",
            "rz": "RZ",
            "cx": "CNOT",
            "measure": "MEASURE",
        },
        binding_names=("parameter_bindings",),
    )


def _import_cirq_workflow_ast(tree: ast.AST) -> ParameterizedWorkflow:
    return _workflow_from_static_ast(
        tree,
        sdk="cirq",
        circuit_methods={},
        binding_names=("parameter_resolver",),
    )


def _import_pennylane_workflow_ast(tree: ast.AST) -> ParameterizedWorkflow:
    return _workflow_from_static_ast(
        tree,
        sdk="pennylane",
        circuit_methods={},
        binding_names=("parameter_bindings",),
    )


def _import_braket_workflow_ast(tree: ast.AST) -> ParameterizedWorkflow:
    return _workflow_from_static_ast(
        tree,
        sdk="braket",
        circuit_methods={
            "h": "H",
            "x": "X",
            "y": "Y",
            "z": "Z",
            "rx": "RX",
            "ry": "RY",
            "rz": "RZ",
            "cnot": "CNOT",
        },
        binding_names=("inputs",),
    )


def _workflow_from_static_ast(
    tree: ast.AST,
    *,
    sdk: str,
    circuit_methods: dict[str, str],
    binding_names: tuple[str, ...],
) -> ParameterizedWorkflow:
    parameters = _static_parameters(tree, sdk)
    bindings = _static_bindings(tree, binding_names)
    n_qubits = _static_n_qubits(tree, sdk)
    shots = _static_shots(tree, sdk)
    operations: list[WorkflowOperation] = []
    measurements: list[MeasurementRequest] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            operation = _static_operation(node, sdk, circuit_methods)
            if operation is not None:
                if operation.gate == "MEASURE":
                    measurements.append(MeasurementRequest("counts", tuple(range(n_qubits))))
                else:
                    operations.append(operation)
            request = _static_measurement_request(node, sdk, n_qubits)
            if request is not None:
                measurements.append(request)
    if not measurements:
        measurements.append(MeasurementRequest("counts", tuple(range(n_qubits))))
    return ParameterizedWorkflow(
        f"imported_{sdk}_workflow",
        n_qubits,
        tuple(parameters),
        tuple(operations),
        bindings,
        tuple(_dedupe_measurements(measurements)),
        shots,
        None,
    )


def _static_parameters(tree: ast.AST, sdk: str) -> list[str]:
    factory_names = {"qiskit": "Parameter", "cirq": "Symbol", "braket": "FreeParameter"}
    if sdk == "pennylane":
        return _pennylane_function_parameters(tree)
    names = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        func_name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr if isinstance(func, ast.Attribute) else ""
        )
        if func_name == factory_names[sdk]:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
    return sorted(set(names))


def _pennylane_function_parameters(tree: ast.AST) -> list[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return [arg.arg for arg in node.args.args]
    return []


def _static_bindings(tree: ast.AST, names: tuple[str, ...]) -> dict[str, float]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in names for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return {str(key): float(item) for key, item in value.items()}
    return {}


def _static_n_qubits(tree: ast.AST, sdk: str) -> int:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr if isinstance(func, ast.Attribute) else ""
        )
        if sdk == "qiskit" and name == "QuantumCircuit" and node.args:
            return int(ast.literal_eval(node.args[0]))
        if sdk == "cirq" and name == "range" and node.args:
            return int(ast.literal_eval(node.args[0]))
        if sdk == "pennylane" and name == "device":
            for keyword in node.keywords:
                if keyword.arg == "wires":
                    return int(ast.literal_eval(keyword.value))
    return _max_wire_index(tree) + 1


def _static_shots(tree: ast.AST, sdk: str) -> int:
    assigned = _static_int_assignment(tree, "shots", 1024)
    if assigned != 1024 or sdk != "pennylane":
        return assigned
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr if isinstance(func, ast.Attribute) else ""
        )
        if name == "device":
            for keyword in node.keywords:
                if keyword.arg == "shots":
                    return int(ast.literal_eval(keyword.value))
    return assigned


def _static_int_assignment(tree: ast.AST, name: str, default: int) -> int:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            try:
                return int(ast.literal_eval(node.value))
            except (ValueError, TypeError):
                return default
    return default


def _static_operation(
    node: ast.Call, sdk: str, circuit_methods: dict[str, str]
) -> WorkflowOperation | None:
    if (
        sdk == "qiskit"
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in circuit_methods
    ):
        gate = circuit_methods[node.func.attr]
        return _operation_from_method_call(gate, node.args)
    if (
        sdk == "braket"
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in circuit_methods
    ):
        gate = circuit_methods[node.func.attr]
        return _operation_from_method_call(gate, node.args)
    if sdk == "cirq":
        return _cirq_static_operation(node)
    if sdk == "pennylane":
        return _pennylane_static_operation(node)
    return None


def _operation_from_method_call(gate: str, args: list[ast.expr]) -> WorkflowOperation | None:
    if gate in {"H", "X", "Y", "Z"} and args:
        return WorkflowOperation(gate, (_wire_index(args[0]),))
    if gate in {"RX", "RY", "RZ"} and len(args) >= 2:
        first = _expr_name_or_float(args[0])
        second = _expr_name_or_float(args[1])
        if isinstance(first, int | float):
            return WorkflowOperation(gate, (int(first),), parameter=second)
        return WorkflowOperation(gate, (_wire_index(args[1]),), parameter=first)
    if gate == "CNOT" and len(args) >= 2:
        return WorkflowOperation("CNOT", (_wire_index(args[1]),), (_wire_index(args[0]),))
    if gate == "MEASURE" and args:
        return WorkflowOperation("MEASURE", (_wire_index(args[0]),))
    return None


def _cirq_static_operation(node: ast.Call) -> WorkflowOperation | None:
    text = ast.unparse(node)
    if isinstance(node.func, ast.Attribute):
        for gate in ("H", "X", "Y", "Z"):
            if node.func.attr == gate and node.args:
                return WorkflowOperation(gate, (_wire_index(node.args[0]),))
        if node.func.attr == "CNOT" and len(node.args) >= 2:
            return WorkflowOperation(
                "CNOT", (_wire_index(node.args[1]),), (_wire_index(node.args[0]),)
            )
        if node.func.attr == "measure" and node.args:
            return WorkflowOperation("MEASURE", (_wire_index(node.args[0]),))
    if isinstance(node.func, ast.Call) and isinstance(node.func.func, ast.Attribute):
        gate = node.func.func.attr
        if gate in {"rx", "ry", "rz"} and node.args:
            parameter = (
                _expr_name_or_float(node.func.args[0]) if node.func.args else ast.unparse(node.func)
            )
            return WorkflowOperation(
                gate.upper(), (_wire_index(node.args[0]),), parameter=parameter
            )
    if "cirq.CNOT(" in text:
        wires = _wire_indexes_from_text(text)
        if len(wires) >= 2:
            return WorkflowOperation("CNOT", (wires[1],), (wires[0],))
    return None


def _pennylane_static_operation(node: ast.Call) -> WorkflowOperation | None:
    if not isinstance(node.func, ast.Attribute):
        return None
    mapping = {
        "Hadamard": "H",
        "PauliX": "X",
        "PauliY": "Y",
        "PauliZ": "Z",
        "RX": "RX",
        "RY": "RY",
        "RZ": "RZ",
        "CNOT": "CNOT",
    }
    gate = mapping.get(node.func.attr)
    if gate is None:
        return None
    wires = _keyword_wires(node)
    if gate == "CNOT" and len(wires) >= 2:
        return WorkflowOperation("CNOT", (wires[1],), (wires[0],))
    if gate in {"RX", "RY", "RZ"}:
        parameter = _expr_name_or_float(node.args[0]) if node.args else None
        return WorkflowOperation(gate, (wires[0],), parameter=parameter)
    return WorkflowOperation(gate, (wires[0],))


def _static_measurement_request(
    node: ast.Call, sdk: str, n_qubits: int
) -> MeasurementRequest | None:
    text = ast.unparse(node)
    if sdk == "pennylane" and "qml.probs" in text:
        return MeasurementRequest("probabilities", tuple(_keyword_wires(node) or range(n_qubits)))
    if sdk == "pennylane" and "qml.sample" in text:
        return MeasurementRequest("samples", tuple(_keyword_wires(node) or range(n_qubits)))
    if sdk == "braket" and isinstance(node.func, ast.Attribute) and node.func.attr == "probability":
        return MeasurementRequest("probabilities", tuple(_keyword_target(node) or range(n_qubits)))
    return None


def _dedupe_measurements(measurements: list[MeasurementRequest]) -> list[MeasurementRequest]:
    output = []
    seen = set()
    for measurement in measurements:
        key = (
            measurement.kind,
            measurement.targets,
            (
                canonical_hamiltonian(measurement.observable)
                if measurement.observable is not None
                else None
            ),
        )
        if key not in seen:
            seen.add(key)
            output.append(measurement)
    return output


def _expr_name_or_float(node: ast.expr) -> str | float:
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        if isinstance(node, ast.Name):
            return node.id
        return ast.unparse(node)
    return float(value) if isinstance(value, int | float) else str(value)


def _wire_index(node: ast.expr) -> int:
    if isinstance(node, ast.Subscript):
        return int(ast.literal_eval(node.slice))
    return int(ast.literal_eval(node))


def _keyword_wires(node: ast.Call) -> list[int]:
    for keyword in node.keywords:
        if keyword.arg == "wires":
            value = ast.literal_eval(keyword.value)
            if isinstance(value, list):
                return [int(item) for item in value]
            return [int(value)]
    return []


def _keyword_target(node: ast.Call) -> list[int]:
    for keyword in node.keywords:
        if keyword.arg == "target":
            value = ast.literal_eval(keyword.value)
            if isinstance(value, list):
                return [int(item) for item in value]
            return [int(value)]
    return []


def _max_wire_index(tree: ast.AST) -> int:
    wires = _wire_indexes_from_text(ast.unparse(tree))
    return max(wires) if wires else 0


def _wire_indexes_from_text(text: str) -> list[int]:
    import re

    return [int(item) for item in re.findall(r"\[(\d+)\]", text)] + [
        int(item) for item in re.findall(r"\((\d+)(?:,|\))", text)
    ]


def _first_wire_from_text(text: str) -> int:
    wires = _wire_indexes_from_text(text)
    return wires[0] if wires else 0


def _last_wire_from_text(text: str) -> int:
    wires = _wire_indexes_from_text(text)
    return wires[-1] if wires else 0


def _first_call_arg_name(node: ast.Call) -> str | float:
    if node.args:
        return _expr_name_or_float(node.args[0])
    return ast.unparse(node)


def _workflow_error(code: str, message: str) -> TranslationError:
    return TranslationError([TranslationDiagnostic("error", code, message)])
