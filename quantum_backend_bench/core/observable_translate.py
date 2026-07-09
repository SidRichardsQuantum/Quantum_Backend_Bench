"""Observable and Pauli-Hamiltonian translation helpers."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import Any

from quantum_backend_bench.core.circuit_translate import (
    TranslationDiagnostic,
    TranslationError,
    TranslationResult,
    TranslationVerification,
)
from quantum_backend_bench.core.neutral_schema import (
    NEUTRAL_SCHEMA_VERSION,
    report_schema_metadata,
)

HAMILTONIAN_INPUT_FORMATS = ("auto", "pauli-json", "qiskit", "cirq", "pennylane", "braket")
HAMILTONIAN_OUTPUT_FORMATS = ("qiskit_aer", "cirq", "pennylane", "braket_local", "pauli-json")
HAMILTONIAN_VERIFY_MODES = ("none", "canonical", "matrix")

_OUTPUT_IMPORT_FORMAT = {
    "qiskit_aer": "qiskit",
    "cirq": "cirq",
    "pennylane": "pennylane",
    "braket_local": "braket",
    "pauli-json": "pauli-json",
}

_PAULIS = {"I", "X", "Y", "Z"}


@dataclass(frozen=True, slots=True)
class PauliTerm:
    """One weighted Pauli product term."""

    coefficient: float
    paulis: tuple[tuple[int, str], ...]


@dataclass(frozen=True, slots=True)
class PauliHamiltonian:
    """Neutral weighted Pauli Hamiltonian representation."""

    n_qubits: int
    terms: tuple[PauliTerm, ...]


@dataclass(frozen=True, slots=True)
class HamiltonianVerification:
    """Semantic verification result for Hamiltonian translation."""

    mode: str
    passed: bool
    details: str


def translate_hamiltonian_source(
    source: str,
    *,
    from_format: str = "auto",
    to_format: str,
    verify: str = "canonical",
) -> TranslationResult:
    """Translate a supported weighted Pauli Hamiltonian source."""

    if verify not in HAMILTONIAN_VERIFY_MODES:
        raise ValueError(
            f"Unknown verification mode '{verify}'. Available: {', '.join(HAMILTONIAN_VERIFY_MODES)}"
        )
    hamiltonian, detected_format = import_hamiltonian_source(source, from_format=from_format)
    output = emit_hamiltonian_source(hamiltonian, to_format)
    notes = [f"input_format={detected_format}", f"output_format={to_format}"]
    diagnostics = [
        TranslationDiagnostic(
            "info",
            "translation.scope.pauli_hamiltonian",
            "Hamiltonian translation preserves weighted sums of Pauli I/X/Y/Z products only.",
        ),
        TranslationDiagnostic(
            "warning",
            "translation.caveat.pauli_ordering",
            "SDKs display Pauli products with different wire-order conventions; canonical verification compares neutral qubit-indexed terms.",
        ),
    ]
    verification = None
    if verify != "none":
        verification = verify_hamiltonian_translation(
            hamiltonian, output, to_format=to_format, mode=verify
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
    return TranslationResult(
        output,
        notes,
        diagnostics,
        _translation_verification(verification) if verification is not None else None,
    )


def import_hamiltonian_source(
    source: str, *, from_format: str = "auto"
) -> tuple[PauliHamiltonian, str]:
    """Import a supported weighted Pauli Hamiltonian into the neutral model."""

    if from_format not in HAMILTONIAN_INPUT_FORMATS:
        available = ", ".join(HAMILTONIAN_INPUT_FORMATS)
        raise ValueError(
            f"Unknown Hamiltonian input format '{from_format}'. Available: {available}"
        )
    selected_format = _detect_format(source) if from_format == "auto" else from_format
    try:
        if selected_format == "pauli-json":
            return _import_pauli_json(source), selected_format
        tree = ast.parse(source)
        if selected_format == "qiskit":
            return _import_qiskit_ast(tree), selected_format
        if selected_format == "cirq":
            return _import_cirq_ast(tree), selected_format
        if selected_format == "pennylane":
            return _import_pennylane_ast(tree), selected_format
        if selected_format == "braket":
            return _import_braket_ast(tree), selected_format
    except TranslationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive diagnostic wrapper
        raise _unsupported(
            "hamiltonian.parse", f"Could not parse Hamiltonian source: {exc}"
        ) from exc
    raise ValueError(f"Unsupported Hamiltonian input format: {selected_format}")


def emit_hamiltonian_source(hamiltonian: PauliHamiltonian, to_format: str) -> str:
    """Emit a neutral Hamiltonian in a supported SDK representation."""

    if to_format not in HAMILTONIAN_OUTPUT_FORMATS:
        available = ", ".join(HAMILTONIAN_OUTPUT_FORMATS)
        raise ValueError(f"Unknown Hamiltonian output format '{to_format}'. Available: {available}")
    if to_format == "pauli-json":
        return _emit_pauli_json(hamiltonian)
    if to_format == "qiskit_aer":
        return _emit_qiskit(hamiltonian)
    if to_format == "cirq":
        return _emit_cirq(hamiltonian)
    if to_format == "pennylane":
        return _emit_pennylane(hamiltonian)
    if to_format == "braket_local":
        return _emit_braket(hamiltonian)
    raise ValueError(f"Unsupported Hamiltonian output format: {to_format}")


def verify_hamiltonian_translation(
    expected: PauliHamiltonian, source: str, *, to_format: str, mode: str = "canonical"
) -> HamiltonianVerification:
    """Verify generated source by reimporting and comparing neutral semantics."""

    imported, _ = import_hamiltonian_source(source, from_format=_OUTPUT_IMPORT_FORMAT[to_format])
    if mode == "canonical":
        passed = canonical_hamiltonian(expected) == canonical_hamiltonian(imported)
        details = (
            "Canonical Pauli-term verification passed."
            if passed
            else "Canonical Pauli-term verification failed."
        )
        return HamiltonianVerification("canonical", passed, details)
    if mode == "matrix":
        if expected.n_qubits > 6:
            return HamiltonianVerification(
                "matrix",
                False,
                "Matrix verification supports up to 6 qubits.",
            )
        distance = _matrix_max_abs_delta(
            _hamiltonian_matrix(expected), _hamiltonian_matrix(imported)
        )
        passed = distance <= 1e-9
        details = (
            f"Matrix verification passed: max_abs_delta={distance:.3g}."
            if passed
            else f"Matrix verification failed: max_abs_delta={distance:.3g}."
        )
        return HamiltonianVerification("matrix", passed, details)
    raise ValueError(f"Unsupported Hamiltonian verification mode: {mode}")


def hamiltonian_translation_report(
    result: TranslationResult,
    *,
    source_path: str | None = None,
    from_format: str | None = None,
    to_format: str | None = None,
) -> dict[str, object]:
    """Return a JSON-compatible report for Hamiltonian translation."""

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
        "schema_metadata": report_schema_metadata(from_format=from_format, to_format=to_format),
        "notes": result.notes,
        "diagnostics": [
            {"severity": item.severity, "code": item.code, "message": item.message}
            for item in result.diagnostics
        ],
        "verification": verification,
    }


def hamiltonian_check_report(
    hamiltonian: PauliHamiltonian,
    detected_format: str,
    *,
    source_path: str | None = None,
) -> dict[str, object]:
    """Return a JSON-compatible preflight report for Hamiltonian translation."""

    return {
        "source_path": source_path,
        "input_format": detected_format,
        "n_qubits": hamiltonian.n_qubits,
        "term_count": len(hamiltonian.terms),
        "pauli_counts": _pauli_counts(hamiltonian),
        "supported_outputs": list(HAMILTONIAN_OUTPUT_FORMATS),
        "verification_available": True,
    }


def translation_capability_rows() -> list[dict[str, object]]:
    """Return current SDK translation capability rows."""

    sdks = ["qiskit_aer", "cirq", "pennylane", "braket_local"]
    rows = []
    for sdk in sdks:
        rows.append(
            {
                "sdk": sdk,
                "schema_version": NEUTRAL_SCHEMA_VERSION,
                "neutral_formats": [
                    "internal-json",
                    "pauli-json",
                    "workflow-json",
                    "result-json",
                ],
                "input_formats": _sdk_input_formats(sdk),
                "output_formats": [sdk],
                "supported_gates": [
                    "H",
                    "X",
                    "Y",
                    "Z",
                    "S",
                    "T",
                    "RX",
                    "RY",
                    "RZ",
                    "CNOT",
                    "CZ",
                    "SWAP",
                    "CPHASE",
                ],
                "parameter_forms": ["static numeric rotations", "named workflow parameters"],
                "measurements": ["static computational-basis measurements"],
                "hamiltonian_terms": ["weighted Pauli I/X/Y/Z products"],
                "result_shapes": ["counts", "probabilities", "samples", "expectations"],
                "diagnostic_modes": ["structured translation errors", "backend caveat warnings"],
                "circuits": True,
                "parameterized_circuits": True,
                "parameter_bindings": True,
                "pauli_hamiltonians": True,
                "observables": True,
                "measurement_requests": True,
                "measurement_grouping": True,
                "noise_models": False,
                "execution_wrappers": True,
                "result_objects": True,
                "verification_modes": ["exact", "samples", "canonical", "matrix"],
                "caveats": [
                    "static source only for SDK imports",
                    "workflow-json required for precise parameterized/execution layers",
                    "Pauli I/X/Y/Z products only",
                    "no symbolic Hamiltonian coefficients",
                    "neutral noise-model translation is not implemented",
                ],
                "planned_layers": [
                    "noise_models",
                    "broader static SDK imports for workflow layers",
                ],
                "notes": "Free/local static circuit, Pauli Hamiltonian, workflow, result, and grouping subset.",
            }
        )
    return rows


def canonical_hamiltonian(
    hamiltonian: PauliHamiltonian,
) -> tuple[int, tuple[tuple[float, tuple[tuple[int, str], ...]], ...]]:
    """Return a normalized, sortable Hamiltonian payload."""

    combined: dict[tuple[tuple[int, str], ...], float] = {}
    for term in hamiltonian.terms:
        key = tuple(sorted((wire, pauli) for wire, pauli in term.paulis if pauli != "I"))
        combined[key] = combined.get(key, 0.0) + float(term.coefficient)
    terms = tuple(
        sorted(
            (round(coefficient, 12), key)
            for key, coefficient in combined.items()
            if abs(coefficient) > 1e-12
        )
    )
    return hamiltonian.n_qubits, terms


def _sdk_input_formats(sdk: str) -> list[str]:
    return {
        "qiskit_aer": ["qiskit", "pauli-json"],
        "cirq": ["cirq", "pauli-json"],
        "pennylane": ["pennylane", "pauli-json"],
        "braket_local": ["braket", "pauli-json"],
    }[sdk]


def _hamiltonian_matrix(hamiltonian: PauliHamiltonian) -> list[list[complex]]:
    size = 2**hamiltonian.n_qubits
    matrix = [[0j for _ in range(size)] for _ in range(size)]
    for term in hamiltonian.terms:
        term_matrix = _term_matrix(term, hamiltonian.n_qubits)
        for row in range(size):
            for col in range(size):
                matrix[row][col] += term.coefficient * term_matrix[row][col]
    return matrix


def _term_matrix(term: PauliTerm, n_qubits: int) -> list[list[complex]]:
    factors = []
    lookup = dict(term.paulis)
    for wire in range(n_qubits):
        factors.append(_pauli_matrix(lookup.get(wire, "I")))
    matrix = factors[0]
    for factor in factors[1:]:
        matrix = _kron(matrix, factor)
    return matrix


def _pauli_matrix(pauli: str) -> list[list[complex]]:
    if pauli == "I":
        return [[1, 0], [0, 1]]
    if pauli == "X":
        return [[0, 1], [1, 0]]
    if pauli == "Y":
        return [[0, -1j], [1j, 0]]
    if pauli == "Z":
        return [[1, 0], [0, -1]]
    raise ValueError(f"Unsupported Pauli matrix: {pauli}")


def _kron(left: list[list[complex]], right: list[list[complex]]) -> list[list[complex]]:
    rows = []
    for left_row in left:
        for right_row in right:
            rows.append(
                [left_value * right_value for left_value in left_row for right_value in right_row]
            )
    return rows


def _matrix_max_abs_delta(left: list[list[complex]], right: list[list[complex]]) -> float:
    return max(
        abs(left[row][col] - right[row][col])
        for row in range(len(left))
        for col in range(len(left[row]))
    )


def _translation_verification(verification: HamiltonianVerification) -> TranslationVerification:
    return TranslationVerification(
        mode=verification.mode,
        passed=verification.passed,
        total_variation_distance=None,
        tolerance=0.0,
        details=verification.details,
    )


def _detect_format(source: str) -> str:
    stripped = source.lstrip()
    if stripped.startswith("{"):
        return "pauli-json"
    lowered = source.lower()
    if "sparsepauliop" in lowered:
        return "qiskit"
    if "cirq." in source:
        return "cirq"
    if "qml.hamiltonian" in lowered or "qml.pauli" in lowered:
        return "pennylane"
    if "observable." in source.lower():
        return "braket"
    raise _unsupported("hamiltonian.detect", "Could not detect Hamiltonian format.")


def _import_pauli_json(source: str) -> PauliHamiltonian:
    payload = json.loads(source)
    terms = [_term_from_payload(item) for item in payload.get("terms", [])]
    n_qubits = int(payload.get("n_qubits", _infer_n_qubits(terms)))
    return _hamiltonian(n_qubits, terms)


def _term_from_payload(payload: dict[str, Any]) -> PauliTerm:
    paulis = payload.get("paulis", {})
    return _term(
        float(payload.get("coefficient", 1.0)), {int(k): str(v) for k, v in paulis.items()}
    )


def _import_qiskit_ast(tree: ast.AST) -> PauliHamiltonian:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func).endswith("SparsePauliOp.from_list"):
            if not node.args:
                raise _unsupported("qiskit.no_terms", "SparsePauliOp.from_list requires terms.")
            terms = []
            for item in _literal_list(node.args[0]):
                if not isinstance(item, ast.Tuple) or len(item.elts) != 2:
                    raise _unsupported("qiskit.term", "Expected ('PAULI', coefficient) tuples.")
                label = _literal_string(item.elts[0])
                coefficient = _literal_number(item.elts[1])
                terms.append(_term_from_label(label, coefficient))
            return _hamiltonian(_infer_n_qubits(terms), terms)
    raise _unsupported("qiskit.no_sparse_pauli", "No SparsePauliOp.from_list Hamiltonian found.")


def _import_pennylane_ast(tree: ast.AST) -> PauliHamiltonian:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == "qml.Hamiltonian":
            if len(node.args) < 2:
                raise _unsupported(
                    "pennylane.hamiltonian",
                    "qml.Hamiltonian requires coefficients and observables.",
                )
            coefficients = [_literal_number(item) for item in _literal_list(node.args[0])]
            observables = _literal_list(node.args[1])
            if len(coefficients) != len(observables):
                raise _unsupported("pennylane.length", "Coefficient and observable counts differ.")
            terms = [
                _term(coefficient, _parse_pennylane_observable(observable))
                for coefficient, observable in zip(coefficients, observables)
            ]
            return _hamiltonian(_infer_n_qubits(terms), terms)
    raise _unsupported("pennylane.no_hamiltonian", "No qml.Hamiltonian construction found.")


def _import_braket_ast(tree: ast.AST) -> PauliHamiltonian:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "hamiltonian_terms":
                    terms = []
                    for item in _literal_list(node.value):
                        if not isinstance(item, ast.Tuple) or len(item.elts) != 3:
                            raise _unsupported(
                                "braket.term", "Expected (coefficient, observable, targets) tuples."
                            )
                        coefficient = _literal_number(item.elts[0])
                        targets = [
                            int(_literal_number(target)) for target in _literal_list(item.elts[2])
                        ]
                        pauli_sequence = _parse_braket_observable(item.elts[1])
                        if len(targets) != len(pauli_sequence):
                            raise _unsupported(
                                "braket.targets", "Observable and target lengths differ."
                            )
                        terms.append(_term(coefficient, dict(zip(targets, pauli_sequence))))
                    return _hamiltonian(_infer_n_qubits(terms), terms)
    raise _unsupported("braket.no_terms", "No hamiltonian_terms list found.")


def _import_cirq_ast(tree: ast.AST) -> PauliHamiltonian:
    qubits = _cirq_qubit_count(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "hamiltonian":
                    terms = [_parse_cirq_term(term) for term in _flatten_add(node.value)]
                    return _hamiltonian(max(qubits, _infer_n_qubits(terms)), terms)
    raise _unsupported("cirq.no_hamiltonian", "No hamiltonian assignment found.")


def _cirq_qubit_count(tree: ast.AST) -> int:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == "cirq.LineQubit.range":
            if node.args:
                return int(_literal_number(node.args[0]))
    return 0


def _flatten_add(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return [*_flatten_add(node.left), *_flatten_add(node.right)]
    return [node]


def _parse_cirq_term(node: ast.AST) -> PauliTerm:
    factors = _flatten_mult(node)
    coefficient = 1.0
    paulis: dict[int, str] = {}
    for factor in factors:
        if _is_number_node(factor):
            coefficient *= _literal_number(factor)
        elif isinstance(factor, ast.Call):
            gate = _call_name(factor.func)
            if gate not in {"cirq.X", "cirq.Y", "cirq.Z"}:
                raise _unsupported("cirq.observable", f"Unsupported Cirq observable {gate}.")
            wire = _qubit_subscript_index(factor.args[0])
            paulis[wire] = gate.rsplit(".", 1)[1]
        else:
            raise _unsupported("cirq.term", "Unsupported Cirq Hamiltonian term.")
    return _term(coefficient, paulis)


def _flatten_mult(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return [*_flatten_mult(node.left), *_flatten_mult(node.right)]
    return [node]


def _parse_pennylane_observable(node: ast.AST) -> dict[int, str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult):
        return {**_parse_pennylane_observable(node.left), **_parse_pennylane_observable(node.right)}
    if isinstance(node, ast.Call):
        name = _call_name(node.func)
        mapping = {"qml.PauliX": "X", "qml.PauliY": "Y", "qml.PauliZ": "Z", "qml.Identity": "I"}
        if name not in mapping:
            raise _unsupported("pennylane.observable", f"Unsupported PennyLane observable {name}.")
        wire = _wire_argument(node)
        return {wire: mapping[name]}
    raise _unsupported("pennylane.observable", "Unsupported PennyLane observable expression.")


def _parse_braket_observable(node: ast.AST) -> list[str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult):
        return [*_parse_braket_observable(node.left), *_parse_braket_observable(node.right)]
    if isinstance(node, ast.Call):
        name = _call_name(node.func)
        mapping = {
            "Observable.X": "X",
            "Observable.Y": "Y",
            "Observable.Z": "Z",
            "Observable.I": "I",
        }
        if name not in mapping:
            raise _unsupported("braket.observable", f"Unsupported Braket observable {name}.")
        return [mapping[name]]
    raise _unsupported("braket.observable", "Unsupported Braket observable expression.")


def _emit_pauli_json(hamiltonian: PauliHamiltonian) -> str:
    payload = {
        "schema_version": NEUTRAL_SCHEMA_VERSION,
        "n_qubits": hamiltonian.n_qubits,
        "terms": [
            {
                "coefficient": term.coefficient,
                "paulis": {str(wire): pauli for wire, pauli in term.paulis},
            }
            for term in hamiltonian.terms
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _emit_qiskit(hamiltonian: PauliHamiltonian) -> str:
    lines = [
        "from qiskit.quantum_info import SparsePauliOp",
        "",
        "hamiltonian = SparsePauliOp.from_list(",
        "    [",
    ]
    for term in hamiltonian.terms:
        lines.append(
            f'        ("{_label(term, hamiltonian.n_qubits)}", {_format_number(term.coefficient)}),'
        )
    lines.extend(["    ]", ")"])
    return "\n".join(lines) + "\n"


def _emit_cirq(hamiltonian: PauliHamiltonian) -> str:
    terms = [
        f"{_format_number(term.coefficient)} * {_cirq_product(term)}" for term in hamiltonian.terms
    ]
    lines = [
        "import cirq",
        "",
        f"qubits = cirq.LineQubit.range({hamiltonian.n_qubits})",
        "hamiltonian = " + " + ".join(terms),
    ]
    return "\n".join(lines) + "\n"


def _emit_pennylane(hamiltonian: PauliHamiltonian) -> str:
    coeffs = ", ".join(_format_number(term.coefficient) for term in hamiltonian.terms)
    observables = ", ".join(_pennylane_product(term) for term in hamiltonian.terms)
    return (
        "import pennylane as qml\n\n"
        f"hamiltonian = qml.Hamiltonian([{coeffs}], [{observables}])\n"
    )


def _emit_braket(hamiltonian: PauliHamiltonian) -> str:
    lines = ["from braket.circuits import Observable", "", "hamiltonian_terms = ["]
    for term in hamiltonian.terms:
        targets = ", ".join(str(wire) for wire, _ in term.paulis)
        lines.append(
            f"    ({_format_number(term.coefficient)}, {_braket_product(term)}, [{targets}]),"
        )
    lines.append("]")
    return "\n".join(lines) + "\n"


def _label(term: PauliTerm, n_qubits: int) -> str:
    lookup = dict(term.paulis)
    return "".join(lookup.get(index, "I") for index in range(n_qubits))


def _cirq_product(term: PauliTerm) -> str:
    if not term.paulis:
        return "cirq.I(qubits[0])"
    return " * ".join(f"cirq.{pauli}(qubits[{wire}])" for wire, pauli in term.paulis)


def _pennylane_product(term: PauliTerm) -> str:
    if not term.paulis:
        return "qml.Identity(0)"
    mapping = {"X": "PauliX", "Y": "PauliY", "Z": "PauliZ", "I": "Identity"}
    return " @ ".join(f"qml.{mapping[pauli]}({wire})" for wire, pauli in term.paulis)


def _braket_product(term: PauliTerm) -> str:
    if not term.paulis:
        return "Observable.I()"
    return " @ ".join(f"Observable.{pauli}()" for _, pauli in term.paulis)


def _hamiltonian(n_qubits: int, terms: list[PauliTerm]) -> PauliHamiltonian:
    if not terms:
        raise _unsupported("hamiltonian.empty", "Hamiltonian must contain at least one term.")
    return PauliHamiltonian(n_qubits=max(n_qubits, _infer_n_qubits(terms)), terms=tuple(terms))


def _term(coefficient: float, paulis: dict[int, str]) -> PauliTerm:
    normalized = []
    for wire, pauli in sorted(paulis.items()):
        if wire < 0:
            raise _unsupported("hamiltonian.wire", "Pauli wire indices must be non-negative.")
        pauli = pauli.upper()
        if pauli not in _PAULIS:
            raise _unsupported("hamiltonian.pauli", f"Unsupported Pauli operator {pauli}.")
        if pauli != "I":
            normalized.append((wire, pauli))
    return PauliTerm(float(coefficient), tuple(normalized))


def _term_from_label(label: str, coefficient: float) -> PauliTerm:
    return _term(
        coefficient, {index: pauli for index, pauli in enumerate(label.upper()) if pauli != "I"}
    )


def _infer_n_qubits(terms: list[PauliTerm] | tuple[PauliTerm, ...]) -> int:
    highest = -1
    for term in terms:
        for wire, _ in term.paulis:
            highest = max(highest, wire)
    return highest + 1


def _pauli_counts(hamiltonian: PauliHamiltonian) -> dict[str, int]:
    counts: dict[str, int] = {}
    for term in hamiltonian.terms:
        for _, pauli in term.paulis:
            counts[pauli] = counts.get(pauli, 0) + 1
    return dict(sorted(counts.items()))


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _literal_list(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.List | ast.Tuple):
        return list(node.elts)
    raise _unsupported("python.literal_list", "Expected a static list or tuple.")


def _literal_string(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise _unsupported("python.literal_string", "Expected a static string literal.")


def _literal_number(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_literal_number(node.operand)
    raise _unsupported("python.literal_number", "Expected a static numeric literal.")


def _is_number_node(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        or isinstance(node, ast.UnaryOp)
    )


def _qubit_subscript_index(node: ast.AST) -> int:
    if not isinstance(node, ast.Subscript):
        raise _unsupported("cirq.qubit", "Expected qubits[index].")
    return int(_literal_number(node.slice))


def _wire_argument(node: ast.Call) -> int:
    if node.args:
        return int(_literal_number(node.args[0]))
    for keyword in node.keywords:
        if keyword.arg == "wires":
            return int(_literal_number(keyword.value))
    raise _unsupported("pennylane.wire", "Expected a static wire index.")


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.12g}"


def _unsupported(code: str, message: str) -> TranslationError:
    return TranslationError([TranslationDiagnostic("error", code, message)])
