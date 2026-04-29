"""Benchmark and backend discovery helpers."""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass
from typing import Any

from quantum_backend_bench.backends import BACKEND_REGISTRY


@dataclass(frozen=True, slots=True)
class BenchmarkInfo:
    """Human-readable benchmark metadata for CLI discovery."""

    cli_name: str
    result_name: str
    family: str
    description: str
    key_parameters: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BackendCapability:
    """Installed-state and capability metadata for one backend or integration."""

    name: str
    role: str
    installed: bool
    install_extra: str
    noise_support: str
    shot_sampling: bool
    exact_statevector: bool
    external_process: bool
    includes_transpilation_time: bool
    local_only: bool
    notes: str


BENCHMARK_INFOS: dict[str, BenchmarkInfo] = {
    "bernstein-vazirani": BenchmarkInfo(
        cli_name="bernstein-vazirani",
        result_name="bernstein_vazirani",
        family="oracle",
        description="Recover a hidden bitstring with one oracle query.",
        key_parameters=("n_qubits", "secret_string"),
    ),
    "deutsch-jozsa": BenchmarkInfo(
        cli_name="deutsch-jozsa",
        result_name="deutsch_jozsa",
        family="oracle",
        description="Classify constant and linear balanced oracle cases.",
        key_parameters=("n_qubits", "oracle_type", "bitmask", "constant_value"),
    ),
    "ghz": BenchmarkInfo(
        cli_name="ghz",
        result_name="ghz",
        family="entanglement",
        description="Generate GHZ states with ideal all-zero/all-one outcomes.",
        key_parameters=("n_qubits",),
    ),
    "grover": BenchmarkInfo(
        cli_name="grover",
        result_name="grover",
        family="search",
        description="Run a small marked-state search benchmark.",
        key_parameters=("n_qubits", "marked_state", "iterations"),
    ),
    "hamiltonian-sim": BenchmarkInfo(
        cli_name="hamiltonian-sim",
        result_name="hamiltonian_sim",
        family="simulation",
        description="Run first-order Trotterized Ising-style evolution.",
        key_parameters=("n_qubits", "time", "trotter_steps"),
    ),
    "qft": BenchmarkInfo(
        cli_name="qft",
        result_name="qft",
        family="transform",
        description="Build a Quantum Fourier Transform workload.",
        key_parameters=("n_qubits",),
    ),
    "quantum-volume": BenchmarkInfo(
        cli_name="quantum-volume",
        result_name="quantum_volume",
        family="synthetic",
        description="Build a shuffled-pair random layered workload.",
        key_parameters=("n_qubits", "depth", "seed"),
    ),
    "random-circuit": BenchmarkInfo(
        cli_name="random-circuit",
        result_name="random_circuit",
        family="synthetic",
        description="Build a reproducible random circuit with fixed gate choices.",
        key_parameters=("n_qubits", "depth", "seed"),
    ),
}


