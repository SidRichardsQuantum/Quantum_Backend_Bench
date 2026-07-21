"""Tests for observable and Pauli-Hamiltonian translation."""

from __future__ import annotations

import json

import pytest

from quantum_backend_bench.cli import main
from quantum_backend_bench.core.observable_translate import (
    hamiltonian_check_report,
    hamiltonian_translation_report,
    import_hamiltonian_source,
    translate_hamiltonian_source,
    verify_hamiltonian_translation,
    translation_capability_rows,
)

PAULI_JSON = """{
  "n_qubits": 2,
  "terms": [
    {"coefficient": 0.5, "paulis": {"0": "Z", "1": "Z"}},
    {"coefficient": -1.25, "paulis": {"0": "X"}}
  ]
}
"""


def test_translate_pauli_json_to_all_local_sdk_hamiltonians() -> None:
    hamiltonian, detected = import_hamiltonian_source(PAULI_JSON, from_format="pauli-json")

    assert detected == "pauli-json"
    assert hamiltonian.n_qubits == 2

    for target in ("qiskit_aer", "cirq", "pennylane", "braket_local"):
        result = translate_hamiltonian_source(
            PAULI_JSON,
            from_format="pauli-json",
            to_format=target,
            verify="canonical",
        )
        assert result.verification is not None
        assert result.verification.passed
        assert f"output_format={target}" in result.notes


def test_import_static_sdk_hamiltonian_snippets() -> None:
    qiskit_source = """from qiskit.quantum_info import SparsePauliOp

hamiltonian = SparsePauliOp.from_list([
    ("ZZ", 0.5),
    ("XI", -1.25),
])
"""
    cirq_source = """import cirq

qubits = cirq.LineQubit.range(2)
hamiltonian = (
    0.5 * cirq.Z(qubits[0]) * cirq.Z(qubits[1])
    + -1.25 * cirq.X(qubits[0])
)
"""
    pennylane_source = """import pennylane as qml

hamiltonian = qml.Hamiltonian(
    [0.5, -1.25],
    [qml.PauliZ(0) @ qml.PauliZ(1), qml.PauliX(0)],
)
"""
    braket_source = """from braket.circuits import Observable

hamiltonian_terms = [
    (0.5, Observable.Z() @ Observable.Z(), [0, 1]),
    (-1.25, Observable.X(), [0]),
]
"""

    expected, _ = import_hamiltonian_source(qiskit_source, from_format="qiskit")
    for source, source_format in (
        (cirq_source, "cirq"),
        (pennylane_source, "pennylane"),
        (braket_source, "braket"),
    ):
        actual, _ = import_hamiltonian_source(source, from_format=source_format)
        assert actual == expected


def test_hamiltonian_reports_and_audit_rows() -> None:
    result = translate_hamiltonian_source(
        PAULI_JSON, from_format="pauli-json", to_format="pennylane"
    )
    report = hamiltonian_translation_report(
        result,
        source_path="inline:pauli_json",
        from_format="pauli-json",
        to_format="pennylane",
    )
    hamiltonian, detected = import_hamiltonian_source(PAULI_JSON, from_format="pauli-json")
    check = hamiltonian_check_report(hamiltonian, detected)
    audit = translation_capability_rows()

    assert report["verification"]["passed"] is True
    assert report["schema_metadata"]["input_schema"] == "pauli-json"
    assert check["term_count"] == 2
    assert check["pauli_counts"] == {"X": 1, "Z": 2}
    assert all(row["pauli_hamiltonians"] for row in audit)
    assert all(
        "arithmetic workflow parameter expressions" in row["parameter_forms"] for row in audit
    )


