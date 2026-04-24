"""Plotting helper tests."""

from quantum_backend_bench.utils.plotting import _case_label, _ket, _select_states


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
