"""Saved result diff tests."""

from __future__ import annotations

import json

from quantum_backend_bench.core.diff import (
    compare_result_sets,
    diff_passed,
    format_diff_table,
    load_result_file,
)
from quantum_backend_bench.utils.io import save_csv


def _result(
    runtime_seconds: float,
    success_probability: float = 1.0,
    *,
    backend: str = "cirq",
) -> dict:
    return {
        "benchmark": "ghz",
        "backend": backend,
        "n_qubits": 3,
        "shots": 32,
        "repeats": 1,
        "total_shots": 32,
        "parameters": {},
        "metrics": {
            "runtime_seconds": runtime_seconds,
            "success_probability": success_probability,
            "total_variation_distance": 0.0,
        },
        "counts": {"000": 16, "111": 16},
        "metadata": {"case_label": "ghz n=3"},
    }


def test_compare_result_sets_flags_regression_and_improvement() -> None:
    rows = compare_result_sets(
        [_result(0.1, success_probability=1.0)],
        [_result(0.2, success_probability=0.9)],
        metrics=["runtime_seconds", "success_probability"],
    )

    statuses = {row["metric"]: row["status"] for row in rows}
    assert statuses == {
        "runtime_seconds": "regressed",
        "success_probability": "regressed",
    }
    assert not diff_passed(rows)


def test_compare_result_sets_applies_relative_threshold() -> None:
    rows = compare_result_sets(
        [_result(1.0)],
        [_result(1.04)],
        metrics=["runtime_seconds"],
        relative_threshold=0.05,
    )

    assert rows[0]["status"] == "ok"
    assert diff_passed(rows)


def test_compare_result_sets_reports_new_and_missing_results() -> None:
    rows = compare_result_sets(
        [_result(0.1, backend="cirq")],
        [_result(0.1, backend="pennylane")],
        metrics=["runtime_seconds"],
    )

    assert [row["status"] for row in rows] == ["missing", "new"]


def test_load_result_file_accepts_json_bundle_and_csv(tmp_path) -> None:
    json_path = tmp_path / "results.json"
    csv_path = tmp_path / "results.csv"
    results = [_result(0.1)]
    json_path.write_text(json.dumps({"results": results}), encoding="utf-8")
    save_csv(results, csv_path)

    assert load_result_file(json_path)[0]["metrics"]["runtime_seconds"] == 0.1
    assert load_result_file(csv_path)[0]["metrics"]["runtime_seconds"] == 0.1


def test_format_diff_table_handles_empty_and_rows() -> None:
    assert format_diff_table([]) == "No comparable result metrics found."
    table = format_diff_table(
        compare_result_sets([_result(0.1)], [_result(0.2)], metrics=["runtime_seconds"])
    )
    assert "runtime_seconds" in table
    assert "regressed" in table