def test_cli_translate_hamiltonian_writes_output_and_report(tmp_path, capsys) -> None:
    source = tmp_path / "hamiltonian.json"
    output = tmp_path / "hamiltonian.py"
    report = tmp_path / "report.json"
    source.write_text(PAULI_JSON, encoding="utf-8")

    exit_code = main(
        [
            "translate-hamiltonian",
            str(source),
            "--from-format",
            "pauli-json",
            "--to-format",
            "qiskit_aer",
            "--output",
            str(output),
            "--save-report",
            str(report),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(report.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "Saved translated Hamiltonian" in captured.out
    assert "SparsePauliOp.from_list" in output.read_text(encoding="utf-8")
    assert payload["verification"]["passed"] is True
    assert payload["schema_metadata"]["input_schema"] == "pauli-json"


def test_cli_translate_observable_stdout_and_audit(capsys, tmp_path) -> None:
    source = tmp_path / "observable.json"
    source.write_text(
        json.dumps({"n_qubits": 1, "terms": [{"coefficient": 1.0, "paulis": {"0": "Z"}}]}),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate-observable",
            str(source),
            "--from-format",
            "pauli-json",
            "--to-format",
            "cirq",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "cirq.Z(qubits[0])" in captured.out

    audit_exit = main(["translation-audit"])
    audit_output = capsys.readouterr().out
    assert audit_exit == 0
    assert "pauli_hamiltonians" in audit_output
    assert "qiskit_aer" in audit_output


def test_matrix_verification_passes_for_generated_hamiltonian() -> None:
    hamiltonian, _ = import_hamiltonian_source(PAULI_JSON, from_format="pauli-json")
    result = translate_hamiltonian_source(
        PAULI_JSON,
        from_format="pauli-json",
        to_format="qiskit_aer",
        verify="matrix",
    )
    verification = verify_hamiltonian_translation(
        hamiltonian,
        result.source,
        to_format="qiskit_aer",
        mode="matrix",
    )

    assert result.verification is not None
    assert result.verification.passed
    assert verification.passed
    assert "max_abs_delta=0" in verification.details


def test_hamiltonian_expected_outputs_are_stable() -> None:
    root = __import__("pathlib").Path(__file__).resolve().parents[1] / "examples" / "translation"
    cases = [
        (
            "ising_hamiltonian.json",
            "pauli-json",
            "qiskit_aer",
            "expected/ising_hamiltonian_to_qiskit.py",
        ),
        ("qiskit_hamiltonian.py", "qiskit", "cirq", "expected/qiskit_hamiltonian_to_cirq.py"),
        ("cirq_hamiltonian.py", "cirq", "pennylane", "expected/cirq_hamiltonian_to_pennylane.py"),
        (
            "pennylane_hamiltonian.py",
            "pennylane",
            "braket_local",
            "expected/pennylane_hamiltonian_to_braket.py",
        ),
    ]

    for source_name, from_format, to_format, expected_name in cases:
        result = translate_hamiltonian_source(
            (root / source_name).read_text(encoding="utf-8"),
            from_format=from_format,
            to_format=to_format,
            verify="matrix",
        )
        assert result.source == (root / expected_name).read_text(encoding="utf-8")
        assert result.verification is not None
        assert result.verification.passed


@pytest.mark.parametrize(
    ("filename", "from_format", "expected_code"),
    [
        ("dynamic_hamiltonian_coeff_qiskit.py", "qiskit", "python.literal_number"),
        ("non_pauli_hamiltonian_qiskit.py", "qiskit", "hamiltonian.pauli"),
        ("symbolic_hamiltonian_pennylane.py", "pennylane", "python.literal_number"),
    ],
)
def test_rejected_hamiltonian_fixtures_have_stable_diagnostics(
    filename: str, from_format: str, expected_code: str
) -> None:
    root = __import__("pathlib").Path(__file__).resolve().parents[1] / "examples" / "translation"
    source = (root / "rejected" / filename).read_text(encoding="utf-8")

    with pytest.raises(Exception) as exc_info:
        import_hamiltonian_source(source, from_format=from_format)

    assert expected_code in {diagnostic.code for diagnostic in exc_info.value.diagnostics}


def test_cli_translation_audit_filters(capsys) -> None:
    exit_code = main(
        ["translation-audit", "--from-format", "qiskit", "--to-format", "qiskit_aer", "--json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [row["sdk"] for row in payload] == ["qiskit_aer"]
    assert payload[0]["schema_version"] == "0.1"
    assert payload[0]["verification_modes"] == [
        "exact",
        "samples",
        "canonical",
        "statevector",
        "matrix",
        "semantic",
        "result-schema",
    ]
    assert "CPHASE" in payload[0]["supported_gates"]
    assert payload[0]["noise_models"] is True
    assert "provider-specific calibrated noise semantics" in payload[0]["planned_layers"]
