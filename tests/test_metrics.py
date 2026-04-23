"""Metric tests."""

import pytest

from quantum_backend_bench.core.metrics import (
    normalize_counts,
    success_probability,
    total_variation_distance,
)


def test_normalize_counts() -> None:
    assert normalize_counts({"00": 2, "11": 2}) == {"00": 0.5, "11": 0.5}


def test_success_probability() -> None:
    assert success_probability({"101": 9, "000": 1}, "101") == 0.9


def test_total_variation_distance() -> None:
    distance = total_variation_distance({"00": 6, "11": 4}, {"00": 0.5, "11": 0.5}, shots=10)
    assert distance == pytest.approx(0.1)
