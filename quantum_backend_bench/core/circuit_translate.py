"""Circuit translation helpers for supported local quantum SDK snippets."""

from __future__ import annotations

import ast
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
from quantum_backend_bench.core.neutral_circuit import (
    internal_circuit_from_json,
    internal_circuit_to_json,
)
from quantum_backend_bench.core.neutral_schema import (
    report_schema_metadata,
)

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
TRANSLATION_VERIFY_MODES = ("none", "exact", "samples", "canonical", "statevector")

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
    canonical_match: bool | None = None
    statevector_distance: float | None = None
    expectation_max_abs_error: float | None = None
    expectation_tolerance: float | None = None
    result_schema_valid: bool | None = None


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


def translation_semantic_contract(
    layer: str = "circuit",
    *,
    from_format: str | None = None,
    to_format: str | None = None,
) -> dict[str, object]:
    """Return the explicit semantic contract for a translation layer."""

    base: dict[str, object] = {
        "guarantee": "Lossless only within the declared neutral semantic subset.",
        "lossless_subset": True,
        "input_format": from_format,
        "output_format": to_format,
        "free_local_targets": list(FREE_LOCAL_TRANSLATION_SDKS),
    }
    if layer == "circuit":
        base.update(
            {
                "layer": "circuit",
                "preserved": [
                    "supported gate sequence",
                    "integer-wire operation targets",
                    "named quantum/classical register offsets where imported",
                    "measurement keys and declared bit ordering where available",
                    "global phase metadata",
                    "static numeric rotation parameters",
                    "static computational-basis measurements",
                    "reset, barrier, and delay annotations where target SDKs can preserve them",
                    "neutral local noise-channel annotations",
                ],
                "rewritten": [
                    "SDK syntax and imports",
                    "register names mapped to neutral integer-wire offsets",
                    "measurement bitstrings normalized for verification",
                    "neutral noise channels mapped to supported local SDK noise syntax",
                ],
                "rejected": [
                    "dynamic Python circuit construction",
                    "custom or opaque gates outside the supported neutral gate set",
                    "classical control",
                    "provider/runtime calls",
                    "transpiler settings",
                    "arbitrary result-processing code",
                ],
                "not_modeled": [
                    "hardware/provider execution semantics",
                    "full Python program behavior",
                    "provider-specific noise calibration semantics",
                    "pulse-level controls",
                ],
                "verification": [
                    "canonical neutral structure",
                    "exact probabilities",
                    "sampled distributions",
                    "statevector comparison up to global phase for small noiseless circuits",
                ],
            }
        )
    elif layer == "pauli_hamiltonian":
        base.update(
            {
                "layer": "pauli_hamiltonian",
                "preserved": [
                    "weighted sums of Pauli I/X/Y/Z products",
                    "neutral qubit-indexed Pauli terms",
                    "numeric coefficients",
                ],
                "rewritten": ["SDK-specific observable syntax", "wire-order display conventions"],
                "rejected": [
                    "non-Pauli operator algebra",
                    "symbolic coefficients",
                    "dynamic Hamiltonian construction",
                ],
                "not_modeled": [
                    "fermionic operators",
                    "time-dependent coefficients",
                    "noise models",
                ],
                "verification": ["canonical Pauli terms", "small dense matrices"],
            }
        )
    elif layer == "workflow":
        base.update(
            {
                "layer": "workflow",
                "preserved": [
                    "supported parameterized circuit operations",
                    "symbolic parameter names and numeric bindings",
                    "measurement and expectation requests",
                    "local shot-count execution settings",
                    "neutral result extraction shape",
                ],
                "rewritten": [
                    "SDK parameter APIs",
                    "local execution wrapper code",
                    "SDK result object access",
                ],
                "rejected": [
                    "arbitrary workflow Python",
                    "provider/runtime services",
                    "unsupported dynamic parameter or wire construction",
                ],
                "not_modeled": ["cloud execution", "optimizer loops", "full application state"],
                "verification": [
                    "canonical workflow reimport",
                    "exact neutral measurement-distribution TVD",
                    "exact Pauli expectation-value comparison",
                    "neutral result-schema and cross-field validation",
                ],
            }
        )
    elif layer == "result":
        base.update(
            {
                "layer": "result",
                "preserved": ["counts", "shots", "probabilities", "expectations", "metadata"],
                "rewritten": ["SDK-specific count/sample payloads normalized to result-json"],
                "rejected": ["non-JSON SDK result objects", "arbitrary post-processing code"],
                "not_modeled": [
                    "backend job lifecycle",
                    "raw provider metadata outside known fields",
                ],
                "verification": [
                    "result schema version and field types",
                    "shot totals and probability normalization",
                    "count/probability cross-field consistency",
                ],
            }
        )
    elif layer == "measurement_grouping":
        base.update(
            {
                "layer": "measurement_grouping",
                "preserved": ["weighted Pauli I/X/Y/Z terms", "qubit-wise commuting groups"],
                "rewritten": ["term ordering within neutral grouping output"],
                "rejected": ["non-Pauli observables", "non-qubit-wise grouping strategies"],
                "not_modeled": ["hardware-specific readout mitigation", "device topology costs"],
                "verification": ["canonical Pauli-term grouping payloads"],
            }
        )
    else:
        raise ValueError(f"Unknown translation contract layer: {layer}")
    return base


