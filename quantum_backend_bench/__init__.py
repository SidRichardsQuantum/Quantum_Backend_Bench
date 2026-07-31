"""Quantum backend benchmark toolkit."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

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
from quantum_backend_bench.core.circuit_translate import (
    TRANSLATION_INPUT_FORMATS,
    TRANSLATION_OUTPUT_FORMATS,
    TRANSLATION_VERIFY_MODES,
    TranslationDiagnostic,
    TranslationError,
    TranslationResult,
    TranslationVerification,
    emit_circuit_source,
    import_circuit_source,
    translate_circuit_source,
    translation_check_report,
    translation_error_report,
    translation_result_report,
    verify_translation,
)
from quantum_backend_bench.core.diagnostics import diagnose_result_parity
from quantum_backend_bench.core.exact import (
    exact_amplitudes,
    exact_probabilities,
    pauli_z_expectation,
)
from quantum_backend_bench.core.observable_translate import (
    HAMILTONIAN_INPUT_FORMATS,
    HAMILTONIAN_OUTPUT_FORMATS,
    HAMILTONIAN_VERIFY_MODES,
    HamiltonianVerification,
    PauliHamiltonian,
    PauliTerm,
    emit_hamiltonian_source,
    hamiltonian_check_report,
    hamiltonian_translation_report,
    import_hamiltonian_source,
    translate_hamiltonian_source,
    translation_capability_rows,
    verify_hamiltonian_translation,
)
from quantum_backend_bench.core.workflow_translate import (
    GROUPING_STRATEGIES,
    RESULT_INPUT_FORMATS,
    RESULT_OUTPUT_FORMATS,
    WORKFLOW_INPUT_FORMATS,
    WORKFLOW_OUTPUT_FORMATS,
    WORKFLOW_VERIFY_MODES,
    MeasurementRequest,
    NeutralResult,
    ParameterizedWorkflow,
    WorkflowOperation,
    canonical_workflow,
    evaluate_workflow_result,
    emit_workflow_source,
    group_pauli_terms,
    group_pauli_terms_source,
    import_result_source,
    import_workflow_source,
    normalize_result_source,
    translate_workflow_source,
    validate_neutral_result,
    verify_workflow_translation,
    workflow_translation_report,
)
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

try:
    __version__ = version("quantum-backend-bench")
except PackageNotFoundError:  # pragma: no cover - editable source tree fallback
    __version__ = "0+unknown"


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load an experiment manifest without importing CLI internals at package import time."""

    from quantum_backend_bench.core.manifest import load_manifest as _load_manifest

    return _load_manifest(path)


def run_experiment_manifest(path: str | Path) -> dict[str, Any]:
    """Run an experiment manifest without importing CLI internals at package import time."""

    from quantum_backend_bench.core.manifest import (
        run_experiment_manifest as _run_experiment_manifest,
    )

    return _run_experiment_manifest(path)


__all__ = [
    "__version__",
    "pauli_z_expectation",
    "import_openqasm_circuit",
    "exact_amplitudes",
    "HAMILTONIAN_INPUT_FORMATS",
    "HAMILTONIAN_OUTPUT_FORMATS",
    "HAMILTONIAN_VERIFY_MODES",
    "GROUPING_STRATEGIES",
    "RESULT_INPUT_FORMATS",
    "RESULT_OUTPUT_FORMATS",
    "WORKFLOW_INPUT_FORMATS",
    "WORKFLOW_OUTPUT_FORMATS",
    "WORKFLOW_VERIFY_MODES",
    "HamiltonianVerification",
    "MeasurementRequest",
    "NeutralResult",
    "ParameterizedWorkflow",
    "PauliHamiltonian",
    "PauliTerm",
    "WorkflowOperation",
    "emit_hamiltonian_source",
    "hamiltonian_check_report",
    "hamiltonian_translation_report",
    "canonical_workflow",
    "evaluate_workflow_result",
    "emit_workflow_source",
    "group_pauli_terms",
    "group_pauli_terms_source",
    "import_hamiltonian_source",
    "import_result_source",
    "import_workflow_source",
    "normalize_result_source",
    "translate_hamiltonian_source",
    "translate_workflow_source",
    "translation_capability_rows",
    "validate_neutral_result",
    "verify_hamiltonian_translation",
    "verify_workflow_translation",
    "workflow_translation_report",
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
    "TRANSLATION_INPUT_FORMATS",
    "TRANSLATION_OUTPUT_FORMATS",
    "TRANSLATION_VERIFY_MODES",
    "TranslationDiagnostic",
    "TranslationError",
    "TranslationResult",
    "TranslationVerification",
    "emit_circuit_source",
    "import_circuit_source",
    "translate_circuit_source",
    "translation_check_report",
    "translation_error_report",
    "translation_result_report",
    "verify_translation",
    "validation_passed",
    "write_preset",
]
