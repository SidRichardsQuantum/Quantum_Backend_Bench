"""Standardized metric helpers."""

from __future__ import annotations

from collections import Counter
from typing import Iterable


def normalize_counts(counts: dict[str, int], shots: int | None = None) -> dict[str, float]:
    """Convert integer counts to a normalized distribution."""

    total = shots if shots is not None else sum(counts.values())
    if total <= 0:
        return {}
    return {state: value / total for state, value in sorted(counts.items())}


def success_probability(
    counts: dict[str, int], target_state: str, shots: int | None = None
) -> float | None:
    """Return the empirical probability of a target bitstring."""

    if not counts:
        return None
    total = shots if shots is not None else sum(counts.values())
    if total <= 0:
        return None
    return counts.get(target_state, 0) / total


def total_variation_distance(
    observed: dict[str, float] | dict[str, int],
    ideal: dict[str, float] | None,
    shots: int | None = None,
) -> float | None:
    """Compute total variation distance between two distributions."""

    if ideal is None:
        return None
    observed_distribution = (
        normalize_counts(observed, shots=shots) if _looks_like_counts(observed) else dict(observed)
    )
    keys = set(observed_distribution) | set(ideal)
    return 0.5 * sum(abs(observed_distribution.get(key, 0.0) - ideal.get(key, 0.0)) for key in keys)


def summarize_gate_count(gates: Iterable[str]) -> Counter[str]:
    """Count operations by gate name."""

    return Counter(gates)


def _looks_like_counts(values: dict[str, float] | dict[str, int]) -> bool:
    return all(isinstance(value, int) for value in values.values())
