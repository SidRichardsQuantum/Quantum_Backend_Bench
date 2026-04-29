"""Quantum backend benchmark toolkit."""

from quantum_backend_bench import _runtime as _runtime
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)
from quantum_backend_bench.core.discovery import (
    BENCHMARK_INFOS,
    BackendCapability,
    BenchmarkInfo,
    backend_capabilities,
)
from quantum_backend_bench.core.draw import draw_benchmark
from quantum_backend_bench.core.diff import (
    compare_result_sets,
    diff_passed,
    format_diff_table,
    load_result_file,
)
from quantum_backend_bench.core.environment import capture_environment
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.suites import SUITES, build_suite
from quantum_backend_bench.core.summary import format_summary, summarize_results
from quantum_backend_bench.core.validation import validate_backends, validation_passed


def load_manifest(path):  # type: ignore[no-untyped-def]
    """Load an experiment manifest without importing CLI internals at package import time."""

    from quantum_backend_bench.core.manifest import load_manifest as _load_manifest

    return _load_manifest(path)


def run_experiment_manifest(path):  # type: ignore[no-untyped-def]
    """Run an experiment manifest without importing CLI internals at package import time."""

    from quantum_backend_bench.core.manifest import (
        run_experiment_manifest as _run_experiment_manifest,
    )

    return _run_experiment_manifest(path)


__all__ = [
    "BenchmarkSpec",
    "BENCHMARK_INFOS",
    "BackendCapability",
    "BenchmarkInfo",
    "CircuitOperation",
    "InternalCircuit",
    "SUITES",
    "backend_capabilities",
    "build_suite",
    "compare_result_sets",
    "capture_environment",
    "diff_passed",
    "draw_benchmark",
    "format_diff_table",
    "format_summary",
    "load_result_file",
    "load_manifest",
    "run_benchmark",
    "run_experiment_manifest",
    "summarize_results",
    "validate_backends",
    "validation_passed",
]
