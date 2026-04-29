"""Command-line interface for quantum-backend-bench."""

from __future__ import annotations

import argparse
import json

from quantum_backend_bench.backends import BACKEND_REGISTRY
from quantum_backend_bench.benchmarks import noise_sensitivity
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec
from quantum_backend_bench.core.diff import (
    DEFAULT_DIFF_METRICS,
    compare_result_sets,
    diff_passed,
    format_diff_table,
    load_result_file,
)
from quantum_backend_bench.core.discovery import BENCHMARK_INFOS, backend_capabilities
from quantum_backend_bench.core.doctor import doctor_checks, doctor_passed, format_doctor_table
from quantum_backend_bench.core.draw import draw_benchmark
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
    recommend_parser.set_defaults(func=_recommend_command)

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
    run_parser.set_defaults(func=_run_command)

    compare_parser = subparsers.add_parser(
        "compare", help="Compare a benchmark across multiple backends."
    )
    _add_benchmark_arguments(compare_parser)
    compare_parser.add_argument(
        "--backends", nargs="+", required=True, choices=sorted(BACKEND_REGISTRY)
    )
    compare_parser.set_defaults(func=_compare_command)

    noise_parser = subparsers.add_parser("noise-sweep", help="Run a depolarizing noise sweep.")
    _add_benchmark_arguments(noise_parser)
    noise_parser.add_argument("--backend", required=True, choices=sorted(BACKEND_REGISTRY))
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
    capabilities = [
        capability
        for capability in backend_capabilities()
        if capability.role == "execution" and capability.installed
    ]
    ranked = _rank_capabilities(capabilities, args.use_case)
    print(f"Recommended installed backends for {args.use_case}")
    if not ranked:
        print("No installed execution backends found.")
        return 1
    for index, capability in enumerate(ranked, start=1):
        reasons = _recommendation_reasons(capability, args.use_case)
        print(f"{index}. {capability.name}: {', '.join(reasons)}")
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


def _recommendation_reasons(capability: object, use_case: str) -> list[str]:
    reasons = []
    if getattr(capability, "local_only"):
        reasons.append("local")
    if getattr(capability, "shot_sampling"):
        reasons.append("shot sampling")
    if getattr(capability, "noise_support") != "not injected":
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


def _build_benchmark_from_args(args: argparse.Namespace) -> BenchmarkSpec:
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
    ):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value
    return build_benchmark_from_config(config)


def _run_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    results = run_benchmark(benchmark, [args.backend], shots=args.shots, repeats=args.repeats)
    return _render_and_save(results, args)


def _compare_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    results = run_benchmark(benchmark, list(args.backends), shots=args.shots, repeats=args.repeats)
    return _render_and_save(results, args)


def _noise_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    noisy_specs = noise_sensitivity.build_benchmark(benchmark, noise_levels=args.noise_levels)
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
