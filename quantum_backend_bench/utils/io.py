"""I/O helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def save_json(data: Any, path: str | Path) -> Path:
    """Save data as indented JSON."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return destination


def save_csv(results: list[dict[str, Any]], path: str | Path) -> Path:
    """Save benchmark results as a flat CSV table."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "benchmark",
        "backend",
        "case_label",
        "benchmark_family",
        "n_qubits",
        "shots",
        "repeats",
        "total_shots",
        "parameters",
        "runtime_seconds",
        "runtime_seconds_stddev",
        "depth",
        "gate_count",
        "two_qubit_gate_count",
        "success_probability",
        "total_variation_distance",
        "counts",
    ]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            metrics = result.get("metrics", {})
            metadata = result.get("metadata", {})
            writer.writerow(
                {
                    "benchmark": result.get("benchmark"),
                    "backend": result.get("backend"),
                    "case_label": metadata.get("case_label"),
                    "benchmark_family": metadata.get("benchmark_family"),
                    "n_qubits": result.get("n_qubits"),
                    "shots": result.get("shots"),
                    "repeats": result.get("repeats"),
                    "total_shots": result.get("total_shots"),
                    "parameters": json.dumps(result.get("parameters", {}), sort_keys=True),
                    "runtime_seconds": metrics.get("runtime_seconds"),
                    "runtime_seconds_stddev": metrics.get("runtime_seconds_stddev"),
                    "depth": metrics.get("depth"),
                    "gate_count": metrics.get("gate_count"),
                    "two_qubit_gate_count": metrics.get("two_qubit_gate_count"),
                    "success_probability": metrics.get("success_probability"),
                    "total_variation_distance": metrics.get("total_variation_distance"),
                    "counts": json.dumps(result.get("counts", {}), sort_keys=True),
                }
            )
    return destination
