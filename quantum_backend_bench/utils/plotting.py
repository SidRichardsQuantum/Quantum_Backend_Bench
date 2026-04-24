"""Matplotlib plotting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantum_backend_bench.core.discovery import result_case_label


def _pyplot() -> Any:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            'matplotlib is not installed. Install with: pip install "quantum-backend-bench[plot]"'
        ) from exc
    return plt


def save_runtime_depth_plot(results: list[dict[str, Any]], path: str | Path) -> Path:
    """Save a side-by-side runtime and depth comparison chart."""

    plt = _pyplot()

    labels = [result["backend"] for result in results]
    runtimes = [result["metrics"].get("runtime_seconds") or 0.0 for result in results]
    depths = [result["metrics"].get("depth") or 0.0 for result in results]

    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(labels, runtimes, color="#2a9d8f")
    axes[0].set_title("Runtime (s)")
    axes[0].set_ylabel("seconds")
    axes[1].bar(labels, depths, color="#e76f51")
    axes[1].set_title("Circuit Depth")
    axes[1].set_ylabel("depth")
    figure.tight_layout()

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return destination


def save_distribution_plot(
    results: list[dict[str, Any]], path: str | Path, top_k: int = 16
) -> Path:
    """Save measured probability distributions as horizontal bar charts."""

    plt = _pyplot()
    if not results:
        raise ValueError("No results to plot.")

    figure, axes = plt.subplots(len(results), 1, figsize=(9, max(3, 2.7 * len(results))))
    if len(results) == 1:
        axes = [axes]

    for axis, result in zip(axes, results, strict=True):
        distribution = result["metrics"].get("measurement_distribution") or {}
        top_states = _select_states(distribution, top_k=top_k)
        labels = [_ket(state) for state in reversed(top_states)]
        values = [distribution[state] for state in reversed(top_states)]
        axis.barh(labels, values, color="#457b9d")
        axis.set_xlim(0.0, 1.0)
        axis.set_xlabel("probability")
        axis.set_title(_result_label(result))

    figure.tight_layout()
    return _save_figure(plt, figure, path)


def save_noise_quality_plot(results: list[dict[str, Any]], path: str | Path) -> Path:
    """Save noise level vs quality metrics for noise-sweep results."""

    plt = _pyplot()
    noise_results = [
        result for result in results if result.get("parameters", {}).get("noise_level") is not None
    ]
    if not noise_results:
        raise ValueError("No noise_level parameters found in results.")

    grouped = _group_by_backend(noise_results)
    metrics = [
        (
            "total_variation_distance",
            "Noise vs TVD",
            "total variation distance",
        ),
        ("success_probability", "Noise vs Success", "success probability"),
    ]
    available_metrics = [
        metric
        for metric in metrics
        if any(result["metrics"].get(metric[0]) is not None for result in noise_results)
    ]
    if not available_metrics:
        raise ValueError("No TVD or success probability metrics found in noise results.")

    figure, axes = plt.subplots(
        1, len(available_metrics), figsize=(5.5 * len(available_metrics), 4)
    )
    if len(available_metrics) == 1:
        axes = [axes]

    for axis, (metric_key, title, ylabel) in zip(axes, available_metrics, strict=True):
        for backend, backend_results in grouped.items():
            ordered = sorted(
                backend_results, key=lambda result: result["parameters"]["noise_level"]
            )
            values = [result["metrics"].get(metric_key) for result in ordered]
            if any(value is not None for value in values):
                levels = [100.0 * result["parameters"]["noise_level"] for result in ordered]
                axis.plot(levels, [value or 0.0 for value in values], marker="o", label=backend)
        axis.set_title(title)
        axis.set_xlabel("noise level (%)")
        axis.set_ylabel(ylabel)

    for axis in axes:
        axis.set_ylim(bottom=0.0)
        if axis.has_data():
            axis.legend()
    figure.tight_layout()
    return _save_figure(plt, figure, path)


def save_suite_runtime_plot(results: list[dict[str, Any]], path: str | Path) -> Path:
    """Save a grouped runtime chart for suite or multi-benchmark results."""

    plt = _pyplot()
    if not results:
        raise ValueError("No results to plot.")

    labels = [_case_label(result) for result in results]
    runtimes = [result["metrics"].get("runtime_seconds") or 0.0 for result in results]
    colors = [_backend_color(result["backend"]) for result in results]

    figure, axis = plt.subplots(figsize=(max(8, 0.65 * len(results)), 4.8))
    axis.bar(range(len(results)), runtimes, color=colors)
    axis.set_xticks(range(len(results)))
    axis.set_xticklabels(labels, rotation=45, ha="right")
    axis.set_ylabel("seconds")
    axis.set_title("Runtime by Benchmark and Backend")
    for backend in sorted({result["backend"] for result in results}):
        axis.bar([], [], color=_backend_color(backend), label=backend)
    axis.legend(title="backend")
    figure.tight_layout()
    return _save_figure(plt, figure, path)


def save_counts_heatmap(results: list[dict[str, Any]], path: str | Path, top_k: int = 16) -> Path:
    """Save a top-k bitstring probability heatmap."""

    plt = _pyplot()
    if not results:
        raise ValueError("No results to plot.")

    states = _top_states(results, top_k=top_k)
    columns = [_result_label(result) for result in results]
    matrix = [
        [
            (result["metrics"].get("measurement_distribution") or {}).get(state, 0.0)
            for result in results
        ]
        for state in states
    ]

    figure, axis = plt.subplots(figsize=(max(7, 0.75 * len(results)), max(4, 0.35 * len(states))))
    image = axis.imshow(matrix, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    axis.set_xticks(range(len(columns)))
    axis.set_xticklabels(columns, rotation=45, ha="right")
    axis.set_yticks(range(len(states)))
    axis.set_yticklabels([_ket(state) for state in states])
    axis.set_title("Top Bitstring Probabilities")
    axis.set_xlabel("result")
    axis.set_ylabel("bitstring")
    figure.colorbar(image, ax=axis, label="probability")
    figure.tight_layout()
    return _save_figure(plt, figure, path)


def _save_figure(plt: Any, figure: Any, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return destination


def _result_label(result: dict[str, Any]) -> str:
    return f"{_case_label(result)} / {result['backend']}"


def _case_label(result: dict[str, Any]) -> str:
    return result_case_label(result)


def _group_by_backend(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(result["backend"], []).append(result)
    return grouped


def _backend_color(backend: str) -> str:
    return {
        "cirq": "#2a9d8f",
        "pennylane": "#e76f51",
        "braket_local": "#457b9d",
        "qiskit_aer": "#6f4bb2",
        "cudaq": "#76b900",
        "pyquil_qvm": "#9c6644",
        "qutip": "#bc5090",
    }.get(backend, "#6c757d")


def _top_states(results: list[dict[str, Any]], top_k: int) -> list[str]:
    totals: dict[str, float] = {}
    for result in results:
        distribution = result["metrics"].get("measurement_distribution") or {}
        for state, probability in distribution.items():
            totals[state] = totals.get(state, 0.0) + probability
    return _select_states(totals, top_k=top_k)


def _select_states(distribution: dict[str, float], top_k: int) -> list[str]:
    selected = sorted(distribution, key=lambda state: distribution[state], reverse=True)[:top_k]
    return sorted(selected, key=_state_sort_key)


def _state_sort_key(state: str) -> tuple[int, int | str]:
    if set(state).issubset({"0", "1"}):
        return (len(state), int(state, 2))
    return (len(state), state)


def _ket(state: Any) -> str:
    text = str(state)
    if text.startswith("|") and text.endswith(">"):
        return text
    return f"|{text}>"
