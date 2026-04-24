"""Named benchmark suite presets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from quantum_backend_bench.benchmarks import (
    bernstein_vazirani,
    deutsch_jozsa,
    ghz,
    grover,
    hamiltonian_sim,
    qft,
    quantum_volume,
    random_circuit,
)
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec


@dataclass(frozen=True, slots=True)
class SuiteCase:
    """One benchmark case inside a named suite."""

    benchmark: str
    description: str
    build: Callable[[], BenchmarkSpec]


SUITES: dict[str, list[SuiteCase]] = {
    "smoke": [
        SuiteCase("ghz", "Small GHZ sanity check", lambda: ghz.build_benchmark(n_qubits=3)),
        SuiteCase(
            "bernstein-vazirani",
            "Small oracle secret-string check",
            lambda: bernstein_vazirani.build_benchmark(n_qubits=4, secret_string="101"),
        ),
        SuiteCase(
            "grover",
            "Small target-state success check",
            lambda: grover.build_benchmark(n_qubits=2, marked_state="11"),
        ),
    ],
    "standard": [
        SuiteCase("ghz", "Entanglement baseline", lambda: ghz.build_benchmark(n_qubits=5)),
        SuiteCase(
            "bernstein-vazirani",
            "Oracle secret-string recovery",
            lambda: bernstein_vazirani.build_benchmark(n_qubits=5, secret_string="1011"),
        ),
        SuiteCase(
            "deutsch-jozsa",
            "Balanced oracle classification",
            lambda: deutsch_jozsa.build_benchmark(n_qubits=5, bitmask="1100"),
        ),
        SuiteCase("qft", "Controlled-phase workload", lambda: qft.build_benchmark(n_qubits=4)),
        SuiteCase(
            "random-circuit",
            "Reproducible synthetic circuit",
            lambda: random_circuit.build_benchmark(n_qubits=4, depth=10, seed=42),
        ),
        SuiteCase(
            "grover",
            "Search target benchmark",
            lambda: grover.build_benchmark(n_qubits=3, marked_state="101"),
        ),
        SuiteCase(
            "hamiltonian-sim",
            "Trotterized Ising-style evolution",
            lambda: hamiltonian_sim.build_benchmark(n_qubits=4, time=1.0, trotter_steps=2),
        ),
        SuiteCase(
            "quantum-volume",
            "Layered randomized workload",
            lambda: quantum_volume.build_benchmark(n_qubits=4, depth=4, seed=42),
        ),
    ],
    "scaling": [
        SuiteCase("ghz", "GHZ with 3 qubits", lambda: ghz.build_benchmark(n_qubits=3)),
        SuiteCase("ghz", "GHZ with 5 qubits", lambda: ghz.build_benchmark(n_qubits=5)),
        SuiteCase("ghz", "GHZ with 7 qubits", lambda: ghz.build_benchmark(n_qubits=7)),
        SuiteCase("qft", "QFT with 3 qubits", lambda: qft.build_benchmark(n_qubits=3)),
        SuiteCase("qft", "QFT with 5 qubits", lambda: qft.build_benchmark(n_qubits=5)),
        SuiteCase(
            "quantum-volume",
            "Quantum-volume-style circuit with 4 qubits",
            lambda: quantum_volume.build_benchmark(n_qubits=4, depth=4, seed=42),
        ),
        SuiteCase(
            "quantum-volume",
            "Quantum-volume-style circuit with 6 qubits",
            lambda: quantum_volume.build_benchmark(n_qubits=6, depth=6, seed=42),
        ),
        SuiteCase(
            "random-circuit",
            "Random circuit with depth 8",
            lambda: random_circuit.build_benchmark(n_qubits=4, depth=8, seed=42),
        ),
        SuiteCase(
            "random-circuit",
            "Random circuit with depth 16",
            lambda: random_circuit.build_benchmark(n_qubits=4, depth=16, seed=42),
        ),
    ],
}


def build_suite(name: str) -> list[BenchmarkSpec]:
    """Build all benchmark specs for a named suite."""

    try:
        cases = SUITES[name]
    except KeyError as exc:
        available = ", ".join(sorted(SUITES))
        raise ValueError(f"Unknown suite '{name}'. Available suites: {available}") from exc
    return [case.build() for case in cases]
