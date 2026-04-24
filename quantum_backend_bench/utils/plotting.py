"""Matplotlib plotting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def save_runtime_depth_plot(results: list[dict[str, Any]], path: str | Path) -> Path:
    """Save a side-by-side runtime and depth comparison chart."""

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            'matplotlib is not installed. Install with: pip install "quantum-backend-bench[plot]"'
        ) from exc

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
