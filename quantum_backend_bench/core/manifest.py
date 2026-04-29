"""Experiment manifest loading and execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantum_backend_bench.benchmarks.noise_sensitivity import (
    build_benchmark as build_noise_benchmarks,
)
from quantum_backend_bench.core.environment import capture_environment
from quantum_backend_bench.core.factory import build_benchmark_from_config
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.utils.io import save_csv, save_json
from quantum_backend_bench.utils.plotting import save_suite_runtime_plot


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load a JSON or YAML experiment manifest."""

    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        data = json.loads(text)
    elif source.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "YAML manifests require PyYAML. Install it directly with: pip install pyyaml"
            ) from exc
        data = yaml.safe_load(text)
    else:
        raise ValueError("Experiment manifest must use .json, .yaml, or .yml.")
    if not isinstance(data, dict):
        raise ValueError("Experiment manifest must contain an object at the top level.")
    return data


def run_experiment_manifest(path: str | Path) -> dict[str, Any]:
    """Run an experiment manifest and return a complete result bundle."""

    manifest_path = Path(path)
    manifest = load_manifest(manifest_path)
    defaults = manifest.get("defaults", {})
    backends = manifest.get("backends", defaults.get("backends", ["cirq"]))
    shots = int(manifest.get("shots", defaults.get("shots", 1024)))
    repeats = int(manifest.get("repeats", defaults.get("repeats", 1)))
    cases = manifest.get("benchmarks") or manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Experiment manifest requires a non-empty 'benchmarks' list.")

    results: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Each benchmark case must be an object.")
        benchmark = build_benchmark_from_config(case)
        benchmarks = [benchmark]
        if case.get("noise_levels") is not None:
            benchmarks = build_noise_benchmarks(
                benchmark,
                noise_type=str(case.get("noise_type", "depolarizing")),
                noise_levels=case["noise_levels"],
            )
        case_backends = case.get("backends", backends)
        case_shots = int(case.get("shots", shots))
        case_repeats = int(case.get("repeats", repeats))
        for benchmark_case in benchmarks:
            results.extend(
                run_benchmark(
                    benchmark_case,
                    list(case_backends),
                    shots=case_shots,
                    repeats=case_repeats,
                )
            )

    bundle = {
        "schema_version": "0.1",
        "manifest_path": str(manifest_path),
        "manifest": manifest,
        "environment": capture_environment(manifest_path.parent),
        "results": results,
    }
    outputs = manifest.get("outputs", {})
    if outputs.get("json"):
        save_json(bundle, outputs["json"])
    if outputs.get("csv"):
        save_csv(results, outputs["csv"])
    if outputs.get("suite_plot"):
        save_suite_runtime_plot(results, outputs["suite_plot"])
    return bundle
