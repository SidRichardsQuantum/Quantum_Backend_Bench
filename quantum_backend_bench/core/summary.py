"""Result summary helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

LOWER_IS_BETTER = {
    "runtime_seconds": "fastest_backend",
    "depth": "lowest_depth_backend",
    "total_variation_distance": "lowest_tvd_backend",
}
HIGHER_IS_BETTER = {
    "success_probability": "best_success_backend",
}


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize benchmark results by benchmark and parameter set."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[_group_key(result)].append(result)

    groups = []
    for key in sorted(grouped):
        group_results = grouped[key]
        first = group_results[0]
        summary: dict[str, Any] = {
            "benchmark": first["benchmark"],
            "n_qubits": first["n_qubits"],
            "parameters": first.get("parameters", {}),
            "runs": len(group_results),
        }
        for metric, label in LOWER_IS_BETTER.items():
            winner = _select_best(group_results, metric, reverse=False)
            if winner is not None:
                summary[label] = winner
        for metric, label in HIGHER_IS_BETTER.items():
            winner = _select_best(group_results, metric, reverse=True)
            if winner is not None:
                summary[label] = winner
        groups.append(summary)

    return {"groups": groups}


def format_summary(summary: dict[str, Any]) -> str:
    """Format a compact textual summary."""

    groups = summary.get("groups", [])
    if not groups:
        return "No results to summarize."

    lines = ["Summary"]
    for group in groups:
        label = _case_label(group)
        details = []
        for key in (
            "fastest_backend",
            "lowest_depth_backend",
            "best_success_backend",
            "lowest_tvd_backend",
        ):
            winner = group.get(key)
            if winner is not None:
                details.append(f"{key}={winner['backend']} ({winner['value']})")
        lines.append(f"- {label}: " + "; ".join(details or ["no comparable metrics"]))
    return "\n".join(lines)


def _group_key(result: dict[str, Any]) -> str:
    params = result.get("parameters", {})
    parameter_key = tuple(sorted((str(key), repr(value)) for key, value in params.items()))
    return repr((result.get("benchmark"), result.get("n_qubits"), parameter_key))


def _select_best(
    results: list[dict[str, Any]], metric: str, reverse: bool
) -> dict[str, Any] | None:
    candidates = [
        (result["metrics"].get(metric), result)
        for result in results
        if result.get("metrics", {}).get(metric) is not None
    ]
    if not candidates:
        return None
    value, result = sorted(candidates, key=lambda candidate: candidate[0], reverse=reverse)[0]
    return {"backend": result["backend"], "value": value}


def _case_label(group: dict[str, Any]) -> str:
    params = group.get("parameters", {})
    extras = ", ".join(f"{key}={value}" for key, value in sorted(params.items()))
    if extras:
        return f"{group['benchmark']}({extras})"
    return f"{group['benchmark']}(n_qubits={group['n_qubits']})"
