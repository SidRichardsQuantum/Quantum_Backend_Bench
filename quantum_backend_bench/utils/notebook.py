"""Helpers for tutorial notebooks and lightweight result inspection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

from quantum_backend_bench.utils.io import save_csv, save_json

DEFAULT_NOTEBOOK_ARTIFACT_DIR = Path("../artifacts/notebooks")
DEFAULT_METRIC_FIELDS: tuple[tuple[str, str], ...] = (
    ("Depth", "depth"),
    ("Gate count", "gate_count"),
    ("Two-qubit gates", "two_qubit_gate_count"),
    ("Runtime seconds", "runtime_seconds"),
    ("Success probability", "success_probability"),
    ("Total variation distance", "total_variation_distance"),
)


def notebook_artifact_dir(path: str | Path = DEFAULT_NOTEBOOK_ARTIFACT_DIR) -> Path:
    """Create and return the default artifact directory used by notebooks."""

    destination = Path(path)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def format_ket(state: Any) -> str:
    """Format a computational basis state as ket notation."""

    text = str(state)
    if text.startswith("|") and text.endswith(">"):
        return text
    return f"|{text}>"


def save_result_artifacts(
    results: list[dict[str, Any]], stem: str, artifact_dir: str | Path | None = None
) -> tuple[Path, Path]:
    """Save notebook result JSON and CSV artifacts using a shared filename stem."""

    destination = notebook_artifact_dir() if artifact_dir is None else Path(artifact_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = save_json(results, destination / f"{stem}.json")
    csv_path = save_csv(results, destination / f"{stem}.csv")
    return json_path, csv_path


def total_counts(result: dict[str, Any]) -> int:
    """Return the total number of measured counts in a result."""

    return int(sum(result.get("counts", {}).values()))


def rounded_or_none(value: Any, digits: int = 6) -> Any:
    """Round floats while preserving None and non-float values."""

    if value is None:
        return None
    if isinstance(value, float):
        return round(value, digits)
    return value


def print_metric_summary(
    result: dict[str, Any], fields: Sequence[tuple[str, str]] = DEFAULT_METRIC_FIELDS
) -> None:
    """Print a compact metric list for one benchmark result."""

    metrics = result["metrics"]
    print("\nKey metrics")
    for label, key in fields:
        print(f"- {label}: {rounded_or_none(metrics.get(key))}")


def top_measurement_states(result: dict[str, Any], top_k: int = 4) -> list[dict[str, Any]]:
    """Return top measured states with ket labels, counts, and probabilities."""

    counts = result.get("counts", {})
    shots = total_counts(result)
    states = sorted(counts, key=counts.get, reverse=True)[:top_k]
    return [
        {
            "state": state,
            "ket": format_ket(state),
            "count": counts[state],
            "probability": counts[state] / shots if shots else 0.0,
        }
        for state in states
    ]


def top_measurement_states_frame(
    result: dict[str, Any], top_k: int = 8, *, sort_by_state: bool = False
) -> Any:
    """Return a pandas DataFrame of top measured states and probabilities."""

    pd = _pandas()
    distribution = result["metrics"].get("measurement_distribution") or {}
    states = sorted(distribution, key=lambda state: distribution[state], reverse=True)[:top_k]
    if sort_by_state:
        states = sorted(states, key=_state_sort_key)
    return pd.DataFrame(
        [
            {"state": format_ket(state), "probability": round(distribution[state], 6)}
            for state in states
        ]
    )


def measurement_distribution_series(result: dict[str, Any]) -> Any:
    """Return a pandas Series for a result distribution with sorted ket labels."""

    pd = _pandas()
    distribution = result["metrics"].get("measurement_distribution") or {}
    states = sorted(distribution, key=_state_sort_key)
    return pd.Series(
        [distribution[state] for state in states], index=[format_ket(state) for state in states]
    )


def verification_frame(checks: Iterable[dict[str, Any]]) -> Any:
    """Return a pandas DataFrame for notebook verification checks."""

    return _pandas().DataFrame(list(checks))


def check_total_counts(result: dict[str, Any], expected: int | None = None) -> dict[str, Any]:
    """Build a verification row for total measured counts."""

    actual = total_counts(result)
    target = result.get("total_shots", result.get("shots")) if expected is None else expected
    return {
        "check": "total counts equals shots",
        "value": actual,
        "expected": target,
        "passed": actual == target,
    }


def check_ghz_support(
    result: dict[str, Any], expected_states: set[str] | None = None
) -> dict[str, Any]:
    """Build a verification row for ideal GHZ support states."""

    n_qubits = int(result.get("n_qubits", 0))
    states = expected_states or {"0" * n_qubits, "1" * n_qubits}
    observed = set(result.get("counts", {}))
    return {
        "check": "GHZ support is only |0...0>/|1...1>",
        "value": ", ".join(format_ket(state) for state in sorted(observed, key=_state_sort_key)),
        "expected": ", ".join(format_ket(state) for state in sorted(states, key=_state_sort_key)),
        "passed": observed <= states,
    }


def check_runtime_samples(result: dict[str, Any], expected: int | None = None) -> dict[str, Any]:
    """Build a verification row for captured runtime samples."""

    samples = result.get("metadata", {}).get("runtime_seconds_samples", [])
    if expected is None:
        return {
            "check": "runtime sample captured",
            "value": len(samples),
            "expected": ">= 1",
            "passed": bool(samples),
        }
    return {
        "check": "runtime samples match repeats",
        "value": len(samples),
        "expected": expected,
        "passed": len(samples) == expected,
    }


def check_success_probability(
    result: dict[str, Any], expected: float = 1.0, digits: int = 6
) -> dict[str, Any]:
    """Build a verification row for an exact success-probability expectation."""

    actual = result["metrics"].get("success_probability")
    return {
        "check": "success probability",
        "value": rounded_or_none(actual, digits),
        "expected": expected,
        "passed": actual == expected,
    }


def _pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            'pandas is not installed. Install with: pip install "quantum-backend-bench[notebooks]"'
        ) from exc
    return pd


def _state_sort_key(state: Any) -> tuple[int, int | str]:
    text = str(state)
    if set(text).issubset({"0", "1"}):
        return (len(text), int(text, 2))
    return (len(text), text)