def circuit_migration_audit(
    benchmark: BenchmarkSpec,
    detected_format: str,
    *,
    to_format: str | None = None,
) -> dict[str, object]:
    """Return target-aware migration guidance for a supported circuit source."""

    if to_format is not None and to_format not in TRANSLATION_OUTPUT_FORMATS:
        available = ", ".join(TRANSLATION_OUTPUT_FORMATS)
        raise ValueError(f"Unknown output format '{to_format}'. Available: {available}")
    circuit = _internal_circuit(benchmark)
    gate_counts: dict[str, int] = {}
    for operation in circuit.operations:
        gate_counts[operation.gate] = gate_counts.get(operation.gate, 0) + 1
    status = "source_supported" if to_format is None else "target_supported"
    return {
        "status": status,
        "input_format": detected_format,
        "target": to_format,
        "operation_count": len(circuit.operations),
        "measurements": list(circuit.measurements),
        "gate_counts": dict(sorted(gate_counts.items())),
        "preserved": [
            "supported gates and operation order",
            "static measurement targets",
            "numeric rotation and phase parameters",
            "named register offset metadata",
            "measurement-key and bit-order metadata",
            "global phase metadata",
            "reset, barrier, and delay annotations where preservable",
            "neutral noise-channel annotations",
        ],
        "rewritten": [
            "SDK imports and construction syntax",
            "wire/register names into neutral integer-wire semantics",
            "neutral noise channels into SDK-local noise syntax when emitted",
            "non-native annotations into explicit neutral comments plus diagnostics",
        ],
        "rejected_if_present": [
            "dynamic Python control flow",
            "custom gates",
            "classical control",
            "provider/runtime calls",
            "transpiler settings",
            "arbitrary result processing",
        ],
        "not_modeled": [
            "cloud execution behavior",
            "provider-calibrated noise semantics",
            "full Python program state",
        ],
        "verification_recommendation": "Run translate with --verify exact for deterministic circuit semantics or --verify samples for sampled workflows.",
    }


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
        "schema_metadata": report_schema_metadata(from_format=from_format, to_format=to_format),
        "semantic_contract": translation_semantic_contract(
            "circuit", from_format=from_format, to_format=to_format
        ),
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
    to_format: str | None = None,
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
        "schema_metadata": report_schema_metadata(from_format=detected_format, to_format=to_format),
        "semantic_contract": translation_semantic_contract(
            "circuit", from_format=detected_format, to_format=to_format
        ),
        "migration_audit": circuit_migration_audit(benchmark, detected_format, to_format=to_format),
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
        "schema_metadata": report_schema_metadata(from_format=from_format),
        "semantic_contract": translation_semantic_contract("circuit", from_format=from_format),
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
        "canonical_match": verification.canonical_match,
        "statevector_distance": verification.statevector_distance,
        "expectation_max_abs_error": verification.expectation_max_abs_error,
        "expectation_tolerance": verification.expectation_tolerance,
        "result_schema_valid": verification.result_schema_valid,
    }


