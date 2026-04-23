"""Command-line interface for quantum-backend-bench."""

from __future__ import annotations

import argparse
from typing import Callable

from quantum_backend_bench.benchmarks import (
    ghz,
    grover,
    hamiltonian_sim,
    noise_sensitivity,
    qft,
    random_circuit,
)
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec
from quantum_backend_bench.core.draw import draw_benchmark
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.utils.formatting import format_results_table
from quantum_backend_bench.utils.io import save_json
from quantum_backend_bench.utils.plotting import save_runtime_depth_plot

BENCHMARK_BUILDERS: dict[str, Callable[..., BenchmarkSpec]] = {
    "ghz": ghz.build_benchmark,
    "grover": grover.build_benchmark,
    "hamiltonian-sim": hamiltonian_sim.build_benchmark,
    "qft": qft.build_benchmark,
    "random-circuit": random_circuit.build_benchmark,
}


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quantum-bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single benchmark on one backend.")
    _add_benchmark_arguments(run_parser)
    run_parser.add_argument(
        "--backend", required=True, choices=["cirq", "pennylane", "braket_local"]
    )
    run_parser.set_defaults(func=_run_command)

    compare_parser = subparsers.add_parser(
        "compare", help="Compare a benchmark across multiple backends."
    )
    _add_benchmark_arguments(compare_parser)
    compare_parser.add_argument(
        "--backends", nargs="+", required=True, choices=["cirq", "pennylane", "braket_local"]
    )
    compare_parser.set_defaults(func=_compare_command)

    noise_parser = subparsers.add_parser("noise-sweep", help="Run a depolarizing noise sweep.")
    _add_benchmark_arguments(noise_parser)
    noise_parser.add_argument(
        "--backend", required=True, choices=["cirq", "pennylane", "braket_local"]
    )
    noise_parser.add_argument(
        "--noise-levels", nargs="+", type=float, default=[0.0, 0.001, 0.005, 0.01, 0.02]
    )
    noise_parser.set_defaults(func=_noise_command)

    draw_parser = subparsers.add_parser("draw", help="Render a circuit diagram using a native SDK.")
    _add_benchmark_arguments(draw_parser)
    draw_parser.add_argument(
        "--backend", required=True, choices=["cirq", "pennylane", "braket_local", "tket"]
    )
    draw_parser.add_argument("--save-path")
    draw_parser.set_defaults(func=_draw_command)

    for command_parser in (run_parser, compare_parser, noise_parser):
        command_parser.add_argument("--shots", type=int, default=1024)
        command_parser.add_argument("--save-json")
        command_parser.add_argument("--save-plot")

    return parser


def _add_benchmark_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("benchmark", choices=sorted(BENCHMARK_BUILDERS))
    parser.add_argument("--n-qubits", type=int, default=None)
    parser.add_argument("--depth", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--marked-state", default=None)
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--time", type=float, default=0.5)
    parser.add_argument("--trotter-steps", type=int, default=1)


def _build_benchmark_from_args(args: argparse.Namespace) -> BenchmarkSpec:
    builder = BENCHMARK_BUILDERS[args.benchmark]
    kwargs: dict[str, object] = {}
    if args.n_qubits is not None:
        kwargs["n_qubits"] = args.n_qubits
    if args.benchmark == "random-circuit":
        kwargs["depth"] = args.depth
        kwargs["seed"] = args.seed
    elif args.benchmark == "grover":
        kwargs["marked_state"] = args.marked_state or ("1" * (args.n_qubits or 3))
        kwargs["iterations"] = args.iterations
    elif args.benchmark == "hamiltonian-sim":
        kwargs["time"] = args.time
        kwargs["trotter_steps"] = args.trotter_steps
    return builder(**kwargs)


def _run_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    results = run_benchmark(benchmark, [args.backend], shots=args.shots)
    return _render_and_save(results, args)


def _compare_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    results = run_benchmark(benchmark, list(args.backends), shots=args.shots)
    return _render_and_save(results, args)


def _noise_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    noisy_specs = noise_sensitivity.build_benchmark(benchmark, noise_levels=args.noise_levels)
    results = []
    for spec in noisy_specs:
        results.extend(run_benchmark(spec, [args.backend], shots=args.shots))
    return _render_and_save(results, args)


def _draw_command(args: argparse.Namespace) -> int:
    benchmark = _build_benchmark_from_args(args)
    diagram = draw_benchmark(benchmark, args.backend, save_path=args.save_path)
    print(diagram)
    if args.save_path:
        print(f"\nSaved diagram to {args.save_path}")
    return 0


def _render_and_save(results: list[dict], args: argparse.Namespace) -> int:
    print(format_results_table(results))
    if args.save_json:
        save_json(results, args.save_json)
        print(f"\nSaved JSON to {args.save_json}")
    if args.save_plot:
        save_runtime_depth_plot(results, args.save_plot)
        print(f"Saved plot to {args.save_plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
