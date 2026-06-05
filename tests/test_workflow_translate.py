"""Tests for workflow-level SDK translation helpers."""

from __future__ import annotations

import json

from quantum_backend_bench.cli import main
from quantum_backend_bench.core.observable_translate import translation_capability_rows
from quantum_backend_bench.core.workflow_translate import (
    group_pauli_terms,
    group_pauli_terms_source,
    import_result_source,
    import_workflow_source,
    normalize_result_source,
    translate_workflow_source,
    verify_workflow_translation,
)

WORKFLOW_JSON = """{
  "name": "parameterized_bell_workflow",
  "n_qubits": 2,
  "parameters": ["theta"],
  "parameter_bindings": {"theta": 1.5707963267948966},
  "operations": [
    {"gate": "H", "targets": [0]},
    {"gate": "RX", "targets": [1], "parameter": "theta"},
    {"gate": "CNOT", "controls": [0], "targets": [1]}
  ],
  "measurements": [
    {"type": "counts", "targets": [0, 1]},
    {"type": "probabilities", "targets": [0, 1]},
    {
      "type": "expectation",
      "observable": {
        "n_qubits": 2,
        "terms": [{"coefficient": 1.0, "paulis": {"0": "Z", "1": "Z"}}]
      }
    }
  ],
  "shots": 512,
  "seed": 1234
}
"""


def test_translate_workflow_to_all_local_sdk_execution_snippets() -> None:
    workflow, detected = import_workflow_source(WORKFLOW_JSON)

    assert detected == "workflow-json"
    assert workflow.parameters == ("theta",)
    assert workflow.parameter_bindings["theta"] == 1.5707963267948966
    assert {request.kind for request in workflow.measurements} == {
        "counts",
        "probabilities",
        "expectation",
    }

    expected_markers = {
        "qiskit_aer": ['Parameter("theta")', "assign_parameters", "AerSimulator", "SparsePauliOp"],
        "cirq": [
            'sympy.Symbol("theta")',
            "param_resolver",
            "cirq.Simulator",
            "simulate_expectation_values",
        ],
        "pennylane": ["parameter_bindings", "qml.RX(theta", "qml.expval", "default.qubit"],
        "braket_local": [
            'FreeParameter("theta")',
            "LocalSimulator",
            'inputs = {"theta":',
            "expectation",
        ],
    }
    for target, markers in expected_markers.items():
        result = translate_workflow_source(WORKFLOW_JSON, to_format=target)
        for marker in markers:
            assert marker in result.source
        assert f"output_format={target}" in result.notes


def test_workflow_json_round_trip_keeps_bindings_and_requests() -> None:
    result = translate_workflow_source(WORKFLOW_JSON, to_format="workflow-json")
    payload = json.loads(result.source)

    assert payload["parameter_bindings"] == {"theta": 1.5707963267948966}
    assert [item["type"] for item in payload["measurements"]] == [
        "counts",
        "probabilities",
        "expectation",
    ]


def test_result_normalization_from_sdk_count_and_sample_shapes() -> None:
    qiskit_result = normalize_result_source(
        json.dumps({"counts": {"0 0": 3, "1 1": 1}, "shots": 4, "backend": "qiskit_aer"}),
        from_format="qiskit-counts-json",
    )
    cirq_result = import_result_source(
        json.dumps({"counts": {"00": 2, "10": 2}, "measurement_key": "m", "shots": 4}),
        from_format="cirq-counts-json",
    )
    braket_result = import_result_source(
        json.dumps({"measurement_counts": {"01": 5, "10": 5}, "shots": 10}),
        from_format="braket-counts-json",
    )
    pennylane_result = import_result_source(
        json.dumps({"samples": [[0, 0], [1, 1], [1, 1]], "shots": 3}),
        from_format="pennylane-samples-json",
    )

    payload = json.loads(qiskit_result.source)
    assert payload["counts"] == {"00": 3, "11": 1}
    assert payload["probabilities"] == {"00": 0.75, "11": 0.25}
    assert payload["metadata"]["backend"] == "qiskit_aer"
    assert cirq_result.metadata["measurement_key"] == "m"
    assert cirq_result.probabilities == {"00": 0.5, "10": 0.5}
    assert braket_result.counts == {"01": 5, "10": 5}
    assert braket_result.probabilities == {"01": 0.5, "10": 0.5}
    assert pennylane_result.counts == {"00": 1, "11": 2}
    assert pennylane_result.probabilities == {"00": 1 / 3, "11": 2 / 3}


def test_group_pauli_terms_qubit_wise_commuting_sets() -> None:
    hamiltonian = """{
      "n_qubits": 2,
      "terms": [
        {"coefficient": 1.0, "paulis": {"0": "Z"}},
        {"coefficient": 0.5, "paulis": {"0": "Z", "1": "Z"}},
        {"coefficient": -0.25, "paulis": {"0": "X"}},
        {"coefficient": 0.75, "paulis": {"1": "X"}}
      ]
    }
    """

    groups = group_pauli_terms(hamiltonian, from_format="pauli-json")
    result = group_pauli_terms_source(hamiltonian, from_format="pauli-json")
    payload = json.loads(result.source)

    assert [len(group.terms) for group in groups] == [2, 2]
    assert payload["group_count"] == 2
    assert payload["groups"][0]["term_count"] == 2


