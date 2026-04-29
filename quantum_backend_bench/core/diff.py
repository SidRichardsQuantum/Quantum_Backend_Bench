"""Compare saved benchmark result sets."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from quantum_backend_bench.core.summary import HIGHER_IS_BETTER, LOWER_IS_BETTER

DEFAULT_DIFF_METRICS = [
    "runtime_seconds",
    "success_probability",
    "total_variation_distance",
]

REGRESSION_STATUSES = {"missing", "regressed"}


def load_result_file(path: str | Path) -> list[dict[str, Any]]:
    """Load benchmark results from a saved JSON bundle/list or flat CSV export."""

    source = Path(path)
    if source.suffix.lower() == ".csv":
        return _load_csv_results(source)
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        data = data["results"]
    if not isinstance(data, list):
        raise ValueError("Result JSON must contain a result list or an object with a results list.")
    return data


def compare_result_sets(
    baseline: list[dict[str, Any]],
    candidate: list[dict[str, Any]],
    metrics: list[str] | None = None,
    *,
    absolute_threshold: float = 0.0,
    relative_threshold: float = 0.0,
) -> list[dict[str, Any]]:
    """Compare matching results and return per-metric deltas."""

    selected_metrics = metrics or DEFAULT_DIFF_METRICS
    baseline_index = {_result_key(result): result for result in baseline}
    candidate_index = {_result_key(result): result for result in candidate}
    rows = []

    for key in sorted(baseline_index):
        base_result = baseline_index[key]
        candidate_result = candidate_index.get(key)
        for metric in selected_metrics:
            row = _compare_metric(
                key,
                metric,
                base_result,
                candidate_result,
                absolute_threshold=absolute_threshold,
                relative_threshold=relative_threshold,
            )
            if row is not None:
                rows.append(row)

    for key in sorted(set(candidate_index) - set(baseline_index)):
        new_result = candidate_index[key]
        for metric in selected_metrics:
            value = _metric_value(new_result, metric)
            if value is not None:
                rows.append(
                    {
                        **_key_fields(key),
                        "metric": metric,
                        "baseline": None,
                        "candidate": value,
                        "delta": None,
                        "relative_delta": None,
                        "status": "new",
                    }
                )

    return rows


def diff_passed(rows: list[dict[str, Any]]) -> bool:
    """Return whether a diff has no missing or regressed rows."""

    return not any(row["status"] in REGRESSION_STATUSES for row in rows)


def format_diff_table(rows: list[dict[str, Any]]) -> str:
    """Render a compact plain-text diff table."""

    if not rows:
        return "No comparable result metrics found."
    headers = [
        "case",
        "backend",
        "metric",
        "baseline",
        "candidate",
        "delta",
        "relative_delta",
        "status",
    ]
    table_rows = [
        [
            row["case"],
            row["backend"],
            row["metric"],
            _fmt(row["baseline"]),
            _fmt(row["candidate"]),
            _fmt(row["delta"]),
            _fmt_relative(row["relative_delta"]),
            row["status"],
        ]
        for row in rows
    ]
    widths = [
        max(len(str(value)) for value in [header, *column])
        for header, column in zip(headers, zip(*table_rows, strict=False))
    ]
    lines = [
        " | ".join(header.ljust(width) for header, width in zip(headers, widths)),
        "-+-".join("-" * width for width in widths),
    ]
    for row in table_rows:
        lines.append(" | ".join(str(value).ljust(width) for value, width in zip(row, widths)))
    return "\n".join(lines)


def _compare_metric(
    key: tuple[str, str, int | None, str],
    metric: str,
    base_result: dict[str, Any],
    candidate_result: dict[str, Any] | None,
    *,
    absolute_threshold: float,
    relative_threshold: float,
) -> dict[str, Any] | None:
    base_value = _metric_value(base_result, metric)
    if base_value is None:
        return None
    if candidate_result is None:
        return {
            **_key_fields(key),
            "metric": metric,
            "baseline": base_value,
            "candidate": None,
            "delta": None,
            "relative_delta": None,
            "status": "missing",
        }
    candidate_value = _metric_value(candidate_result, metric)
    if candidate_value is None:
        return {
            **_key_fields(key),
            "metric": metric,
            "baseline": base_value,
            "candidate": None,
            "delta": None,
            "relative_delta": None,
            "status": "missing",
        }

    delta = candidate_value - base_value
    relative_delta = None if base_value == 0 else delta / abs(base_value)
    tolerance = absolute_threshold + abs(base_value) * relative_threshold
    status = _status(metric, delta, tolerance)
    return {
        **_key_fields(key),
        "metric": metric,
        "baseline": base_value,
        "candidate": candidate_value,
        "delta": delta,
        "relative_delta": relative_delta,
        "status": status,
    }


def _status(metric: str, delta: float, tolerance: float) -> str:
    if abs(delta) <= tolerance:
        return "ok"
    if metric in HIGHER_IS_BETTER:
        return "improved" if delta > 0 else "regressed"
    if metric in LOWER_IS_BETTER:
        return "improved" if delta < 0 else "regressed"
    return "changed"


def _load_csv_results(path: Path) -> list[dict[str, Any]]:
    results = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            parameters = _loads_json_field(row.get("parameters"), default={})
            counts = _loads_json_field(row.get("counts"), default={})
            metrics = {
                key: _number_or_none(row.get(key))
                for key in (
                    "runtime_seconds",
                    "runtime_seconds_stddev",
                    "depth",
                    "gate_count",
                    "two_qubit_gate_count",
                    "success_probability",
                    "total_variation_distance",
                )
            }
            results.append(
                {
                    "benchmark": row.get("benchmark"),
                    "backend": row.get("backend"),
                    "n_qubits": _int_or_none(row.get("n_qubits")),
                    "shots": _int_or_none(row.get("shots")),
                    "repeats": _int_or_none(row.get("repeats")),
                    "total_shots": _int_or_none(row.get("total_shots")),
                    "parameters": parameters,
                    "metrics": metrics,
                    "counts": counts,
                    "metadata": {
                        "case_label": row.get("case_label") or None,
                        "benchmark_family": row.get("benchmark_family") or None,
                    },
                }
            )
    return results


def _result_key(result: dict[str, Any]) -> tuple[str, str, int | None, str]:
    parameters = json.dumps(result.get("parameters", {}), sort_keys=True)
    return (
        str(result.get("benchmark")),
        str(result.get("backend")),
        _int_or_none(result.get("n_qubits")),
        parameters,
    )


def _key_fields(key: tuple[str, str, int | None, str]) -> dict[str, Any]:
    benchmark, backend, n_qubits, parameters = key
    parsed_parameters = json.loads(parameters)
    return {
        "case": _case_label(benchmark, n_qubits, parsed_parameters),
        "backend": backend,
        "benchmark": benchmark,
        "n_qubits": n_qubits,
        "parameters": parsed_parameters,
    }


def _case_label(benchmark: str, n_qubits: int | None, parameters: dict[str, Any]) -> str:
    if parameters:
        extras = ", ".join(f"{key}={value}" for key, value in sorted(parameters.items()))
        return f"{benchmark}({extras})"
    return f"{benchmark}(n_qubits={n_qubits})"


def _metric_value(result: dict[str, Any], metric: str) -> float | None:
    value = result.get("metrics", {}).get(metric)
    number = _number_or_none(value)
    return float(number) if number is not None else None


def _loads_json_field(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def _number_or_none(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _fmt_relative(value: Any) -> str:
    if value is None:
        return "None"
    return f"{value:.2%}"
