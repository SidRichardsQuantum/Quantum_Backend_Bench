"""Helpers for converting benchmark results into tabular data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantum_backend_bench.core.diff import load_result_file
from quantum_backend_bench.core.discovery import result_case_label


def results_to_records(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten benchmark result dictionaries into analysis-friendly records."""

    records: list[dict[str, Any]] = []
    for result in results:
        metrics = result.get("metrics", {}) or {}
        metadata = result.get("metadata", {}) or {}
        record = {
            "benchmark": result.get("benchmark"),
            "backend": result.get("backend"),
            "case_label": result_case_label(result),
            "benchmark_family": metadata.get("benchmark_family"),
            "n_qubits": result.get("n_qubits"),
            "shots": result.get("shots"),
            "repeats": result.get("repeats"),
            "total_shots": result.get("total_shots"),
            "runtime_seconds": metrics.get("runtime_seconds"),
            "runtime_seconds_stddev": metrics.get("runtime_seconds_stddev"),
            "runtime_seconds_min": metrics.get("runtime_seconds_min"),
            "runtime_seconds_max": metrics.get("runtime_seconds_max"),
            "compile_seconds": metrics.get("compile_seconds"),
            "compile_seconds_stddev": metrics.get("compile_seconds_stddev"),
            "compiled_depth": metrics.get("compiled_depth"),
            "compiled_gate_count": metrics.get("compiled_gate_count"),
            "compiled_two_qubit_gate_count": metrics.get("compiled_two_qubit_gate_count"),
            "depth": metrics.get("depth"),
            "gate_count": metrics.get("gate_count"),
            "two_qubit_gate_count": metrics.get("two_qubit_gate_count"),
            "success_probability": metrics.get("success_probability"),
            "total_variation_distance": metrics.get("total_variation_distance"),
            "noise_level": metadata.get("noise_level"),
            "noise_requested": metadata.get("noise_requested"),
            "noise_supported": metadata.get("noise_supported"),
            "noise_applied": metadata.get("noise_applied"),
            "seed": metadata.get("seed"),
            "runtime_includes_transpilation": metadata.get("runtime_includes_transpilation"),
            "compile_toolchain": metadata.get("compile_toolchain"),
            "compiled_basis_gates": json.dumps(
                metadata.get("compiled_basis_gates") or {}, sort_keys=True
            ),
            "external_process": metadata.get("external_process"),
            "local_only": metadata.get("local_only"),
            "parameters": json.dumps(result.get("parameters", {}) or {}, sort_keys=True),
            "counts": json.dumps(result.get("counts", {}) or {}, sort_keys=True),
        }
        records.append(record)
    return records


def results_to_dataframe(results: list[dict[str, Any]] | str | Path):
    """Return benchmark results as a pandas DataFrame.

    ``results`` may be an in-memory result list or a saved JSON/CSV result path.
    """

    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            'pandas is not installed. Install with: pip install "quantum-backend-bench[notebooks]"'
        ) from exc

    loaded = load_result_file(results) if isinstance(results, (str, Path)) else results
    return pd.DataFrame(results_to_records(list(loaded)))