def _caveat_diagnostics() -> list[TranslationDiagnostic]:
    from quantum_backend_bench.core.translation_adapters import circuit_adapter_diagnostics

    adapter_diagnostics = circuit_adapter_diagnostics()
    return [
        TranslationDiagnostic(
            "warning",
            "translation.caveat.measurement_order",
            "SDKs may display measurement bitstrings with different endian conventions; verification compares neutral measurement probabilities.",
        ),
        *[
            diagnostic
            for diagnostic in adapter_diagnostics
            if isinstance(diagnostic, TranslationDiagnostic)
        ],
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
            "Static circuit translation preserves supported gates, measurements, and supported neutral annotations.",
        ),
        *_annotation_diagnostics(_internal_circuit(benchmark), to_format),
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
    if to_format in FREE_LOCAL_TRANSLATION_SDKS:
        from quantum_backend_bench.core.translation_adapters import circuit_adapter_for_output

        return circuit_adapter_for_output(to_format).emit(
            circuit, include_runner=include_runner, runner_shots=runner_shots
        )
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

    if mode not in {"exact", "samples", "canonical", "statevector"}:
        raise ValueError(
            "Verification mode must be 'exact', 'samples', 'canonical', or 'statevector'."
        )
    imported, _ = import_circuit_source(
        translated_source,
        from_format=_OUTPUT_IMPORT_FORMAT[to_format],
        name=f"{original.name}_translated",
    )
    if mode == "canonical":
        original_signature = canonical_circuit_signature(original)
        translated_signature = canonical_circuit_signature(imported)
        passed = original_signature == translated_signature
        status = "passed" if passed else "failed"
        return TranslationVerification(
            mode=mode,
            passed=passed,
            total_variation_distance=None,
            tolerance=tolerance,
            details=f"Canonical neutral structure verification {status}.",
            canonical_match=passed,
        )
    if mode == "statevector":
        distance = statevector_distance_up_to_global_phase(original, imported)
        passed = distance <= tolerance
        status = "passed" if passed else "failed"
        return TranslationVerification(
            mode=mode,
            passed=passed,
            total_variation_distance=None,
            tolerance=tolerance,
            details=(
                f"Statevector verification {status}: distance={distance} "
                f"with tolerance={tolerance}."
            ),
            statevector_distance=distance,
        )
    original_probs = exact_probabilities(original)
    translated_probs = exact_probabilities(imported)
    if mode == "samples":
        from quantum_backend_bench.core.neutral_simulator import sample_counts

        original_counts = sample_counts(original_probs, shots=sample_shots, seed=0)
        translated_counts = sample_counts(translated_probs, shots=sample_shots, seed=0)
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


def canonical_circuit_signature(benchmark: BenchmarkSpec) -> dict[str, object]:
    """Return a stable neutral circuit signature for structure-preserving checks."""

    circuit = _internal_circuit(benchmark)
    return {
        "n_qubits": circuit.n_qubits,
        "operations": [
            {
                "gate": operation.gate,
                "qubits": list(operation.qubits),
                "params": _canonical_params(operation.params),
            }
            for operation in circuit.operations
        ],
        "measurements": list(circuit.measurements),
        "global_phase": round(circuit.global_phase, 12),
        "noise": [
            {
                "channel": item.channel,
                "targets": list(item.targets),
                "probability": round(item.probability, 12),
            }
            for item in circuit.noise
        ],
    }


