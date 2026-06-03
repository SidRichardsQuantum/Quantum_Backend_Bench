"""Notebook helper tests."""

from __future__ import annotations

from quantum_backend_bench.utils.notebook import (
    check_ghz_support,
    check_runtime_samples,
    check_success_probability,
    check_total_counts,
    format_ket,
    measurement_distribution_series,
    top_measurement_states,
    total_counts,
)


def _result() -> dict:
    return {
        "backend": "fake",
        "n_qubits": 3,
        "shots": 8,
        "total_shots": 8,
        "counts": {"111": 5, "000": 3},
        "metrics": {
            "measurement_distribution": {"111": 0.625, "000": 0.375},
            "success_probability": 1.0,
        },
        "metadata": {"runtime_seconds_samples": [0.1]},
    }


def test_format_ket_is_idempotent() -> None:
    assert format_ket("101") == "|101>"
    assert format_ket("|101>") == "|101>"


def test_top_measurement_states_include_probabilities() -> None:
    states = top_measurement_states(_result())
    assert states[0] == {"state": "111", "ket": "|111>", "count": 5, "probability": 0.625}
    assert total_counts(_result()) == 8


def test_measurement_distribution_series_uses_sorted_kets() -> None:
    series = measurement_distribution_series(_result())
    assert list(series.index) == ["|000>", "|111>"]
    assert list(series) == [0.375, 0.625]


def test_verification_checks() -> None:
    result = _result()
    assert check_total_counts(result)["passed"] is True
    assert check_ghz_support(result)["passed"] is True
    assert check_runtime_samples(result)["passed"] is True
    assert check_success_probability(result)["passed"] is True


def test_notebook_module_is_exported_from_utils_package() -> None:
    from quantum_backend_bench import utils

    assert utils.notebook.format_ket("11") == "|11>"
