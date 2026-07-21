from quantum_backend_bench.core.sdk_audit import (
    NOISE_MODELS,
    audit_passed,
    format_scorecard,
    noise_model_matrix,
    roundtrip_audit,
    save_audit_csv,
    save_audit_json,
    save_audit_report,
    sdk_parity_scorecard,
)


def test_sdk_parity_scorecard_has_free_local_sdks():
    rows = sdk_parity_scorecard()
    sdks = {row["sdk"] for row in rows}

    assert {"cirq", "pennylane", "braket_local", "qiskit_aer", "qutip"} <= sdks
    assert all("circuit_translation" in row for row in rows)
    assert "SDK Parity Scorecard" in format_scorecard(rows)


def test_noise_model_matrix_reports_broader_local_models():
    rows = noise_model_matrix()
    qiskit = next(row for row in rows if row["backend"] == "qiskit_aer")

    assert set(qiskit["models"]) == set(NOISE_MODELS)
    assert qiskit["models"]["amplitude_damping"] == "implemented"
    assert qiskit["models"]["readout_error"] == "implemented"


def test_roundtrip_audit_passes_for_free_translation_targets():
    rows = roundtrip_audit(
        targets=["cirq", "qiskit_aer", "pennylane", "braket_local"],
        include_hamiltonian=True,
        include_workflow=True,
    )

    assert rows
    assert audit_passed(rows)
    assert {row["target"] for row in rows} == {
        "cirq",
        "qiskit_aer",
        "pennylane",
        "braket_local",
    }
    assert "gate-coverage" in {row["case"] for row in rows}
    assert "hamiltonian_roundtrip" in {row["audit"] for row in rows}
    assert "workflow_roundtrip" in {row["audit"] for row in rows}


def test_roundtrip_audit_supports_canonical_verification_mode():
    rows = roundtrip_audit(targets=["qiskit_aer"], circuit_verify="canonical")

    assert rows
    assert audit_passed(rows)
    assert {row["verification_mode"] for row in rows} == {"canonical"}
    assert all(row["canonical_match"] is True for row in rows)


def test_audit_artifact_writers(tmp_path):
    rows = roundtrip_audit(targets=["cirq"])

    json_path = save_audit_json(rows, tmp_path / "audit.json")
    csv_path = save_audit_csv(rows, tmp_path / "audit.csv")
    report_path = save_audit_report(rows, tmp_path / "audit.md", title="Audit")

    assert json_path.read_text(encoding="utf-8").startswith("[\n")
    assert "audit,target,case" in csv_path.read_text(encoding="utf-8")
    assert "# Audit" in report_path.read_text(encoding="utf-8")


def test_roundtrip_audit_reports_workflow_semantic_metrics():
    rows = roundtrip_audit(
        targets=["cirq"],
        include_workflow=True,
        workflow_verify="semantic",
    )
    workflow_rows = [row for row in rows if row["audit"] == "workflow_roundtrip"]

    assert audit_passed(workflow_rows)
    assert {row["verification_mode"] for row in workflow_rows} == {"semantic"}
    assert all(row["total_variation_distance"] == 0.0 for row in workflow_rows)
    assert all(row["expectation_max_abs_error"] == 0.0 for row in workflow_rows)
    assert all(row["result_schema_valid"] is True for row in workflow_rows)
