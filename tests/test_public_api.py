"""Public API tests."""

from quantum_backend_bench import (
    BENCHMARK_BUILDERS,
    SUITES,
    build_benchmark_from_config,
    build_suite,
    doctor_checks,
    format_compatibility_report,
    format_doctor_table,
    format_summary,
    results_to_records,
    summarize_results,
    translate_circuit_source,
    translation_check_report,
)


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
