"""Quantum backend benchmark toolkit."""

from quantum_backend_bench import _runtime as _runtime
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)
from quantum_backend_bench.core.circuit_export import (
    export_benchmark_circuit,
    import_openqasm_circuit,
)
from quantum_backend_bench.core.diagnostics import diagnose_result_parity
from quantum_backend_bench.core.exact import (
    exact_amplitudes,
    exact_probabilities,
    pauli_z_expectation,
)
from quantum_backend_bench.core.hardware import write_hardware_artifacts
from quantum_backend_bench.core.sweeps import expand_benchmark_sweep, parse_sweep_specs
from quantum_backend_bench.core.bundle import create_result_bundle
from quantum_backend_bench.core.compatibility import (
    compatibility_rows,
    format_compatibility_report,
    python_compatibility,
)
from quantum_backend_bench.core.dataframe import results_to_dataframe, results_to_records
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
from quantum_backend_bench.core.doctor import doctor_checks, doctor_passed, format_doctor_table
from quantum_backend_bench.core.environment import capture_environment
from quantum_backend_bench.core.factory import BENCHMARK_BUILDERS, build_benchmark_from_config
from quantum_backend_bench.core.presets import list_presets, load_preset, write_preset
from quantum_backend_bench.core.report import (
    format_markdown_report,
    load_report_input,
    save_markdown_report,
)
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
    "pauli_z_expectation",
    "import_openqasm_circuit",
    "exact_amplitudes",
    "write_hardware_artifacts",
    "parse_sweep_specs",
    "export_benchmark_circuit",
    "expand_benchmark_sweep",
    "exact_probabilities",
    "diagnose_result_parity",
    "BenchmarkSpec",
    "BENCHMARK_BUILDERS",
    "BENCHMARK_INFOS",
    "BackendCapability",
    "BenchmarkInfo",
    "CircuitOperation",
    "InternalCircuit",
    "SUITES",
    "backend_capabilities",
    "build_benchmark_from_config",
    "build_suite",
    "compatibility_rows",
    "compare_result_sets",
    "capture_environment",
    "create_result_bundle",
    "diff_passed",
    "doctor_checks",
    "doctor_passed",
    "draw_benchmark",
    "format_compatibility_report",
    "format_diff_table",
    "format_doctor_table",
    "format_summary",
    "load_result_file",
    "load_manifest",
    "list_presets",
    "load_preset",
    "load_report_input",
    "format_markdown_report",
    "python_compatibility",
    "results_to_dataframe",
    "results_to_records",
    "run_benchmark",
    "run_experiment_manifest",
    "save_markdown_report",
    "summarize_results",
    "validate_backends",
    "validation_passed",
    "write_preset",
]
