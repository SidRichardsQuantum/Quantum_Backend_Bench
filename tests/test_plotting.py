"""Plotting helper tests."""

import pytest

from quantum_backend_bench.utils.plotting import (
    _case_label,
    _ket,
    _select_states,
    save_counts_heatmap,
    save_distribution_plot,
    save_noise_quality_plot,
    save_suite_runtime_plot,
)


def test_ket_formats_bitstring_states() -> None:
    assert _ket("101") == "|101>"
    assert _ket("|101>") == "|101>"


def test_case_label_uses_ket_for_oracle_states() -> None:
    assert (
        _case_label(
            {
                "benchmark": "bernstein_vazirani",
                "backend": "cirq",
                "n_qubits": 4,
                "parameters": {"secret_string": "101"},
            }
        )
        == "bernstein_vazirani s=|101>"
    )
    assert (
        _case_label(
            {
                "benchmark": "deutsch_jozsa",
                "backend": "cirq",
                "n_qubits": 4,
                "parameters": {"oracle_type": "balanced", "bitmask": "101"},
            }
        )
        == "deutsch_jozsa m=|101>"
    )


def test_select_states_preserves_basis_order_after_top_k_selection() -> None:
    states = _select_states({"111": 0.9, "001": 0.8, "010": 0.7, "000": 0.1}, top_k=3)
    assert states == ["001", "010", "111"]


@pytest.mark.parametrize(
    ("plotter", "filename", "results"),
    [
        (
            save_distribution_plot,
            "distribution.png",
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 2,
                    "parameters": {"n_qubits": 2},
                    "metrics": {"measurement_distribution": {"00": 0.5, "11": 0.5}},
                }
            ],
        ),
        (
            save_counts_heatmap,
            "heatmap.png",
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 2,
                    "parameters": {"n_qubits": 2},
                    "metrics": {"measurement_distribution": {"00": 0.5, "11": 0.5}},
                }
            ],
        ),
        (
            save_suite_runtime_plot,
            "suite.png",
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 2,
                    "parameters": {"n_qubits": 2},
                    "metrics": {"runtime_seconds": 0.1},
                }
            ],
        ),
        (
            save_noise_quality_plot,
            "quality.png",
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 2,
                    "parameters": {"n_qubits": 2, "noise_level": 0.0},
                    "metrics": {
                        "total_variation_distance": 0.0,
                        "success_probability": 1.0,
                    },
                },
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 2,
                    "parameters": {"n_qubits": 2, "noise_level": 0.01},
                    "metrics": {
                        "total_variation_distance": 0.1,
                        "success_probability": 0.9,
                    },
                },
            ],
        ),
    ],
)
def test_plot_helpers_write_files(plotter, filename: str, results: list[dict], tmp_path) -> None:
    pytest.importorskip("matplotlib")

    output_path = tmp_path / filename
    saved_path = plotter(results, output_path)

    assert saved_path == output_path
    assert output_path.stat().st_size > 0
