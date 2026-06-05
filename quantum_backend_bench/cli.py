"""Command-line interface for quantum-backend-bench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from quantum_backend_bench.backends import BACKEND_REGISTRY
from quantum_backend_bench.benchmarks import noise_sensitivity
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec
from quantum_backend_bench.core.bundle import create_result_bundle
from quantum_backend_bench.core.circuit_export import (
    EXPORT_FORMATS,
    export_benchmark_circuit,
    import_openqasm_circuit,
)
from quantum_backend_bench.core.circuit_translate import (
    TRANSLATION_INPUT_FORMATS,
    TRANSLATION_OUTPUT_FORMATS,
    TRANSLATION_VERIFY_MODES,
    TranslationError,
    import_circuit_source,
    translate_circuit_source,
    translation_check_report,
    translation_error_report,
    translation_result_report,
)
from quantum_backend_bench.core.compatibility import format_compatibility_report
from quantum_backend_bench.core.diff import (
    DEFAULT_DIFF_METRICS,
    compare_result_sets,
    diff_passed,
    format_diff_table,
    load_result_file,
)
from quantum_backend_bench.core.diagnostics import diagnose_result_parity
from quantum_backend_bench.core.discovery import BENCHMARK_INFOS, backend_capabilities
from quantum_backend_bench.core.doctor import doctor_checks, doctor_passed, format_doctor_table
from quantum_backend_bench.core.draw import draw_benchmark
from quantum_backend_bench.core.exact import (
    exact_amplitudes,
    exact_probabilities,
    pauli_z_expectation,
)
from quantum_backend_bench.core.factory import BENCHMARK_BUILDERS, build_benchmark_from_config
from quantum_backend_bench.core.hardware import PROVIDERS, write_hardware_artifacts
from quantum_backend_bench.core.observable_translate import (
    HAMILTONIAN_INPUT_FORMATS,
    HAMILTONIAN_OUTPUT_FORMATS,
    HAMILTONIAN_VERIFY_MODES,
    hamiltonian_translation_report,
    translate_hamiltonian_source,
    translation_capability_rows,
)
from quantum_backend_bench.core.workflow_translate import (
    GROUPING_STRATEGIES,
    RESULT_INPUT_FORMATS,
    RESULT_OUTPUT_FORMATS,
    WORKFLOW_INPUT_FORMATS,
    WORKFLOW_OUTPUT_FORMATS,
    WORKFLOW_VERIFY_MODES,
    group_pauli_terms_source,
    normalize_result_source,
    translate_workflow_source,
    workflow_translation_report,
)
from quantum_backend_bench.core.presets import list_presets, load_preset, write_preset
from quantum_backend_bench.core.report import (
    format_markdown_report,
    load_report_input,
    save_markdown_report,
)
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.sdk_audit import (
    NOISE_MODELS,
    audit_passed,
    compile_audit,
    format_audit_rows,
    format_scorecard,
    noise_model_matrix,
    roundtrip_audit,
    runnable_noise_audit,
    save_audit_csv,
    save_audit_json,
    save_audit_report,
    sdk_parity_scorecard,
    semantic_audit,
)
from quantum_backend_bench.core.suites import SUITES, build_suite
from quantum_backend_bench.core.sweeps import expand_benchmark_sweep, parse_sweep_specs
from quantum_backend_bench.core.summary import format_summary, summarize_results
from quantum_backend_bench.utils.formatting import format_results_table
from quantum_backend_bench.utils.io import save_csv, save_json
from quantum_backend_bench.utils.plotting import (
    save_counts_heatmap,
    save_distribution_plot,
    save_noise_quality_plot,
    save_runtime_depth_plot,
    save_suite_runtime_plot,
)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quantum-bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available benchmarks and suites.")
    list_parser.add_argument("--kind", choices=["all", "benchmarks", "suites"], default="all")
    list_parser.set_defaults(func=_list_command)

    info_parser = subparsers.add_parser("info", help="Show backend and integration availability.")
    info_parser.set_defaults(func=_info_command)

    doctor_parser = subparsers.add_parser(
        "doctor", help="Diagnose local optional integrations and backend readiness."
    )
    doctor_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when no execution backend is installed.",
    )
    doctor_parser.set_defaults(func=_doctor_command)

    recommend_parser = subparsers.add_parser(
        "recommend", help="Recommend installed backends for a use case."
    )
    recommend_parser.add_argument(
        "--use-case",
        choices=["portable", "teaching", "noise", "performance", "research"],
        default="research",
    )
    recommend_parser.add_argument("--needs-noise", action="store_true")
    recommend_parser.add_argument("--needs-statevector", action="store_true")
    recommend_parser.add_argument("--no-external-runtime", action="store_true")
    recommend_parser.add_argument("--max-qubits", type=_positive_int)
    recommend_parser.add_argument("--python-version")
    recommend_parser.set_defaults(func=_recommend_command)

    compatibility_parser = subparsers.add_parser(
        "compatibility", help="Show Python, SDK, and local-runtime compatibility status."
    )
    compatibility_parser.set_defaults(func=_compatibility_command)

    bundle_parser = subparsers.add_parser(
        "bundle", help="Create a reproducible artifact bundle from saved benchmark results."
    )
    bundle_parser.add_argument("results")
    bundle_parser.add_argument("--output", "-o", required=True)
    bundle_parser.add_argument("--title", default="Quantum Backend Benchmark Bundle")
    bundle_parser.add_argument(
        "--no-plots", action="store_true", help="Skip plot generation when creating the bundle."
    )
    bundle_parser.set_defaults(func=_bundle_command)

    validate_parser = subparsers.add_parser(
        "validate", help="Run known-correct checks against installed or selected backends."
    )
    validate_parser.add_argument("--backends", nargs="+", choices=sorted(BACKEND_REGISTRY))
    validate_parser.add_argument("--shots", type=_positive_int, default=64)
    validate_parser.add_argument("--success-threshold", type=_probability, default=0.95)
    validate_parser.add_argument("--save-json")
    validate_parser.set_defaults(func=_validate_command)

    diff_parser = subparsers.add_parser("diff", help="Compare two saved JSON or CSV result files.")
    diff_parser.add_argument("baseline")
    diff_parser.add_argument("candidate")
    diff_parser.add_argument(
        "--metric",
        action="append",
        dest="metrics",
        help=(
            "Metric to compare. Can be repeated. Defaults to " f"{', '.join(DEFAULT_DIFF_METRICS)}."
        ),
    )
    diff_parser.add_argument(
        "--absolute-threshold",
        type=float,
        default=0.0,
        help="Allowed absolute metric delta before flagging a regression.",
    )
    diff_parser.add_argument(
        "--relative-threshold",
        type=float,
        default=0.0,
        help="Allowed relative metric delta before flagging a regression, e.g. 0.05.",
    )
    diff_parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with status 1 when a matching metric regresses or is missing.",
    )
    diff_parser.add_argument("--save-json")
    diff_parser.set_defaults(func=_diff_command)

    report_parser = subparsers.add_parser(
        "report", help="Generate a Markdown report from saved JSON or CSV results."
    )
    report_parser.add_argument("results")
    report_parser.add_argument("--output", "-o")
    report_parser.add_argument("--title", default="Quantum Backend Benchmark Report")
    report_parser.set_defaults(func=_report_command)

    diagnose_parser = subparsers.add_parser(
        "diagnose", help="Explain likely causes of SDK result disagreement."
    )
    diagnose_parser.add_argument("results")
    diagnose_parser.set_defaults(func=_diagnose_command)

    export_parser = subparsers.add_parser(
        "export", help="Export a benchmark circuit as internal JSON, OpenQASM, or native SDK text."
    )
    _add_benchmark_arguments(export_parser)
    export_parser.add_argument("--format", choices=EXPORT_FORMATS, default="openqasm")
    export_parser.add_argument("--backend", choices=sorted(BACKEND_REGISTRY))
    export_parser.add_argument("--save-path")
    export_parser.set_defaults(func=_export_command)

    import_qasm_parser = subparsers.add_parser(
        "import-qasm", help="Import a supported OpenQASM subset and print internal JSON."
    )
    import_qasm_parser.add_argument("source")
    import_qasm_parser.add_argument("--name", default="imported_openqasm")
    import_qasm_parser.add_argument("--save-json")
    import_qasm_parser.set_defaults(func=_import_qasm_command)

    translate_parser = subparsers.add_parser(
        "translate",
        help="Translate supported OpenQASM, internal JSON, or static SDK circuits.",
    )
    translate_parser.add_argument("source")
    translate_parser.add_argument(
        "--from-format",
        choices=TRANSLATION_INPUT_FORMATS,
        default="auto",
        help="Input circuit format. Auto-detection supports OpenQASM, internal JSON, and static SDK snippets.",
    )
    translate_parser.add_argument(
        "--to-format",
        required=True,
        choices=TRANSLATION_OUTPUT_FORMATS,
        help="Output format. SDK outputs are limited to free local Python SDKs.",
    )
    translate_parser.add_argument("--output", "-o")
    translate_parser.add_argument("--save-report")
    translate_parser.add_argument("--name", default="translated_circuit")
    translate_parser.add_argument(
        "--include-runner",
        action="store_true",
        help="Emit a runnable script that executes the translated circuit locally.",
    )
    translate_parser.add_argument(
        "--runner-shots",
        type=_positive_int,
        default=1024,
        help="Shot count baked into --include-runner output.",
    )
    translate_parser.add_argument(
        "--verify",
        choices=TRANSLATION_VERIFY_MODES,
        default="none",
        help="Compare source and translated circuit semantics through the neutral simulator.",
    )
    translate_parser.add_argument(
        "--verify-tolerance",
        type=float,
        default=1e-9,
        help="Maximum allowed total variation distance for semantic verification.",
    )
    translate_parser.add_argument(
        "--sample-shots",
        type=_positive_int,
        default=2048,
        help="Shot count used by --verify samples.",
    )
    translate_parser.set_defaults(func=_translate_command)

    translate_check_parser = subparsers.add_parser(
        "translate-check",
        help="Inspect whether a circuit source can be translated without writing output.",
    )
    translate_check_parser.add_argument("source")
    translate_check_parser.add_argument(
        "--from-format", choices=TRANSLATION_INPUT_FORMATS, default="auto"
    )
    translate_check_parser.add_argument("--save-report")
    translate_check_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the translation-check report as JSON to stdout.",
    )
    translate_check_parser.add_argument("--name", default="checked_circuit")
    translate_check_parser.set_defaults(func=_translate_check_command)

    translate_hamiltonian_parser = subparsers.add_parser(
        "translate-hamiltonian",
        help="Translate supported weighted Pauli Hamiltonians across local SDKs.",
    )
    _add_hamiltonian_translation_arguments(translate_hamiltonian_parser)
    translate_hamiltonian_parser.set_defaults(func=_translate_hamiltonian_command)

    translate_observable_parser = subparsers.add_parser(
        "translate-observable",
        help="Translate a supported single- or multi-term Pauli observable across local SDKs.",
    )
    _add_hamiltonian_translation_arguments(translate_observable_parser)
    translate_observable_parser.set_defaults(func=_translate_hamiltonian_command)

    workflow_parser = subparsers.add_parser(
        "translate-workflow",
        help="Translate parameterized workflow JSON into local SDK execution code.",
    )
    workflow_parser.add_argument("source")
    workflow_parser.add_argument(
        "--from-format",
        choices=WORKFLOW_INPUT_FORMATS,
        default="workflow-json",
        help="Input workflow format.",
    )
    workflow_parser.add_argument(
        "--to-format",
        required=True,
        choices=WORKFLOW_OUTPUT_FORMATS,
        help="Output workflow format. SDK outputs are limited to free local Python SDKs.",
    )
    workflow_parser.add_argument("--output", "-o")
    workflow_parser.add_argument("--save-report")
    workflow_parser.add_argument(
        "--verify",
        choices=WORKFLOW_VERIFY_MODES,
        default="canonical",
        help="Reimport generated workflow source and compare canonical workflow semantics.",
    )
    workflow_parser.set_defaults(func=_translate_workflow_command)

    result_parser = subparsers.add_parser(
        "translate-result",
        help="Normalize supported SDK-shaped result JSON into portable result JSON.",
    )
    result_parser.add_argument("source")
    result_parser.add_argument(
        "--from-format",
        choices=RESULT_INPUT_FORMATS,
        default="result-json",
        help="Input result shape.",
    )
    result_parser.add_argument(
        "--to-format",
        choices=RESULT_OUTPUT_FORMATS,
        default="result-json",
        help="Output result shape.",
    )
    result_parser.add_argument("--output", "-o")
    result_parser.add_argument("--save-report")
    result_parser.set_defaults(func=_translate_result_command)

    group_parser = subparsers.add_parser(
        "group-pauli-terms",
        help="Group Pauli Hamiltonian terms into jointly measurable sets.",
    )
    group_parser.add_argument("source")
    group_parser.add_argument(
        "--from-format",
        choices=HAMILTONIAN_INPUT_FORMATS,
        default="auto",
        help="Input Hamiltonian format.",
    )
    group_parser.add_argument(
        "--strategy",
        choices=GROUPING_STRATEGIES,
        default="qubit-wise",
        help="Measurement grouping strategy.",
    )
    group_parser.add_argument("--output", "-o")
    group_parser.add_argument("--save-report")
    group_parser.set_defaults(func=_group_pauli_terms_command)

    audit_parser = subparsers.add_parser(
        "translation-audit",
        help="Show current SDK translation capability coverage.",
    )
    audit_parser.add_argument("--json", action="store_true", help="Print audit rows as JSON.")
    audit_parser.add_argument("--sdk", choices=HAMILTONIAN_OUTPUT_FORMATS[:-1])
    audit_parser.add_argument("--from-format", choices=HAMILTONIAN_INPUT_FORMATS)
    audit_parser.add_argument("--to-format", choices=HAMILTONIAN_OUTPUT_FORMATS)
    audit_parser.add_argument(
        "--layer",
        choices=[
            "circuits",
            "pauli_hamiltonians",
            "observables",
            "noise_models",
            "execution_wrappers",
            "result_objects",
            "parameterized_circuits",
            "parameter_bindings",
            "measurement_requests",
            "measurement_grouping",
        ],
    )
    audit_parser.set_defaults(func=_translation_audit_command)

    parity_parser = subparsers.add_parser(
        "sdk-parity",
        help="Show free local SDK feature parity scorecards.",
    )
    parity_parser.add_argument("--json", action="store_true", help="Print scorecard as JSON.")
    _add_audit_output_arguments(parity_parser)
    parity_parser.set_defaults(func=_sdk_parity_command)

    semantic_parser = subparsers.add_parser(
        "semantic-audit",
        help="Run compact cross-SDK semantic checks against neutral exact probabilities.",
    )
    semantic_parser.add_argument("--backends", nargs="+", choices=sorted(BACKEND_REGISTRY))
    semantic_parser.add_argument("--shots", type=_positive_int, default=512)
    semantic_parser.add_argument("--tolerance", type=float, default=0.15)
    semantic_parser.add_argument("--json", action="store_true", help="Print audit rows as JSON.")
    _add_audit_output_arguments(semantic_parser)
    semantic_parser.add_argument(
        "--fail-on-error", action="store_true", help="Exit nonzero when an audit row fails."
    )
    semantic_parser.set_defaults(func=_semantic_audit_command)

    noise_audit_parser = subparsers.add_parser(
        "noise-audit",
        help="Show or run local noise model support checks across SDKs.",
    )
    noise_audit_parser.add_argument("--backends", nargs="+", choices=sorted(BACKEND_REGISTRY))
    noise_audit_parser.add_argument("--noise-types", nargs="+", choices=NOISE_MODELS)
    noise_audit_parser.add_argument("--noise-level", type=_probability, default=0.01)
    noise_audit_parser.add_argument("--shots", type=_positive_int, default=256)
    noise_audit_parser.add_argument(
        "--run", action="store_true", help="Execute tiny noisy workloads."
    )
    noise_audit_parser.add_argument("--json", action="store_true", help="Print audit rows as JSON.")
    _add_audit_output_arguments(noise_audit_parser)
    noise_audit_parser.add_argument(
        "--fail-on-error", action="store_true", help="Exit nonzero when an audit row fails."
    )
    noise_audit_parser.set_defaults(func=_noise_audit_command)

    compile_audit_parser = subparsers.add_parser(
        "compile-audit",
        help="Run compact compilation/structure comparison checks across SDKs.",
    )
    compile_audit_parser.add_argument("--backends", nargs="+", choices=sorted(BACKEND_REGISTRY))
    compile_audit_parser.add_argument("--shots", type=_positive_int, default=128)
    compile_audit_parser.add_argument(
        "--json", action="store_true", help="Print audit rows as JSON."
    )
    _add_audit_output_arguments(compile_audit_parser)
    compile_audit_parser.add_argument(
        "--fail-on-error", action="store_true", help="Exit nonzero when an audit row fails."
    )
    compile_audit_parser.set_defaults(func=_compile_audit_command)

    roundtrip_parser = subparsers.add_parser(
        "roundtrip-audit",
        help="Verify neutral-to-SDK-to-neutral circuit translation round trips.",
    )
    roundtrip_parser.add_argument(
        "--targets", nargs="+", choices=TRANSLATION_OUTPUT_FORMATS, help="Translation targets."
    )
    roundtrip_parser.add_argument("--tolerance", type=float, default=1e-9)
    roundtrip_parser.add_argument(
        "--include-hamiltonian", action="store_true", help="Include Pauli Hamiltonian round trips."
    )
    roundtrip_parser.add_argument(
        "--include-workflow",
        action="store_true",
        help="Include parameterized workflow round trips.",
    )
    roundtrip_parser.add_argument("--json", action="store_true", help="Print audit rows as JSON.")
    _add_audit_output_arguments(roundtrip_parser)
    roundtrip_parser.add_argument(
        "--fail-on-error", action="store_true", help="Exit nonzero when an audit row fails."
    )
    roundtrip_parser.set_defaults(func=_roundtrip_audit_command)

    exact_parser = subparsers.add_parser(
        "exact", help="Print exact measurement probabilities for an internal benchmark circuit."
    )
    _add_benchmark_arguments(exact_parser)
    exact_parser.add_argument("--save-json")
    exact_parser.add_argument("--top-k", type=_positive_int)
    exact_parser.add_argument("--amplitudes", action="store_true")
    exact_parser.add_argument("--observable", help="Pauli I/Z observable, e.g. ZZI.")
    exact_parser.set_defaults(func=_exact_command)

    hardware_parser = subparsers.add_parser(
        "hardware", help="Write hardware-preparation artifacts without submitting cloud jobs."
    )
    _add_benchmark_arguments(hardware_parser)
    hardware_parser.add_argument("--output", "-o", required=True)
    hardware_parser.add_argument("--backend-hint")
    hardware_parser.add_argument("--provider", choices=PROVIDERS, default="generic")
    hardware_parser.add_argument(
        "--qasm-version", choices=["openqasm", "openqasm2", "openqasm3"], default="openqasm"
    )
    hardware_parser.add_argument("--shots", type=_positive_int, default=1024)
    hardware_parser.set_defaults(func=_hardware_command)

    experiment_parser = subparsers.add_parser(
        "experiment", help="Run benchmark cases from a JSON or YAML manifest."
    )
    experiment_subparsers = experiment_parser.add_subparsers(
        dest="experiment_command", required=True
    )
    experiment_run_parser = experiment_subparsers.add_parser(
        "run", help="Run an experiment manifest."
    )
    experiment_run_parser.add_argument("manifest")
    experiment_run_parser.set_defaults(func=_experiment_run_command)

    preset_parser = subparsers.add_parser("preset", help="Use packaged comparison presets.")
    preset_subparsers = preset_parser.add_subparsers(dest="preset_command", required=True)
    preset_list_parser = preset_subparsers.add_parser("list", help="List packaged presets.")
    preset_list_parser.set_defaults(func=_preset_list_command)
    preset_show_parser = preset_subparsers.add_parser("show", help="Print a preset manifest.")
    preset_show_parser.add_argument("preset", choices=list_presets())
    preset_show_parser.add_argument("--save-json")
    preset_show_parser.set_defaults(func=_preset_show_command)
    preset_run_parser = preset_subparsers.add_parser("run", help="Run a packaged preset.")
    preset_run_parser.add_argument("preset", choices=list_presets())
    preset_run_parser.add_argument("--backends", nargs="+", choices=sorted(BACKEND_REGISTRY))
    preset_run_parser.add_argument("--shots", type=_positive_int)
    preset_run_parser.add_argument("--repeats", type=_positive_int)
    preset_run_parser.add_argument("--save-json")
    preset_run_parser.add_argument("--save-csv")
    preset_run_parser.add_argument("--save-suite-plot")
    preset_run_parser.add_argument("--save-report")
    preset_run_parser.add_argument("--summary", action="store_true")
    preset_run_parser.set_defaults(func=_preset_run_command)

    run_parser = subparsers.add_parser("run", help="Run a single benchmark on one backend.")
    _add_benchmark_arguments(run_parser)
    run_parser.add_argument("--backend", required=True, choices=sorted(BACKEND_REGISTRY))
    run_parser.add_argument(
        "--sweep", action="append", help="Parameter sweep, e.g. n-qubits=2:6 or depth=4,8."
    )
    run_parser.set_defaults(func=_run_command)

    compare_parser = subparsers.add_parser(
        "compare", help="Compare a benchmark across multiple backends."
    )
    _add_benchmark_arguments(compare_parser)
    compare_parser.add_argument(
        "--backends", nargs="+", required=True, choices=sorted(BACKEND_REGISTRY)
    )
    compare_parser.add_argument(
        "--sweep", action="append", help="Parameter sweep, e.g. n-qubits=2:6 or depth=4,8."
    )
    compare_parser.set_defaults(func=_compare_command)

    noise_parser = subparsers.add_parser("noise-sweep", help="Run a depolarizing noise sweep.")
    _add_benchmark_arguments(noise_parser)
    noise_parser.add_argument("--backend", required=True, choices=sorted(BACKEND_REGISTRY))
    noise_parser.add_argument(
        "--noise-type",
        choices=["depolarizing", "bit_flip", "phase_flip", "amplitude_damping", "readout_error"],
        default="depolarizing",
    )
    noise_parser.add_argument(
        "--noise-levels",
        nargs="+",
        type=_probability,
        default=[0.0, 0.001, 0.005, 0.01, 0.02],
    )
    noise_parser.set_defaults(func=_noise_command)

    suite_parser = subparsers.add_parser("suite", help="Run a named benchmark suite.")
    suite_parser.add_argument("suite", choices=sorted(SUITES))
    suite_parser.add_argument(
        "--backends",
        nargs="+",
        default=["cirq"],
        choices=sorted(BACKEND_REGISTRY),
    )
    suite_parser.add_argument(
        "--list-cases",
        "--dry-run",
        action="store_true",
        dest="list_cases",
        help="Print planned suite cases without executing them.",
    )
    suite_parser.set_defaults(func=_suite_command)

    draw_parser = subparsers.add_parser("draw", help="Render a circuit diagram using a native SDK.")
    _add_benchmark_arguments(draw_parser)
    draw_parser.add_argument(
        "--backend", required=True, choices=[*sorted(BACKEND_REGISTRY), "tket"]
    )
    draw_parser.add_argument("--save-path")
    draw_parser.set_defaults(func=_draw_command)

    for command_parser in (run_parser, compare_parser, noise_parser, suite_parser):
        command_parser.add_argument("--shots", type=_positive_int, default=1024)
        command_parser.add_argument("--repeats", type=_positive_int, default=1)
        command_parser.add_argument("--save-json")
        command_parser.add_argument("--save-csv")
        command_parser.add_argument("--save-plot")
        command_parser.add_argument("--save-distribution")
        command_parser.add_argument("--save-quality-plot")
        command_parser.add_argument("--save-suite-plot")
        command_parser.add_argument("--save-heatmap")
        command_parser.add_argument("--summary", action="store_true")

    return parser


def _add_audit_output_arguments(command_parser: argparse.ArgumentParser) -> None:
    command_parser.add_argument("--save-json", help="Save audit rows as JSON.")
    command_parser.add_argument("--save-csv", help="Save audit rows as flattened CSV.")
    command_parser.add_argument("--save-report", help="Save audit rows as a Markdown report.")


def _add_hamiltonian_translation_arguments(command_parser: argparse.ArgumentParser) -> None:
    command_parser.add_argument("source")
    command_parser.add_argument(
        "--from-format",
        choices=HAMILTONIAN_INPUT_FORMATS,
        default="auto",
        help="Input Hamiltonian format. Auto-detection supports pauli-json and static SDK snippets.",
    )
    command_parser.add_argument(
        "--to-format",
        required=True,
        choices=HAMILTONIAN_OUTPUT_FORMATS,
        help="Output Hamiltonian format. SDK outputs are limited to free local Python SDKs.",
    )
    command_parser.add_argument("--output", "-o")
    command_parser.add_argument("--save-report")
    command_parser.add_argument(
        "--verify",
        choices=HAMILTONIAN_VERIFY_MODES,
        default="canonical",
        help="Reimport generated source and compare canonical Pauli terms.",
    )


def _list_command(args: argparse.Namespace) -> int:
    if args.kind in {"all", "benchmarks"}:
        print("Benchmarks")
        for info in sorted(BENCHMARK_INFOS.values(), key=lambda item: item.cli_name):
            params = ", ".join(info.key_parameters)
            print(f"  {info.cli_name:<20} {info.family:<12} {info.description}")
            print(f"  {'':<20} parameters: {params}")
    if args.kind == "all":
        print()
    if args.kind in {"all", "suites"}:
        print("Suites")
        for suite_name, cases in sorted(SUITES.items()):
            print(f"  {suite_name:<10} {len(cases)} cases")
            for case in cases:
                print(f"    - {case.benchmark}: {case.description}")
    return 0


def _info_command(args: argparse.Namespace) -> int:
    del args
    print("Integrations")
    print("name          role           installed  noise support   local  external  notes")
    for capability in backend_capabilities():
        installed = "yes" if capability.installed else "no"
        local = "yes" if capability.local_only else "no"
        external = "yes" if capability.external_process else "no"
        install_hint = (
            ""
            if capability.installed
            else f" Install with quantum-backend-bench[{capability.install_extra}]."
        )
        print(
            f"{capability.name:<13} {capability.role:<14} {installed:<10} "
            f"{capability.noise_support:<15} {local:<6} {external:<9} "
            f"{capability.notes}{install_hint}"
        )
    return 0


def _recommend_command(args: argparse.Namespace) -> int:
    execution_capabilities = [
        capability for capability in backend_capabilities() if capability.role == "execution"
    ]
    installed = [capability for capability in execution_capabilities if capability.installed]
    installed = _filter_recommendations(installed, args)
    ranked = _rank_capabilities(installed, args.use_case)
    print(f"Recommended installed backends for {args.use_case}")
    if args.max_qubits is not None:
        print(
            f"Constraint: max_qubits={args.max_qubits} (local simulators are not hard-limited by metadata; validate memory locally)."
        )
    if args.python_version:
        print(
            f"Constraint: python_version={args.python_version} (use compatibility for package-version details)."
        )
    if not ranked:
        print("No installed execution backends found.")
    for index, capability in enumerate(ranked, start=1):
        reasons = _recommendation_reasons(capability, args.use_case)
        print(f"{index}. {capability.name}: {', '.join(reasons)}")

    missing = [capability for capability in execution_capabilities if not capability.installed]
    if missing:
        print("\nOther execution backends")
        for capability in sorted(missing, key=lambda item: item.name):
            reasons = _missing_reasons(capability)
            print(f"- {capability.name}: {', '.join(reasons)}")
    return 0 if ranked else 1


def _compatibility_command(args: argparse.Namespace) -> int:
    del args
    print(format_compatibility_report())
    return 0


def _bundle_command(args: argparse.Namespace) -> int:
    paths = create_result_bundle(
        args.results,
        args.output,
        title=args.title,
        include_plots=not args.no_plots,
    )
    print(f"Created bundle at {args.output}")
    for key, path in sorted(paths.items()):
        print(f"  {key}: {path}")
    return 0


def _doctor_command(args: argparse.Namespace) -> int:
    checks = doctor_checks()
    print("Diagnostics")
    print(format_doctor_table(checks))
    if not doctor_passed(checks):
        print("\nNo installed execution backend found.")
    return 0 if not args.strict or doctor_passed(checks) else 1


def _validate_command(args: argparse.Namespace) -> int:
    from quantum_backend_bench.core.validation import validate_backends, validation_passed

    checks = validate_backends(
        backends=args.backends,
        shots=args.shots,
        success_threshold=args.success_threshold,
    )
    print("Validation")
    print("backend       benchmark             status  message")
    for check in checks:
        print(
            f"{check['backend']:<13} {check['benchmark']:<21} "
            f"{check['status']:<7} {check['message']}"
        )
    if args.save_json:
        save_json(checks, args.save_json)
        print(f"\nSaved validation JSON to {args.save_json}")
    return 0 if validation_passed(checks) else 1


def _diff_command(args: argparse.Namespace) -> int:
    baseline = load_result_file(args.baseline)
    candidate = load_result_file(args.candidate)
    rows = compare_result_sets(
        baseline,
        candidate,
        metrics=args.metrics,
        absolute_threshold=args.absolute_threshold,
        relative_threshold=args.relative_threshold,
    )
    print(format_diff_table(rows))
    if args.save_json:
        save_json(rows, args.save_json)
        print(f"\nSaved diff JSON to {args.save_json}")
    if args.fail_on_regression and not diff_passed(rows):
        return 1
    return 0


def _report_command(args: argparse.Namespace) -> int:
    bundle = load_report_input(args.results)
    if args.output:
        save_markdown_report(bundle, args.output, title=args.title)
        print(f"Saved report to {args.output}")
    else:
        print(format_markdown_report(bundle, title=args.title))
    return 0


def _diagnose_command(args: argparse.Namespace) -> int:
    bundle = load_report_input(args.results)
    for finding in diagnose_result_parity(list(bundle.get("results", []))):
        print(f"- {finding}")
    return 0


def _export_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    output = export_benchmark_circuit(
        benchmark, args.format, backend=args.backend, save_path=args.save_path
    )
    print(output)
    if args.save_path:
        print(f"Saved circuit export to {args.save_path}")
    return 0


def _import_qasm_command(args: argparse.Namespace) -> int:
    source = Path(args.source).read_text(encoding="utf-8")
    benchmark = import_openqasm_circuit(source, name=args.name)
    output = export_benchmark_circuit(benchmark, "internal-json", save_path=args.save_json)
    print(output)
    if args.save_json:
        print(f"Saved imported circuit JSON to {args.save_json}")
    return 0


def _translate_command(args: argparse.Namespace) -> int:
    source = Path(args.source).read_text(encoding="utf-8")
    try:
        result = translate_circuit_source(
            source,
            from_format=args.from_format,
            to_format=args.to_format,
            name=args.name,
            verify=args.verify,
            verification_tolerance=args.verify_tolerance,
            sample_shots=args.sample_shots,
            include_runner=args.include_runner,
            runner_shots=args.runner_shots,
        )
    except TranslationError as exc:
        print("Translation failed")
        for diagnostic in exc.diagnostics:
            print(f"  {diagnostic.severity}: {diagnostic.code}: {diagnostic.message}")
        if args.save_report:
            _write_translation_report(
                args.save_report,
                translation_error_report(
                    exc, source_path=args.source, from_format=args.from_format
                ),
            )
        return 1
    if args.output:
        Path(args.output).write_text(result.source, encoding="utf-8")
        print(f"Saved translated circuit to {args.output}")
        for note in result.notes:
            print(f"  {note}")
        for diagnostic in result.diagnostics:
            print(f"  {diagnostic.severity}: {diagnostic.code}: {diagnostic.message}")
    else:
        print(result.source)
        if result.verification is not None:
            print(f"# {result.verification.details}")
    if args.save_report:
        _write_translation_report(
            args.save_report,
            translation_result_report(
                result,
                source_path=args.source,
                from_format=args.from_format,
                to_format=args.to_format,
            ),
        )
    return 0 if result.verification is None or result.verification.passed else 1


def _translate_check_command(args: argparse.Namespace) -> int:
    source = Path(args.source).read_text(encoding="utf-8")
    try:
        benchmark, detected_format = import_circuit_source(
            source, from_format=args.from_format, name=args.name
        )
    except TranslationError as exc:
        report = translation_error_report(
            exc, source_path=args.source, from_format=args.from_format
        )
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("Translation check failed")
            for diagnostic in exc.diagnostics:
                print(f"  {diagnostic.severity}: {diagnostic.code}: {diagnostic.message}")
        if args.save_report:
            _write_translation_report(args.save_report, report)
        return 1

    report = translation_check_report(benchmark, detected_format, source_path=args.source)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Translation check")
        print(f"  input_format: {report['input_format']}")
        print(f"  n_qubits: {report['n_qubits']}")
        print(f"  operations: {report['operation_count']}")
        print(f"  measurements: {report['measurements']}")
        print(f"  gates: {json.dumps(report['gate_counts'], sort_keys=True)}")
        print("  verification_available: yes")
        print("  supported_outputs: " + ", ".join(TRANSLATION_OUTPUT_FORMATS))
    if args.save_report:
        _write_translation_report(args.save_report, report)
    return 0


def _translate_hamiltonian_command(args: argparse.Namespace) -> int:
    source = Path(args.source).read_text(encoding="utf-8")
    try:
        result = translate_hamiltonian_source(
            source,
            from_format=args.from_format,
            to_format=args.to_format,
            verify=args.verify,
        )
    except TranslationError as exc:
        print("Hamiltonian translation failed")
        for diagnostic in exc.diagnostics:
            print(f"  {diagnostic.severity}: {diagnostic.code}: {diagnostic.message}")
        if args.save_report:
            _write_translation_report(
                args.save_report,
                {
                    "source_path": args.source,
                    "from_format": args.from_format,
                    "status": "failed",
                    "diagnostics": [
                        {
                            "severity": diagnostic.severity,
                            "code": diagnostic.code,
                            "message": diagnostic.message,
                        }
                        for diagnostic in exc.diagnostics
                    ],
                },
            )
        return 1

    if args.output:
        Path(args.output).write_text(result.source, encoding="utf-8")
        print(f"Saved translated Hamiltonian to {args.output}")
        for note in result.notes:
            print(f"  {note}")
    else:
        print(result.source)
        if result.verification is not None:
            print(f"# {result.verification.details}")
    if args.save_report:
        _write_translation_report(
            args.save_report,
            hamiltonian_translation_report(
                result,
                source_path=args.source,
                from_format=args.from_format,
                to_format=args.to_format,
            ),
        )
    return 0 if result.verification is None or result.verification.passed else 1


def _translate_workflow_command(args: argparse.Namespace) -> int:
    source = Path(args.source).read_text(encoding="utf-8")
    try:
        result = translate_workflow_source(
            source,
            from_format=args.from_format,
            to_format=args.to_format,
            verify=args.verify,
        )
    except TranslationError as exc:
        print("Workflow translation failed")
        for diagnostic in exc.diagnostics:
            print(f"  {diagnostic.severity}: {diagnostic.code}: {diagnostic.message}")
        return 1

    if args.output:
        Path(args.output).write_text(result.source, encoding="utf-8")
        print(f"Saved translated workflow to {args.output}")
        for note in result.notes:
            print(f"  {note}")
    else:
        print(result.source)
    if args.save_report:
        _write_translation_report(
            args.save_report,
            workflow_translation_report(
                result,
                source_path=args.source,
                from_format=args.from_format,
                to_format=args.to_format,
            ),
        )
    return 0 if result.verification is None or result.verification.passed else 1


def _translate_result_command(args: argparse.Namespace) -> int:
    source = Path(args.source).read_text(encoding="utf-8")
    try:
        result = normalize_result_source(
            source,
            from_format=args.from_format,
            to_format=args.to_format,
        )
    except TranslationError as exc:
        print("Result translation failed")
        for diagnostic in exc.diagnostics:
            print(f"  {diagnostic.severity}: {diagnostic.code}: {diagnostic.message}")
        return 1

    if args.output:
        Path(args.output).write_text(result.source, encoding="utf-8")
        print(f"Saved translated result to {args.output}")
        for note in result.notes:
            print(f"  {note}")
    else:
        print(result.source)
    if args.save_report:
        _write_translation_report(
            args.save_report,
            workflow_translation_report(
                result,
                source_path=args.source,
                from_format=args.from_format,
                to_format=args.to_format,
            ),
        )
    return 0


def _group_pauli_terms_command(args: argparse.Namespace) -> int:
    source = Path(args.source).read_text(encoding="utf-8")
    try:
        result = group_pauli_terms_source(
            source,
            from_format=args.from_format,
            strategy=args.strategy,
        )
    except TranslationError as exc:
        print("Pauli-term grouping failed")
        for diagnostic in exc.diagnostics:
            print(f"  {diagnostic.severity}: {diagnostic.code}: {diagnostic.message}")
        return 1

    if args.output:
        Path(args.output).write_text(result.source, encoding="utf-8")
        print(f"Saved Pauli-term groups to {args.output}")
        for note in result.notes:
            print(f"  {note}")
    else:
        print(result.source)
    if args.save_report:
        _write_translation_report(
            args.save_report,
            workflow_translation_report(
                result,
                source_path=args.source,
                from_format=args.from_format,
                to_format="measurement-groups",
            ),
        )
    return 0


def _translation_audit_command(args: argparse.Namespace) -> int:
    rows = _filter_translation_audit_rows(translation_capability_rows(), args)
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0
    print("SDK Translation Capability Audit")
    print(
        "sdk           circuits  pauli_hamiltonians  params  bindings  measurements  grouping  execution  results  verification"
    )
    for row in rows:
        print(
            f"{row['sdk']:<13} {_yes_no(row['circuits']):<8} "
            f"{_yes_no(row['pauli_hamiltonians']):<19} "
            f"{_yes_no(row['parameterized_circuits']):<7} "
            f"{_yes_no(row['parameter_bindings']):<9} "
            f"{_yes_no(row['measurement_requests']):<13} "
            f"{_yes_no(row['measurement_grouping']):<9} "
            f"{_yes_no(row['execution_wrappers']):<9} "
            f"{_yes_no(row['result_objects']):<7} {', '.join(row['verification_modes'])}"
        )
    return 0


def _filter_translation_audit_rows(
    rows: list[dict[str, object]], args: argparse.Namespace
) -> list[dict[str, object]]:
    selected = rows
    if args.sdk:
        selected = [row for row in selected if row["sdk"] == args.sdk]
    if args.to_format:
        selected = [row for row in selected if args.to_format in row["output_formats"]]
    if args.from_format:
        selected = [row for row in selected if args.from_format in row["input_formats"]]
    if args.layer:
        selected = [row for row in selected if row[args.layer]]
    return selected


def _yes_no(value: object) -> str:
    return "yes" if value else "no"


def _sdk_parity_command(args: argparse.Namespace) -> int:
    rows = sdk_parity_scorecard()
    _save_audit_outputs(args, rows, title="SDK Parity Scorecard")
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(format_scorecard(rows))
    return 0


def _semantic_audit_command(args: argparse.Namespace) -> int:
    rows = semantic_audit(backends=args.backends, shots=args.shots, tolerance=args.tolerance)
    _save_audit_outputs(args, rows, title="Semantic Audit")
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(format_audit_rows("Semantic Audit", rows))
    return 0 if not args.fail_on_error or audit_passed(rows) else 1


def _noise_audit_command(args: argparse.Namespace) -> int:
    if args.run:
        rows = runnable_noise_audit(
            backends=args.backends,
            noise_models=args.noise_types,
            noise_level=args.noise_level,
            shots=args.shots,
        )
        title = "Noise Execution Audit"
    else:
        rows = noise_model_matrix()
        if args.backends:
            rows = [row for row in rows if row["backend"] in args.backends]
        if args.noise_types:
            rows = [
                {**row, "models": {key: row["models"][key] for key in args.noise_types}}
                for row in rows
            ]
        title = "Noise Model Matrix"
    _save_audit_outputs(args, rows, title=title)
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(format_audit_rows(title, rows))
    return 0 if not args.fail_on_error or audit_passed(rows) else 1


def _compile_audit_command(args: argparse.Namespace) -> int:
    rows = compile_audit(backends=args.backends, shots=args.shots)
    _save_audit_outputs(args, rows, title="Compile Audit")
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(format_audit_rows("Compile Audit", rows))
    return 0 if not args.fail_on_error or audit_passed(rows) else 1


def _roundtrip_audit_command(args: argparse.Namespace) -> int:
    rows = roundtrip_audit(
        targets=args.targets,
        tolerance=args.tolerance,
        include_hamiltonian=args.include_hamiltonian,
        include_workflow=args.include_workflow,
    )
    _save_audit_outputs(args, rows, title="Roundtrip Audit")
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print(format_audit_rows("Roundtrip Audit", rows))
    return 0 if not args.fail_on_error or audit_passed(rows) else 1


def _save_audit_outputs(
    args: argparse.Namespace, rows: list[dict[str, object]], *, title: str
) -> None:
    if args.save_json:
        save_audit_json(rows, args.save_json)
        print(f"Saved audit JSON to {args.save_json}")
    if args.save_csv:
        save_audit_csv(rows, args.save_csv)
        print(f"Saved audit CSV to {args.save_csv}")
    if args.save_report:
        save_audit_report(rows, args.save_report, title=title)
        print(f"Saved audit report to {args.save_report}")


def _write_translation_report(path: str, report: dict[str, object]) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Saved translation report to {path}")


def _exact_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    payload: dict[str, object] = {
        "probabilities": exact_probabilities(benchmark, top_k=args.top_k),
    }
    if args.amplitudes:
        payload["amplitudes"] = exact_amplitudes(benchmark, top_k=args.top_k)
    if args.observable:
        payload["expectation"] = {args.observable: pauli_z_expectation(benchmark, args.observable)}
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.save_json:
        save_json(payload, args.save_json)
        print(f"Saved exact results to {args.save_json}")
    return 0


def _hardware_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    paths = write_hardware_artifacts(
        benchmark,
        args.output,
        backend_hint=args.backend_hint,
        shots=args.shots,
        provider=args.provider,
        qasm_version=args.qasm_version,
    )
    print(f"Created hardware artifacts at {args.output}")
    for key, path in sorted(paths.items()):
        print(f"  {key}: {path}")
    return 0


def _filter_recommendations(capabilities: list[object], args: argparse.Namespace) -> list[object]:
    filtered = []
    for capability in capabilities:
        if args.needs_noise and getattr(capability, "noise_support") in {"not injected", "n/a"}:
            continue
        if args.needs_statevector and not getattr(capability, "exact_statevector"):
            continue
        if args.no_external_runtime and getattr(capability, "external_process"):
            continue
        filtered.append(capability)
    return filtered


def _rank_capabilities(capabilities: list[object], use_case: str) -> list[object]:
    def score(capability: object) -> tuple[int, str]:
        value = 0
        if getattr(capability, "local_only"):
            value += 2
        if getattr(capability, "shot_sampling"):
            value += 2
        if (
            use_case in {"noise", "research"}
            and getattr(capability, "noise_support") != "not injected"
        ):
            value += 4
        if use_case == "performance" and not getattr(capability, "external_process"):
            value += 2
        if use_case == "teaching" and not getattr(capability, "external_process"):
            value += 2
        if use_case == "portable" and not getattr(capability, "includes_transpilation_time"):
            value += 1
        return (-value, getattr(capability, "name"))

    return sorted(capabilities, key=score)


def _missing_reasons(capability: object) -> list[str]:
    reasons = [
        f"not installed; install quantum-backend-bench[{getattr(capability, 'install_extra')}]"
    ]
    if getattr(capability, "external_process"):
        reasons.append("requires external local runtime")
    if not getattr(capability, "local_only"):
        reasons.append("outside credential-free local execution scope")
    if getattr(capability, "includes_transpilation_time"):
        reasons.append("runtime includes transpilation")
    if getattr(capability, "noise_support") not in {"not injected", "n/a"}:
        reasons.append(f"noise={getattr(capability, 'noise_support')}")
    return reasons


def _recommendation_reasons(capability: object, use_case: str) -> list[str]:
    reasons = []
    if getattr(capability, "local_only"):
        reasons.append("local")
    if getattr(capability, "shot_sampling"):
        reasons.append("shot sampling")
    if getattr(capability, "noise_support") not in {"not injected", "n/a"}:
        reasons.append(f"noise={getattr(capability, 'noise_support')}")
    if getattr(capability, "exact_statevector"):
        reasons.append("exact statevector")
    if getattr(capability, "external_process"):
        reasons.append("external local process")
    if getattr(capability, "includes_transpilation_time"):
        reasons.append("runtime includes transpilation")
    if use_case == "research":
        reasons.append("capture caveats in results")
    return reasons or ["installed"]


def _add_benchmark_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("benchmark", choices=sorted(BENCHMARK_BUILDERS))
    parser.add_argument("--n-qubits", type=int, default=None)
    parser.add_argument("--depth", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--marked-state", default=None)
    parser.add_argument("--secret-string", default=None)
    parser.add_argument("--oracle-type", choices=["balanced", "constant"], default="balanced")
    parser.add_argument("--bitmask", default=None)
    parser.add_argument("--constant-value", type=int, choices=[0, 1], default=0)
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--time", type=float, default=0.5)
    parser.add_argument("--trotter-steps", type=int, default=1)
    parser.add_argument("--gamma", type=float, default=0.8)
    parser.add_argument("--beta", type=float, default=0.4)
    parser.add_argument("--graph", choices=["line", "ring"], default="ring")
    parser.add_argument("--theta", type=float, default=0.3)
    parser.add_argument("--phase", type=float, default=0.25)
    parser.add_argument("--probability", type=_probability, default=0.25)
    parser.add_argument("--feature-scale", type=float, default=0.7)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _probability(value: str) -> float:
    parsed = float(value)
    if parsed < 0.0 or parsed > 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def _benchmark_config_from_args(args: argparse.Namespace) -> dict[str, object]:
    config: dict[str, object] = {"benchmark": args.benchmark}
    for key in (
        "n_qubits",
        "depth",
        "seed",
        "marked_state",
        "secret_string",
        "oracle_type",
        "bitmask",
        "constant_value",
        "iterations",
        "time",
        "trotter_steps",
        "gamma",
        "beta",
        "graph",
        "theta",
        "phase",
        "probability",
        "feature_scale",
    ):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value
    return config


def _build_benchmark_from_args(args: argparse.Namespace) -> BenchmarkSpec:
    return build_benchmark_from_config(_benchmark_config_from_args(args))


def _swept_benchmarks_from_args(args: argparse.Namespace) -> list[BenchmarkSpec]:
    return expand_benchmark_sweep(_benchmark_config_from_args(args), parse_sweep_specs(args.sweep))


def _run_command(args: argparse.Namespace) -> int:
    results = []
    for benchmark in _swept_benchmarks_from_args(args):
        results.extend(
            run_benchmark(benchmark, [args.backend], shots=args.shots, repeats=args.repeats)
        )
    return _render_and_save(results, args)


def _compare_command(args: argparse.Namespace) -> int:
    results = []
    for benchmark in _swept_benchmarks_from_args(args):
        results.extend(
            run_benchmark(benchmark, list(args.backends), shots=args.shots, repeats=args.repeats)
        )
    return _render_and_save(results, args)


def _noise_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    noisy_specs = noise_sensitivity.build_benchmark(
        benchmark, noise_type=args.noise_type, noise_levels=args.noise_levels
    )
    results = []
    for spec in noisy_specs:
        results.extend(run_benchmark(spec, [args.backend], shots=args.shots, repeats=args.repeats))
    return _render_and_save(results, args)


def _suite_command(args: argparse.Namespace) -> int:
    if args.list_cases:
        manifest = _suite_manifest(args.suite)
        _print_suite_cases(args.suite, manifest)
        if args.save_json:
            save_json(manifest, args.save_json)
            print(f"\nSaved suite manifest to {args.save_json}")
        return 0
    results = []
    for benchmark in build_suite(args.suite):
        results.extend(
            run_benchmark(benchmark, list(args.backends), shots=args.shots, repeats=args.repeats)
        )
    return _render_and_save(results, args)


def _experiment_run_command(args: argparse.Namespace) -> int:
    from quantum_backend_bench.core.manifest import run_experiment_manifest

    bundle = run_experiment_manifest(args.manifest)
    print(format_results_table(bundle["results"]))
    outputs = bundle["manifest"].get("outputs", {})
    if outputs.get("json"):
        print(f"\nSaved experiment JSON to {outputs['json']}")
    if outputs.get("csv"):
        print(f"Saved experiment CSV to {outputs['csv']}")
    if outputs.get("suite_plot"):
        print(f"Saved experiment plot to {outputs['suite_plot']}")
    if outputs.get("report"):
        print(f"Saved experiment report to {outputs['report']}")
    return 0


def _preset_list_command(args: argparse.Namespace) -> int:
    del args
    print("Presets")
    for name in list_presets():
        preset = load_preset(name)
        print(f"  {name:<12} {preset.get('description', '')}")
    return 0


def _preset_show_command(args: argparse.Namespace) -> int:
    if args.save_json:
        write_preset(args.preset, args.save_json)
        print(f"Saved preset manifest to {args.save_json}")
    else:
        print(json.dumps(load_preset(args.preset), indent=2, sort_keys=True))
    return 0


def _preset_run_command(args: argparse.Namespace) -> int:
    from quantum_backend_bench.core.manifest import run_experiment

    manifest = load_preset(args.preset)
    if args.backends:
        manifest["backends"] = list(args.backends)
    if args.shots is not None:
        manifest["shots"] = args.shots
    if args.repeats is not None:
        manifest["repeats"] = args.repeats
    outputs = dict(manifest.get("outputs", {}))
    if args.save_json:
        outputs["json"] = args.save_json
    if args.save_csv:
        outputs["csv"] = args.save_csv
    if args.save_suite_plot:
        outputs["suite_plot"] = args.save_suite_plot
    if args.save_report:
        outputs["report"] = args.save_report
    if outputs:
        manifest["outputs"] = outputs

    bundle = run_experiment(manifest)
    print(format_results_table(bundle["results"]))
    if args.summary:
        print()
        print(format_summary(summarize_results(bundle["results"])))
    if args.save_json:
        print(f"\nSaved preset JSON to {args.save_json}")
    if args.save_csv:
        print(f"Saved preset CSV to {args.save_csv}")
    if args.save_suite_plot:
        print(f"Saved preset plot to {args.save_suite_plot}")
    if args.save_report:
        print(f"Saved preset report to {args.save_report}")
    return 0


def _suite_manifest(suite_name: str) -> list[dict[str, object]]:
    manifest = []
    for index, case in enumerate(SUITES[suite_name], start=1):
        benchmark = case.build()
        manifest.append(
            {
                "index": index,
                "suite": suite_name,
                "benchmark": case.benchmark,
                "result_name": benchmark.name,
                "description": case.description,
                "n_qubits": benchmark.n_qubits,
                "parameters": benchmark.parameters,
                "metadata": benchmark.metadata or {},
            }
        )
    return manifest


def _print_suite_cases(suite_name: str, manifest: list[dict[str, object]]) -> None:
    print(f"Suite: {suite_name}")
    for case in manifest:
        parameters = ", ".join(
            f"{key}={value}" for key, value in sorted(case["parameters"].items())
        )
        print(f"{case['index']}. {case['benchmark']}: {case['description']}")
        print(f"   result_name={case['result_name']}; {parameters}")


def _draw_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    diagram = draw_benchmark(benchmark, args.backend, save_path=args.save_path)
    print(diagram)
    if args.save_path:
        print(f"\nSaved diagram to {args.save_path}")
    return 0


def _render_and_save(results: list[dict], args: argparse.Namespace) -> int:
    print(format_results_table(results))
    if args.summary:
        print()
        print(format_summary(summarize_results(results)))
    if args.save_json:
        save_json(results, args.save_json)
        print(f"\nSaved JSON to {args.save_json}")
    if args.save_csv:
        save_csv(results, args.save_csv)
        print(f"Saved CSV to {args.save_csv}")
    if args.save_plot:
        save_runtime_depth_plot(results, args.save_plot)
        print(f"Saved plot to {args.save_plot}")
    if args.save_distribution:
        save_distribution_plot(results, args.save_distribution)
        print(f"Saved distribution plot to {args.save_distribution}")
    if args.save_quality_plot:
        save_noise_quality_plot(results, args.save_quality_plot)
        print(f"Saved quality plot to {args.save_quality_plot}")
    if args.save_suite_plot:
        save_suite_runtime_plot(results, args.save_suite_plot)
        print(f"Saved suite plot to {args.save_suite_plot}")
    if args.save_heatmap:
        save_counts_heatmap(results, args.save_heatmap)
        print(f"Saved heatmap to {args.save_heatmap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
