"""Formatting helpers for CLI output."""

from __future__ import annotations

from typing import Any

from quantum_backend_bench.core.discovery import result_case_label


def format_results_table(results: list[dict[str, Any]]) -> str:
    """Render a small plain-text table."""

    headers = [
        "case",
        "backend",
        "runtime_seconds",
        "runtime_stddev",
        "depth",
        "gate_count",
        "two_qubit_gate_count",
        "success_prob",
    ]
    rows = []
    for result in results:
        metrics = result["metrics"]
        rows.append(
            [
                result_case_label(result),
                result["backend"],
                _fmt(metrics.get("runtime_seconds")),
                _fmt(metrics.get("runtime_seconds_stddev")),
                _fmt(metrics.get("depth")),
                _fmt(metrics.get("gate_count")),
                _fmt(metrics.get("two_qubit_gate_count")),
                _fmt(metrics.get("success_probability")),
            ]
        )
    widths = [
        max(len(str(value)) for value in [header, *column])
        for header, column in zip(headers, zip(*rows, strict=False))
    ]
    lines = [
        " | ".join(header.ljust(width) for header, width in zip(headers, widths)),
        "-+-".join("-" * width for width in widths),
    ]
    for row in rows:
        lines.append(" | ".join(str(value).ljust(width) for value, width in zip(row, widths)))
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)