def statevector_distance_up_to_global_phase(
    original: BenchmarkSpec, translated: BenchmarkSpec
) -> float:
    """Return L2 statevector distance after optimal global-phase alignment."""

    from quantum_backend_bench.core.exact import _statevector

    original_circuit = _internal_circuit(original)
    translated_circuit = _internal_circuit(translated)
    if original_circuit.noise or translated_circuit.noise:
        raise ValueError("Statevector verification does not support noisy neutral annotations.")
    if any(
        operation.gate == "RESET"
        for operation in [*original_circuit.operations, *translated_circuit.operations]
    ):
        raise ValueError("Statevector verification does not support RESET annotations.")
    if original_circuit.n_qubits != translated_circuit.n_qubits:
        return float("inf")
    np = __import__("numpy")
    left = _statevector(original)
    right = _statevector(translated)
    overlap = np.vdot(left, right)
    if abs(overlap) > 1e-15:
        right = right * (overlap / abs(overlap)).conjugate()
    return float(np.linalg.norm(left - right))


def _canonical_params(params: dict[str, object]) -> dict[str, object]:
    canonical: dict[str, object] = {}
    for key, value in sorted(params.items()):
        if isinstance(value, float):
            canonical[key] = round(value, 12)
        else:
            canonical[key] = value
    return canonical


