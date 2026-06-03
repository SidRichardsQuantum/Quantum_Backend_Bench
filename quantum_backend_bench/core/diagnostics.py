"""Result diagnostics for SDK parity checks."""

from __future__ import annotations

from itertools import combinations
from typing import Any


def diagnose_result_parity(results: list[dict[str, Any]]) -> list[str]:
    """Return human-readable explanations for likely backend disagreement causes."""

    findings: list[str] = []
    for left, right in combinations(results, 2):
        if left.get("benchmark") != right.get("benchmark"):
            continue
        label = f"{left.get('backend')} vs {right.get('backend')} / {left.get('benchmark')}"
        left_counts = left.get("counts") or {}
        right_counts = right.get("counts") or {}
        if set(left_counts) != set(right_counts):
            findings.append(f"{label}: observed bitstring sets differ.")
            if _reverse_keys(left_counts) == set(right_counts):
                findings.append(
                    f"{label}: bitstrings match after reversal; check endian convention."
                )
        left_meta = left.get("metadata") or {}
        right_meta = right.get("metadata") or {}
        for key, message in (
            ("noise_applied", "noise application differs"),
            ("runtime_includes_transpilation", "runtime includes transpilation for only one side"),
            ("external_process", "only one side uses an external local runtime"),
            ("seed_applied", "seed application differs"),
        ):
            if left_meta.get(key) != right_meta.get(key):
                findings.append(f"{label}: {message}.")
        if _metric_delta(left, right, "total_variation_distance") > 0.05:
            findings.append(f"{label}: total variation distance differs by more than 0.05.")
        if _metric_delta(left, right, "success_probability") > 0.05:
            findings.append(f"{label}: success probability differs by more than 0.05.")
    return findings or ["No obvious SDK parity issues detected in the supplied results."]


def _reverse_keys(counts: dict[str, Any]) -> set[str]:
    return {key[::-1] for key in counts}


def _metric_delta(left: dict[str, Any], right: dict[str, Any], metric: str) -> float:
    left_value = left.get(metric)
    right_value = right.get(metric)
    if left_value is None or right_value is None:
        return 0.0
    return abs(float(left_value) - float(right_value))
