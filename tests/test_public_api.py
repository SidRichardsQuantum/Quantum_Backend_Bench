"""Public API tests."""

from quantum_backend_bench import (
    BENCHMARK_BUILDERS,
    SUITES,
    build_benchmark_from_config,
    build_suite,
    doctor_checks,
    format_doctor_table,
    format_summary,
    summarize_results,
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