def _annotation_diagnostics(
    circuit: InternalCircuit, to_format: str
) -> list[TranslationDiagnostic]:
    annotation_gates = {operation.gate for operation in circuit.operations} & {
        "RESET",
        "BARRIER",
        "DELAY",
    }
    native_support = {
        "internal-json": {"RESET", "BARRIER", "DELAY"},
        "openqasm": {"RESET", "BARRIER", "DELAY"},
        "qiskit_aer": {"RESET", "BARRIER", "DELAY"},
        "cirq": {"RESET"},
        "pennylane": {"BARRIER"},
        "braket_local": set(),
    }
    unsupported = annotation_gates - native_support.get(to_format, set())
    if not unsupported:
        return []
    return [
        TranslationDiagnostic(
            "warning",
            f"translation.annotation.{gate.lower()}",
            (
                f"{to_format} output represents neutral {gate.lower()} annotations "
                "as explicit comments when no matching local SDK primitive is emitted."
            ),
        )
        for gate in sorted(unsupported)
    ]


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
    circuit = internal_circuit_from_json(source)
    return BenchmarkSpec(
        name=name,
        n_qubits=circuit.n_qubits,
        parameters={"source": "internal-json"},
        circuit_data=circuit,
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
    from quantum_backend_bench.core.translation_adapters import circuit_adapter_for_input

    circuit = circuit_adapter_for_input(sdk).parse_ast(tree)
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
    register_sizes: dict[str, int] = {}
    classical_register_sizes: dict[str, int] = {}
    register_offsets: dict[str, tuple[int, int]] = {}
    classical_offsets: dict[str, tuple[int, int]] = {}
    circuit_vars: dict[str, int] = {}
    operations: list[CircuitOperation] = []
    measurements: list[int] = []
    measurement_keys: dict[str, str] = {}
    global_phase = 0.0

    for node, constants in _iter_static_statements(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call_name = _call_name(node.value.func)
            if call_name == "QuantumRegister" and node.value.args:
                size = _int_expr(node.value.args[0], constants)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        register_sizes[target.id] = size
            if call_name == "ClassicalRegister" and node.value.args:
                size = _int_expr(node.value.args[0], constants)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        classical_register_sizes[target.id] = size
            if call_name == "QuantumCircuit" and node.value.args:
                n_qubits, register_offsets, classical_offsets = _qiskit_circuit_layout(
                    node.value, constants, register_sizes, classical_register_sizes
                )
                for keyword in node.value.keywords:
                    if keyword.arg == "global_phase":
                        global_phase = _number_expr(keyword.value, constants)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        circuit_vars[target.id] = n_qubits
        if isinstance(node, ast.Assign) and isinstance(
            node.value, ast.Constant | ast.Name | ast.BinOp | ast.UnaryOp | ast.Attribute
        ):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "global_phase":
                    var_name = _name(target.value)
                    if var_name in circuit_vars:
                        global_phase = _number_expr(node.value, constants)
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        var_name = _name(call.func.value)
        if var_name not in circuit_vars:
            continue
        method = call.func.attr
        if method == "barrier" and not call.args:
            operations.append(CircuitOperation("BARRIER", tuple(range(circuit_vars[var_name]))))
            continue
        if method == "measure_all":
            measurements = list(range(circuit_vars[var_name]))
            measurement_keys = {str(qubit): f"c[{qubit}]" for qubit in measurements}
            continue
        if method == "measure":
            if call.args:
                qubit = _qiskit_index_expr(call.args[0], constants, register_offsets)
                measurements.append(qubit)
                if len(call.args) >= 2:
                    measurement_keys[str(qubit)] = _qiskit_classical_key(
                        call.args[1], constants, classical_offsets
                    )
            continue
        operation = _qiskit_operation(method, call, constants, register_offsets)
        if operation is not None:
            operations.append(operation)

    if not circuit_vars:
        raise _unsupported(
            "qiskit.no_circuit", "No supported Qiskit QuantumCircuit construction found."
        )
    n_qubits = next(iter(circuit_vars.values()))
    return InternalCircuit(
        n_qubits,
        operations,
        measurements or list(range(n_qubits)),
        quantum_registers={
            name: list(range(offset, offset + size))
            for name, (offset, size) in register_offsets.items()
        },
        classical_registers={
            name: list(range(offset, offset + size))
            for name, (offset, size) in classical_offsets.items()
        },
        measurement_keys=measurement_keys,
        bit_order="qiskit-classical",
        global_phase=global_phase,
    )


def _qiskit_circuit_layout(
    call: ast.Call,
    constants: dict[str, object],
    register_sizes: dict[str, int],
    classical_register_sizes: dict[str, int],
) -> tuple[int, dict[str, tuple[int, int]], dict[str, tuple[int, int]]]:
    quantum_offsets: dict[str, tuple[int, int]] = {}
    classical_offsets: dict[str, tuple[int, int]] = {}
    next_quantum = 0
    next_classical = 0
    direct_qubit_count: int | None = None
    for arg in call.args:
        if isinstance(arg, ast.Name) and arg.id in register_sizes:
            size = register_sizes[arg.id]
            quantum_offsets[arg.id] = (next_quantum, size)
            next_quantum += size
        elif isinstance(arg, ast.Name) and arg.id in classical_register_sizes:
            size = classical_register_sizes[arg.id]
            classical_offsets[arg.id] = (next_classical, size)
            next_classical += size
        elif direct_qubit_count is None:
            direct_qubit_count = _int_expr(arg, constants)
            next_quantum = max(next_quantum, direct_qubit_count)
        else:
            try:
                classical_size = _int_expr(arg, constants)
            except TranslationError:
                continue
            classical_offsets.setdefault("c", (next_classical, classical_size))
            next_classical += classical_size
    if direct_qubit_count is not None and not quantum_offsets:
        quantum_offsets["q"] = (0, direct_qubit_count)
    return next_quantum, quantum_offsets, classical_offsets


def _qiskit_operation(
    method: str,
    call: ast.Call,
    constants: dict[str, object],
    register_offsets: dict[str, tuple[int, int]],
) -> CircuitOperation | None:
    one_qubit = {"h": "H", "x": "X", "y": "Y", "z": "Z", "s": "S", "t": "T", "sx": "SX"}
    phase_gates = {"p": "P", "phase": "P"}
    rotations = {"rx": "RX", "ry": "RY", "rz": "RZ"}
    two_qubit = {"cx": "CNOT", "cnot": "CNOT", "cz": "CZ", "swap": "SWAP"}
    controlled_rotations = {"crx": "CRX", "cry": "CRY", "crz": "CRZ"}
    if method == "reset" and len(call.args) >= 1:
        return CircuitOperation(
            "RESET", (_qiskit_index_expr(call.args[0], constants, register_offsets),)
        )
    if method == "barrier" and call.args:
        qubits: list[int] = []
        for arg in call.args:
            qubits.extend(_qiskit_index_list(arg, constants, register_offsets))
        return CircuitOperation("BARRIER", tuple(qubits))
    if method == "delay" and len(call.args) >= 2:
        params: dict[str, object] = {"duration": _number_expr(call.args[0], constants)}
        unit = _keyword(call, "unit")
        if isinstance(unit, ast.Constant) and isinstance(unit.value, str):
            params["unit"] = unit.value
        return CircuitOperation(
            "DELAY",
            (_qiskit_index_expr(call.args[1], constants, register_offsets),),
            params,
        )
    if method in one_qubit and len(call.args) >= 1:
        return CircuitOperation(
            one_qubit[method], (_qiskit_index_expr(call.args[0], constants, register_offsets),)
        )
    if method in phase_gates and len(call.args) >= 2:
        return CircuitOperation(
            phase_gates[method],
            (_qiskit_index_expr(call.args[1], constants, register_offsets),),
            {"theta": _number_expr(call.args[0], constants)},
        )
    if method in rotations and len(call.args) >= 2:
        return CircuitOperation(
            rotations[method],
            (_qiskit_index_expr(call.args[1], constants, register_offsets),),
            {"theta": _number_expr(call.args[0], constants)},
        )
    if method == "u" and len(call.args) >= 4:
        return CircuitOperation(
            "U",
            (_qiskit_index_expr(call.args[3], constants, register_offsets),),
            {
                "theta": _number_expr(call.args[0], constants),
                "phi": _number_expr(call.args[1], constants),
                "lambda": _number_expr(call.args[2], constants),
            },
        )
    if method in two_qubit and len(call.args) >= 2:
        return CircuitOperation(
            two_qubit[method],
            (
                _qiskit_index_expr(call.args[0], constants, register_offsets),
                _qiskit_index_expr(call.args[1], constants, register_offsets),
            ),
        )
    if method == "ccx" and len(call.args) >= 3:
        return CircuitOperation(
            "CCX",
            tuple(_qiskit_index_expr(arg, constants, register_offsets) for arg in call.args[:3]),
        )
    if method in controlled_rotations and len(call.args) >= 3:
        return CircuitOperation(
            controlled_rotations[method],
            (
                _qiskit_index_expr(call.args[1], constants, register_offsets),
                _qiskit_index_expr(call.args[2], constants, register_offsets),
            ),
            {"theta": _number_expr(call.args[0], constants)},
        )
    if method == "cp" and len(call.args) >= 3:
        return CircuitOperation(
            "CPHASE",
            (
                _qiskit_index_expr(call.args[1], constants, register_offsets),
                _qiskit_index_expr(call.args[2], constants, register_offsets),
            ),
            {"theta": _number_expr(call.args[0], constants)},
        )
    return None


def _qiskit_index_list(
    node: ast.AST, constants: dict[str, object], register_offsets: dict[str, tuple[int, int]]
) -> list[int]:
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_qiskit_index_expr(item, constants, register_offsets) for item in node.elts]
    if isinstance(node, ast.Name) and node.id in register_offsets:
        offset, size = register_offsets[node.id]
        return list(range(offset, offset + size))
    return [_qiskit_index_expr(node, constants, register_offsets)]


def _qiskit_index_expr(
    node: ast.AST, constants: dict[str, object], register_offsets: dict[str, tuple[int, int]]
) -> int:
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in register_offsets
    ):
        offset, _ = register_offsets[node.value.id]
        return offset + _int_expr(node.slice, constants)
    return _int_expr(node, constants)