def test_cli_workflow_result_grouping_and_audit(capsys, tmp_path) -> None:
    workflow_path = tmp_path / "workflow.json"
    result_path = tmp_path / "result.json"
    groups_path = tmp_path / "groups.json"
    workflow_path.write_text(WORKFLOW_JSON, encoding="utf-8")
    result_path.write_text(json.dumps({"counts": {"00": 2, "11": 2}, "shots": 4}), encoding="utf-8")

    assert main(["translate-workflow", str(workflow_path), "--to-format", "qiskit_aer"]) == 0
    assert "AerSimulator" in capsys.readouterr().out

    assert (
        main(
            [
                "translate-result",
                str(result_path),
                "--from-format",
                "qiskit-counts-json",
            ]
        )
        == 0
    )
    assert '"probabilities"' in capsys.readouterr().out

    assert (
        main(
            [
                "group-pauli-terms",
                "examples/translation/ising_hamiltonian.json",
                "--from-format",
                "pauli-json",
                "--output",
                str(groups_path),
            ]
        )
        == 0
    )
    assert json.loads(groups_path.read_text(encoding="utf-8"))["group_count"] >= 1
    capsys.readouterr()

    assert main(["translation-audit", "--layer", "parameterized_circuits", "--json"]) == 0
    audit = json.loads(capsys.readouterr().out)
    assert audit
    assert all(row["parameter_bindings"] and row["result_objects"] for row in audit)


def test_capability_rows_include_requested_workflow_layers() -> None:
    rows = translation_capability_rows()
    for row in rows:
        assert row["parameterized_circuits"]
        assert row["parameter_bindings"]
        assert row["measurement_requests"]
        assert row["execution_wrappers"]
        assert row["result_objects"]
        assert row["measurement_grouping"]


def test_workflow_expected_outputs_are_stable_and_verifiable() -> None:
    root = __import__("pathlib").Path(__file__).resolve().parents[1] / "examples" / "translation"
    cases = [
        ("qiskit_aer", "expected/parameterized_workflow_to_qiskit.py"),
        ("cirq", "expected/parameterized_workflow_to_cirq.py"),
        ("pennylane", "expected/parameterized_workflow_to_pennylane.py"),
        ("braket_local", "expected/parameterized_workflow_to_braket.py"),
    ]
    workflow_source = (root / "parameterized_workflow.json").read_text(encoding="utf-8")
    workflow, _ = import_workflow_source(workflow_source)

    for to_format, expected_name in cases:
        result = translate_workflow_source(workflow_source, to_format=to_format, verify="canonical")
        expected = (root / expected_name).read_text(encoding="utf-8")
        verification = verify_workflow_translation(workflow, result.source, to_format=to_format)

        assert result.source == expected
        assert result.verification is not None
        assert result.verification.passed
        assert verification.passed
        assert "neutral_result" in result.source
        assert "workflow_spec" in result.source


def test_static_sdk_parameterized_workflow_importers() -> None:
    qiskit_source = """from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
theta = Parameter("theta")
circuit = QuantumCircuit(1, 1)
circuit.rx(theta, 0)
circuit.measure(0, 0)
parameter_bindings = {'theta': 0.25}
shots = 64
"""
    cirq_source = """import cirq
import sympy
qubits = cirq.LineQubit.range(1)
theta = sympy.Symbol("theta")
circuit = cirq.Circuit()
circuit.append(cirq.rx(theta)(qubits[0]))
circuit.append(cirq.measure(qubits[0], key='m'))
parameter_resolver = {'theta': 0.25}
shots = 64
"""
    pennylane_source = """import pennylane as qml
parameter_bindings = {'theta': 0.25}
dev = qml.device('default.qubit', wires=1, shots=64)
@qml.qnode(dev)
def circuit(theta):
    qml.RX(theta, wires=0)
    return qml.sample(wires=[0])
"""
    braket_source = """from braket.circuits import Circuit, FreeParameter
theta = FreeParameter("theta")
circuit = Circuit()
circuit.rx(0, theta)
inputs = {"theta": 0.25}
shots = 64
"""

    cases = [
        (qiskit_source, "qiskit"),
        (cirq_source, "cirq"),
        (pennylane_source, "pennylane"),
        (braket_source, "braket"),
    ]
    for source, from_format in cases:
        workflow, detected = import_workflow_source(source, from_format=from_format)
        assert detected == from_format
        assert workflow.n_qubits == 1
        assert workflow.parameters == ("theta",)
        assert workflow.parameter_bindings == {"theta": 0.25}
        assert workflow.operations[0].gate == "RX"
        assert workflow.operations[0].parameter == "theta"
        assert workflow.shots == 64


def test_result_normalization_example_fixtures() -> None:
    root = __import__("pathlib").Path(__file__).resolve().parents[1] / "examples" / "translation"
    cases = [
        ("qiskit_counts_result.json", "qiskit-counts-json"),
        ("cirq_counts_result.json", "cirq-counts-json"),
        ("pennylane_samples_result.json", "pennylane-samples-json"),
        ("braket_counts_result.json", "braket-counts-json"),
    ]

    for filename, from_format in cases:
        result = normalize_result_source(
            (root / filename).read_text(encoding="utf-8"),
            from_format=from_format,
        )
        payload = json.loads(result.source)
        assert payload["shots"] > 0
        assert sum(payload["counts"].values()) == payload["shots"]
        assert abs(sum(payload["probabilities"].values()) - 1.0) < 1e-12
        if from_format == "qiskit-counts-json":
            assert "0 0" not in payload["counts"]
            assert payload["metadata"]["backend"] == "qiskit_aer"
        if from_format == "cirq-counts-json":
            assert payload["metadata"]["measurement_key"] == "m"
        if from_format == "braket-counts-json":
            assert payload["metadata"]["result_type"] == "measurement_counts"
