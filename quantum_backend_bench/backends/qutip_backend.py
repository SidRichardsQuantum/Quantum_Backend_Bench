"""QuTiP-backed local statevector simulator backend."""

from __future__ import annotations

import math
import random
import time
from collections import Counter
from typing import Any

from quantum_backend_bench.backends.base_backend import BaseBackend
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


class QuTiPBackend(BaseBackend):
    """Execute benchmarks with a QuTiP-compatible local statevector simulation."""

    name = "qutip"

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        try:
            import qutip
        except ImportError as exc:
            raise RuntimeError(
                'QuTiP is not installed. Install with: pip install "quantum-backend-bench[qutip]"'
            ) from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("QuTiP backend requires InternalCircuit benchmark data.")
        return {
            "qutip": qutip,
            "n_qubits": circuit_data.n_qubits,
            "operations": circuit_data.operations,
            "measurements": circuit_data.measurements or list(range(circuit_data.n_qubits)),
        }

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        native = self.build_native_circuit(benchmark)
        metadata = benchmark.metadata or {}

        start = time.perf_counter()
        probabilities = _simulate_probabilities(
            native["n_qubits"], native["operations"], native["measurements"]
        )
        counts = _sample_counts(probabilities, shots=shots, seed=benchmark.parameters.get("seed"))
        runtime = time.perf_counter() - start
        seed = benchmark.parameters.get("seed")

        return {
            "counts": counts,
            "runtime_seconds": runtime,
            "noise_supported": False,
            "noise_applied": False,
            "seed_supported": True,
            "seed_applied": seed is not None,
            "notes": (
                "QuTiP statevector execution completed without noise injection in this adapter."
                if metadata.get("noise_level", 0.0) > 0
                else "QuTiP statevector execution completed."
            ),
        }


def _simulate_probabilities(
    n_qubits: int, operations: list[CircuitOperation], measurements: list[int]
) -> dict[str, float]:
    np = _numpy()
    state = np.zeros(2**n_qubits, dtype=complex)
    state[0] = 1.0
    for operation in operations:
        state = _apply_operation(state, n_qubits, operation)

    probabilities: dict[str, float] = {}
    for index, amplitude in enumerate(state):
        basis = format(index, f"0{n_qubits}b")
        measured = "".join(basis[qubit] for qubit in measurements)
        probabilities[measured] = probabilities.get(measured, 0.0) + float(abs(amplitude) ** 2)
    return probabilities


def _apply_operation(state: Any, n_qubits: int, operation: CircuitOperation) -> Any:
    np = _numpy()
    gate = operation.gate
    q = operation.qubits
    params = operation.params

    if gate in {"H", "X", "Y", "Z", "S", "T", "RX", "RY", "RZ"}:
        return _single_qubit_operator(n_qubits, q[0], _single_qubit_gate(gate, params)) @ state
    if gate == "CNOT":
        return _controlled_permutation(state, n_qubits, q[0], q[1], target_gate="X")
    if gate == "CZ":
        return _controlled_phase(state, n_qubits, q[0], q[1], phase=-1.0)
    if gate == "SWAP":
        return _swap(state, n_qubits, q[0], q[1])
    if gate == "CPHASE":
        return _controlled_phase(state, n_qubits, q[0], q[1], phase=np.exp(1j * params["theta"]))
    raise ValueError(f"Unsupported QuTiP gate: {gate}")


def _single_qubit_gate(gate: str, params: dict[str, Any]) -> Any:
    np = _numpy()
    if gate == "H":
        return np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
    if gate == "X":
        return np.array([[0, 1], [1, 0]], dtype=complex)
    if gate == "Y":
        return np.array([[0, -1j], [1j, 0]], dtype=complex)
    if gate == "Z":
        return np.array([[1, 0], [0, -1]], dtype=complex)
    if gate == "S":
        return np.array([[1, 0], [0, 1j]], dtype=complex)
    if gate == "T":
        return np.array([[1, 0], [0, np.exp(1j * math.pi / 4)]], dtype=complex)
    if gate == "RX":
        theta = params["theta"]
        return np.array(
            [
                [math.cos(theta / 2), -1j * math.sin(theta / 2)],
                [-1j * math.sin(theta / 2), math.cos(theta / 2)],
            ],
            dtype=complex,
        )
    if gate == "RY":
        theta = params["theta"]
        return np.array(
            [
                [math.cos(theta / 2), -math.sin(theta / 2)],
                [math.sin(theta / 2), math.cos(theta / 2)],
            ],
            dtype=complex,
        )
    if gate == "RZ":
        theta = params["theta"]
        return np.array([[np.exp(-0.5j * theta), 0], [0, np.exp(0.5j * theta)]], dtype=complex)
    raise ValueError(f"Unsupported one-qubit gate: {gate}")


def _single_qubit_operator(n_qubits: int, qubit: int, gate: Any) -> Any:
    np = _numpy()
    operator = np.array([[1]], dtype=complex)
    identity = np.eye(2, dtype=complex)
    for index in range(n_qubits):
        operator = np.kron(operator, gate if index == qubit else identity)
    return operator


def _controlled_permutation(
    state: Any, n_qubits: int, control: int, target: int, target_gate: str
) -> Any:
    np = _numpy()
    if target_gate != "X":
        raise ValueError(f"Unsupported controlled target gate: {target_gate}")
    output = np.zeros_like(state)
    for index, amplitude in enumerate(state):
        bits = list(format(index, f"0{n_qubits}b"))
        if bits[control] == "1":
            bits[target] = "0" if bits[target] == "1" else "1"
        output[int("".join(bits), 2)] += amplitude
    return output


def _controlled_phase(state: Any, n_qubits: int, control: int, target: int, phase: complex) -> Any:
    output = state.copy()
    for index in range(len(output)):
        bits = format(index, f"0{n_qubits}b")
        if bits[control] == "1" and bits[target] == "1":
            output[index] *= phase
    return output


def _swap(state: Any, n_qubits: int, left: int, right: int) -> Any:
    np = _numpy()
    output = np.zeros_like(state)
    for index, amplitude in enumerate(state):
        bits = list(format(index, f"0{n_qubits}b"))
        bits[left], bits[right] = bits[right], bits[left]
        output[int("".join(bits), 2)] += amplitude
    return output


def _sample_counts(
    probabilities: dict[str, float], shots: int, seed: object | None = None
) -> dict[str, int]:
    rng = random.Random(0 if seed is None else seed)
    states = sorted(probabilities)
    weights = [max(0.0, probabilities[state]) for state in states]
    samples = rng.choices(states, weights=weights, k=shots)
    return dict(Counter(samples))


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            'NumPy is required by the QuTiP backend. Install with: pip install "quantum-backend-bench[qutip]"'
        ) from exc
    return np