def _qiskit_classical_key(
    node: ast.AST, constants: dict[str, object], classical_offsets: dict[str, tuple[int, int]]
) -> str:
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        index = _int_expr(node.slice, constants)
        register_name = node.value.id
        if register_name in classical_offsets:
            offset, _ = classical_offsets[register_name]
            return f"{register_name}[{offset + index}]"
        return f"{register_name}[{index}]"
    return f"c[{_int_expr(node, constants)}]"


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

    inferred_n_qubits = _inferred_n_qubits(operations, measurements, qubit_ranges, qubit_vars)
    if inferred_n_qubits is None:
        raise _unsupported("cirq.no_circuit", "No supported Cirq circuit construction found.")
    return InternalCircuit(
        inferred_n_qubits, operations, measurements or list(range(inferred_n_qubits))
    )


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
    if gate_name == "reset":
        operations.extend(
            CircuitOperation(
                "RESET",
                (_cirq_qubit_index(arg, qubit_ranges, qubit_vars, constants),),
            )
            for arg in node.args
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
    if gate_name == "TOFFOLI" and len(call.args) >= 3:
        return CircuitOperation(
            "CCX",
            (
                _cirq_qubit_index(call.args[0], qubit_ranges, qubit_vars, constants),
                _cirq_qubit_index(call.args[1], qubit_ranges, qubit_vars, constants),
                _cirq_qubit_index(call.args[2], qubit_ranges, qubit_vars, constants),
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
    if gate_name in {"XPowGate", "ZPowGate"} and op_call.args:
        exponent = _keyword(gate_call, "exponent")
        if exponent is None:
            return None
        target = _cirq_qubit_index(op_call.args[0], qubit_ranges, qubit_vars, constants)
        if gate_name == "XPowGate":
            if abs(_number_expr(exponent, constants) - 0.5) <= 1e-12:
                return CircuitOperation("SX", (target,))
            return None
        return CircuitOperation(
            "P",
            (target,),
            {"theta": _number_expr(exponent, constants) * 3.141592653589793},
        )
    if gate_name == "CZPowGate" and len(op_call.args) >= 2:
        exponent = _keyword(gate_call, "exponent")
        if exponent is None:
            return None
        return CircuitOperation(
            "CPHASE",
            (
                _cirq_qubit_index(op_call.args[0], qubit_ranges, qubit_vars, constants),
                _cirq_qubit_index(op_call.args[1], qubit_ranges, qubit_vars, constants),
            ),
            {"theta": _number_expr(exponent, constants) * 3.141592653589793},
        )
    if gate_name == "ResetChannel" and op_call.args:
        return CircuitOperation(
            "RESET",
            (_cirq_qubit_index(op_call.args[0], qubit_ranges, qubit_vars, constants),),
        )
    if gate_name == "WaitGate" and op_call.args:
        duration = _keyword(gate_call, "duration") or (
            gate_call.args[0] if gate_call.args else None
        )
        params: dict[str, object] = {}
        if duration is not None:
            try:
                params["duration"] = _number_expr(duration, constants)
            except TranslationError:
                params["duration"] = ast.unparse(duration)
        return CircuitOperation(
            "DELAY",
            tuple(
                _cirq_qubit_index(arg, qubit_ranges, qubit_vars, constants) for arg in op_call.args
            ),
            params,
        )
    if gate_name == "ControlledGate" and gate_call.args and len(op_call.args) >= 2:
        inner = gate_call.args[0]
        if isinstance(inner, ast.Call):
            inner_name = _call_name(inner.func).rsplit(".", 1)[-1]
            if inner_name in rotations and inner.args:
                return CircuitOperation(
                    "C" + rotations[inner_name],
                    (
                        _cirq_qubit_index(op_call.args[0], qubit_ranges, qubit_vars, constants),
                        _cirq_qubit_index(op_call.args[1], qubit_ranges, qubit_vars, constants),
                    ),
                    {"theta": _number_expr(inner.args[0], constants)},
                )
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
        "SX": "SX",
    }
    rotations = {"RX": "RX", "RY": "RY", "RZ": "RZ", "PhaseShift": "P"}
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
    if gate_name == "U3" and len(call.args) >= 3 and len(wires) >= 1:
        return CircuitOperation(
            "U",
            (wires[0],),
            {
                "theta": _number_expr(call.args[0], constants),
                "phi": _number_expr(call.args[1], constants),
                "lambda": _number_expr(call.args[2], constants),
            },
        )
    if gate_name in two_qubit and len(wires) >= 2:
        return CircuitOperation(two_qubit[gate_name], (wires[0], wires[1]))
    if gate_name == "Toffoli" and len(wires) >= 3:
        return CircuitOperation("CCX", (wires[0], wires[1], wires[2]))
    if gate_name in {"CRX", "CRY", "CRZ"} and call.args and len(wires) >= 2:
        return CircuitOperation(
            gate_name, (wires[0], wires[1]), {"theta": _number_expr(call.args[0], constants)}
        )
    if gate_name == "ControlledPhaseShift" and call.args and len(wires) >= 2:
        return CircuitOperation(
            "CPHASE",
            (wires[0], wires[1]),
            {"theta": _number_expr(call.args[0], constants)},
        )
    if gate_name == "Barrier" and wires:
        return CircuitOperation("BARRIER", tuple(wires))
    if gate_name == "Reset" and wires:
        return CircuitOperation("RESET", (wires[0],))
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
    if gate_name in {"Toffoli", "CRX", "CRY", "CRZ"} and call.args:
        return call.args[-1]
    if gate_name == "U3" and len(call.args) >= 4:
        return call.args[3]
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
            probability_target = _keyword(call, "target")
            if probability_target is not None:
                measurements = _wire_list(probability_target, constants)
            continue
        if call.func.attr == "barrier":
            targets = _wire_list(call.args[0], constants) if call.args else []
            operations.append(CircuitOperation("BARRIER", tuple(targets)))
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
    one_qubit = {"h": "H", "x": "X", "y": "Y", "z": "Z", "s": "S", "t": "T", "v": "SX"}
    rotations = {"rx": "RX", "ry": "RY", "rz": "RZ", "phaseshift": "P"}
    two_qubit = {"cnot": "CNOT", "cz": "CZ", "swap": "SWAP"}
    if method in one_qubit and len(call.args) >= 1:
        return CircuitOperation(one_qubit[method], (_int_expr(call.args[0], constants),))
    if method == "reset" and len(call.args) >= 1:
        return CircuitOperation("RESET", (_int_expr(call.args[0], constants),))
    if method in rotations and len(call.args) >= 1:
        angle = _keyword(call, "angle") or (call.args[1] if len(call.args) >= 2 else None)
        if angle is None:
            return None
        return CircuitOperation(
            rotations[method],
            (_int_expr(call.args[0], constants),),
            {"theta": _number_expr(angle, constants)},
        )
    if method == "u" and len(call.args) >= 4:
        return CircuitOperation(
            "U",
            (_int_expr(call.args[0], constants),),
            {
                "theta": _number_expr(call.args[1], constants),
                "phi": _number_expr(call.args[2], constants),
                "lambda": _number_expr(call.args[3], constants),
            },
        )
    if method in two_qubit and len(call.args) >= 2:
        return CircuitOperation(
            two_qubit[method],
            (_int_expr(call.args[0], constants), _int_expr(call.args[1], constants)),
        )
    if method == "ccnot" and len(call.args) >= 3:
        return CircuitOperation(
            "CCX",
            (
                _int_expr(call.args[0], constants),
                _int_expr(call.args[1], constants),
                _int_expr(call.args[2], constants),
            ),
        )
    if method in {"crx", "cry", "crz"} and len(call.args) >= 2:
        angle = _keyword(call, "angle") or (call.args[2] if len(call.args) >= 3 else None)
        if angle is None:
            return None
        return CircuitOperation(
            method.upper(),
            (_int_expr(call.args[0], constants), _int_expr(call.args[1], constants)),
            {"theta": _number_expr(angle, constants)},
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
    return internal_circuit_to_json(circuit)


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
    if isinstance(node, ast.Name):
        value = constants.get(node.id)
        if isinstance(value, (int, float)):
            return float(value)
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
    if isinstance(node, ast.Name):
        value = constants.get(node.id)
        if isinstance(value, int):
            return [value]
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
    if isinstance(node, ast.Name):
        value = constants.get(node.id)
        if isinstance(value, int):
            return value
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
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")
    return repr(float(value))


def _unsupported(code: str, message: str) -> TranslationError:
    return TranslationError([TranslationDiagnostic("error", code, message)])
