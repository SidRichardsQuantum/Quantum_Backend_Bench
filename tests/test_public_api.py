"""Public API tests."""

from quantum_backend_bench import SUITES, build_suite, format_summary, summarize_results


def test_suite_and_summary_helpers_are_public() -> None:
    assert "smoke" in SUITES
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
