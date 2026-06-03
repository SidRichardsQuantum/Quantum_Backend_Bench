"""Benchmark construction helpers shared by CLI and manifests."""

from __future__ import annotations

from typing import Callable

from quantum_backend_bench.benchmarks import (
    amplitude_estimation,
    bernstein_vazirani,
    deutsch_jozsa,
    ghz,
    grover,
    hamiltonian_sim,
    phase_estimation,
    qft,
    qaoa_maxcut,
    quantum_kernel,
    quantum_volume,
    random_circuit,
    vqe_ansatz,
)
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec

BENCHMARK_BUILDERS: dict[str, Callable[..., BenchmarkSpec]] = {
    "amplitude-estimation": amplitude_estimation.build_benchmark,
    "bernstein-vazirani": bernstein_vazirani.build_benchmark,
    "deutsch-jozsa": deutsch_jozsa.build_benchmark,
    "ghz": ghz.build_benchmark,
    "grover": grover.build_benchmark,
    "hamiltonian-sim": hamiltonian_sim.build_benchmark,
    "phase-estimation": phase_estimation.build_benchmark,
    "qft": qft.build_benchmark,
    "qaoa-maxcut": qaoa_maxcut.build_benchmark,
    "quantum-kernel": quantum_kernel.build_benchmark,
    "quantum-volume": quantum_volume.build_benchmark,
    "random-circuit": random_circuit.build_benchmark,
    "vqe-ansatz": vqe_ansatz.build_benchmark,
}


def build_benchmark_from_config(config: dict[str, object]) -> BenchmarkSpec:
    """Build a benchmark from CLI-style manifest configuration."""

    name = str(config["benchmark"])
    builder = BENCHMARK_BUILDERS[name]
    kwargs: dict[str, object] = {}
    if config.get("n_qubits") is not None:
        kwargs["n_qubits"] = config["n_qubits"]
    if name in {"quantum-volume", "random-circuit", "quantum-kernel", "vqe-ansatz"}:
        kwargs["depth"] = config.get("depth", 10)
    if name in {"quantum-volume", "random-circuit"}:
        kwargs["seed"] = config.get("seed", 42)
    if name == "bernstein-vazirani":
        kwargs["secret_string"] = config.get("secret_string")
    elif name == "deutsch-jozsa":
        kwargs["oracle_type"] = config.get("oracle_type", "balanced")
        kwargs["bitmask"] = config.get("bitmask")
        kwargs["constant_value"] = config.get("constant_value", 0)
    elif name == "grover":
        n_qubits = int(config.get("n_qubits") or 3)
        kwargs["marked_state"] = config.get("marked_state") or ("1" * n_qubits)
        kwargs["iterations"] = config.get("iterations")
    elif name == "amplitude-estimation":
        kwargs["probability"] = config.get("probability", 0.25)
        kwargs["iterations"] = config.get("iterations", 1)
    elif name == "hamiltonian-sim":
        kwargs["time"] = config.get("time", 0.5)
        kwargs["trotter_steps"] = config.get("trotter_steps", 1)
    elif name == "phase-estimation":
        kwargs["phase"] = config.get("phase", 0.25)
    elif name == "qaoa-maxcut":
        kwargs["gamma"] = config.get("gamma", 0.8)
        kwargs["beta"] = config.get("beta", 0.4)
        kwargs["graph"] = config.get("graph", "ring")
    elif name == "quantum-kernel":
        kwargs["feature_scale"] = config.get("feature_scale", 0.7)
    elif name == "vqe-ansatz":
        kwargs["theta"] = config.get("theta", 0.3)
    return builder(**kwargs)