def backend_capabilities() -> list[BackendCapability]:
    """Return installed-state and support details for known integrations."""

    capabilities = [
        BackendCapability(
            name="cirq",
            role="execution",
            installed=_is_module_installed("cirq"),
            install_extra="cirq",
            noise_support="depolarizing",
            shot_sampling=True,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Uses cirq.Simulator.",
        ),
        BackendCapability(
            name="pennylane",
            role="execution",
            installed=_is_module_installed("pennylane"),
            install_extra="pennylane",
            noise_support="depolarizing",
            shot_sampling=True,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Uses default.qubit/default.mixed.",
        ),
        BackendCapability(
            name="braket_local",
            role="execution",
            installed=_is_module_installed("braket"),
            install_extra="braket",
            noise_support="not injected",
            shot_sampling=True,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Uses Amazon Braket LocalSimulator only.",
        ),
        BackendCapability(
            name="qiskit_aer",
            role="execution",
            installed=_is_module_installed("qiskit") and _is_module_installed("qiskit_aer"),
            install_extra="qiskit",
            noise_support="not injected",
            shot_sampling=True,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=True,
            local_only=True,
            notes="Uses Qiskit AerSimulator locally.",
        ),
        BackendCapability(
            name="cudaq",
            role="execution",
            installed=_is_module_installed("cudaq"),
            install_extra="cudaq",
            noise_support="not injected",
            shot_sampling=True,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Uses NVIDIA CUDA-Q local simulation target.",
        ),
        BackendCapability(
            name="pyquil_qvm",
            role="execution",
            installed=_is_module_installed("pyquil") and _has_executables("qvm", "quilc"),
            install_extra="pyquil",
            noise_support="not injected",
            shot_sampling=True,
            exact_statevector=False,
            external_process=True,
            includes_transpilation_time=True,
            local_only=True,
            notes="Uses pyQuil with local QVM/quilc runtime.",
        ),
        BackendCapability(
            name="qutip",
            role="execution",
            installed=_is_module_installed("qutip"),
            install_extra="qutip",
            noise_support="not injected",
            shot_sampling=True,
            exact_statevector=True,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Uses a QuTiP-compatible local statevector simulation.",
        ),
        BackendCapability(
            name="pytket",
            role="analysis/draw",
            installed=_is_module_installed("pytket"),
            install_extra="tket",
            noise_support="n/a",
            shot_sampling=False,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Used for structural metrics, not execution.",
        ),
        BackendCapability(
            name="matplotlib",
            role="plotting",
            installed=_is_module_installed("matplotlib"),
            install_extra="plot",
            noise_support="n/a",
            shot_sampling=False,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Required for plot output options.",
        ),
        BackendCapability(
            name="qbraid",
            role="interop/runtime",
            installed=_is_module_installed("qbraid"),
            install_extra="qbraid",
            noise_support="n/a",
            shot_sampling=False,
            exact_statevector=False,
            external_process=True,
            includes_transpilation_time=False,
            local_only=False,
            notes="Pip-installable SDK; reported for interop, not used as a local execution backend.",
        ),
        BackendCapability(
            name="qsharp",
            role="language/runtime",
            installed=_is_module_installed("qsharp"),
            install_extra="qsharp",
            noise_support="n/a",
            shot_sampling=False,
            exact_statevector=False,
            external_process=False,
            includes_transpilation_time=False,
            local_only=True,
            notes="Pip-installable Q# runtime; reported for interop, not used as a circuit backend.",
        ),
    ]
    known_execution = {
        capability.name for capability in capabilities if capability.role == "execution"
    }
    missing_registry = sorted(set(BACKEND_REGISTRY) - known_execution)
    for backend_name in missing_registry:
        capabilities.append(
            BackendCapability(
                name=backend_name,
                role="execution",
                installed=False,
                install_extra="all",
                noise_support="unknown",
                shot_sampling=False,
                exact_statevector=False,
                external_process=False,
                includes_transpilation_time=False,
                local_only=False,
                notes="Registered backend without discovery metadata.",
            )
        )
    return capabilities


def result_case_label(result: dict[str, Any]) -> str:
    """Return a stable human-readable label for a result dict."""

    metadata = result.get("metadata") or {}
    if metadata.get("case_label"):
        return str(metadata["case_label"])
    return case_label(
        benchmark=result["benchmark"],
        n_qubits=result["n_qubits"],
        parameters=result.get("parameters") or {},
    )


def case_label(benchmark: str, n_qubits: int, parameters: dict[str, Any]) -> str:
    """Return a concise label for a benchmark case."""

    if "noise_level" in parameters:
        return f"{benchmark} p={parameters['noise_level']}"
    if "secret_string" in parameters:
        return f"{benchmark} s={_ket(parameters['secret_string'])}"
    if "bitmask" in parameters and parameters.get("oracle_type") == "balanced":
        return f"{benchmark} m={_ket(parameters['bitmask'])}"
    if parameters.get("oracle_type") == "constant":
        return f"{benchmark} c={parameters.get('constant_value', 0)}"
    if "marked_state" in parameters:
        return f"{benchmark} target={_ket(parameters['marked_state'])}"
    if "depth" in parameters:
        return f"{benchmark} n={n_qubits} d={parameters['depth']}"
    return f"{benchmark} n={n_qubits}"


def _is_module_installed(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _has_executables(*names: str) -> bool:
    return all(shutil.which(name) is not None for name in names)


def _ket(state: Any) -> str:
    text = str(state)
    if text.startswith("|") and text.endswith(">"):
        return text
    return f"|{text}>"
