"""Public API tests."""

import quantum_backend_bench as qbb
from quantum_backend_bench import (
    __version__,
    BENCHMARK_BUILDERS,
    SUITES,
    build_benchmark_from_config,
    build_suite,
    doctor_checks,
    format_compatibility_report,
    format_doctor_table,
    format_summary,
    group_pauli_terms,
    normalize_result_source,
    results_to_records,
    summarize_results,
    translate_circuit_source,
    translate_hamiltonian_source,
    translate_workflow_source,
    translation_capability_rows,
    translation_check_report,
)


def test_all_public_exports_resolve() -> None:
    assert __version__
    assert sorted(qbb.__all__) == sorted(set(qbb.__all__))
    missing = [name for name in qbb.__all__ if not hasattr(qbb, name)]
    assert missing == []


def test_suite_and_summary_helpers_are_public() -> None:
    assert "smoke" in SUITES
    assert "ghz" in BENCHMARK_BUILDERS
    assert build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 3}).name == "ghz"
    assert "name" in format_doctor_table(doctor_checks())
    assert build_suite("smoke")[0].name == "ghz"
    summary = summarize_results(
        [
            {
                "benchmark": "ghz",
                "backend": "cirq",
                "n_qubits": 3,
                "parameters": {"n_qubits": 3},
                "metrics": {"runtime_seconds": 1.0},
            }
        ]
    )
    assert "Summary" in format_summary(summary)
    assert "Compatibility" in format_compatibility_report()
    assert (
        results_to_records(
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 3,
                    "parameters": {},
                    "metrics": {},
                }
            ]
        )[0]["backend"]
        == "cirq"
    )


def test_translation_helpers_are_public() -> None:
    source = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
creg c[1];
h q[0];
measure q[0] -> c[0];
"""

    result = translate_circuit_source(source, from_format="openqasm", to_format="cirq")

    assert "cirq.H" in result.source
    assert callable(translation_check_report)


def test_hamiltonian_translation_helpers_are_public() -> None:
    source = """{
  "n_qubits": 1,
  "terms": [{"coefficient": 1.0, "paulis": {"0": "Z"}}]
}
"""

    result = translate_hamiltonian_source(
        source,
        from_format="pauli-json",
        to_format="cirq",
    )

    assert "cirq.Z" in result.source
    assert translation_capability_rows()[0]["pauli_hamiltonians"] is True


def test_workflow_translation_helpers_are_public() -> None:
    workflow = """{
  "n_qubits": 1,
  "parameters": ["theta"],
  "parameter_bindings": {"theta": 0.5},
  "operations": [{"gate": "RX", "targets": [0], "parameter": "theta"}],
  "measurements": [{"type": "counts", "targets": [0]}]
}
"""
    hamiltonian = """{
  "n_qubits": 1,
  "terms": [{"coefficient": 1.0, "paulis": {"0": "Z"}}]
}
"""

    workflow_result = translate_workflow_source(workflow, to_format="qiskit_aer")
    result_object = normalize_result_source(
        '{"counts": {"0": 1, "1": 1}, "shots": 2}',
        from_format="qiskit-counts-json",
    )

    assert 'Parameter("theta")' in workflow_result.source
    assert '"probabilities"' in result_object.source
    assert len(group_pauli_terms(hamiltonian, from_format="pauli-json")) == 1
