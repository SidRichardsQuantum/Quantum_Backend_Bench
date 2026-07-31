"""Small neutral statevector simulator used for translation verification."""

from __future__ import annotations

import cmath
import math
import random
from collections import Counter
from typing import Any

from quantum_backend_bench.core.benchmark_spec import CircuitOperation


def simulate_statevector(
    n_qubits: int,
    operations: list[CircuitOperation],
    *,
    global_phase: float = 0.0,
) -> Any:
    """Return the exact statevector for a neutral circuit."""

    np = _numpy()
    state = np.zeros(2**n_qubits, dtype=complex)
    state[0] = 1.0
    for operation in operations:
        state = apply_operation(state, n_qubits, operation)
    if global_phase:
        state = state * np.exp(1j * global_phase)
    return state


def simulate_probabilities(
    n_qubits: int,
    operations: list[CircuitOperation],
    measurements: list[int],
) -> dict[str, float]:
    """Return exact probabilities for the selected measurement wires."""

    state = simulate_statevector(n_qubits, operations)
    probabilities: dict[str, float] = {}
    for index, amplitude in enumerate(state):
        basis = format(index, f"0{n_qubits}b")
        measured = "".join(basis[qubit] for qubit in measurements)
        probabilities[measured] = probabilities.get(measured, 0.0) + float(abs(amplitude) ** 2)
    return probabilities


def sample_counts(
    probabilities: dict[str, float],
    shots: int,
    seed: object | None = None,
) -> dict[str, int]:
    """Sample counts from a neutral probability distribution."""

    rng_seed = seed if isinstance(seed, (int, float, str, bytes, bytearray)) else 0
    rng = random.Random(rng_seed)
    states = sorted(probabilities)
    weights = [max(0.0, probabilities[state]) for state in states]
    samples = rng.choices(states, weights=weights, k=shots)
    return dict(Counter(samples))


def apply_operation(state: Any, n_qubits: int, operation: CircuitOperation) -> Any:
    """Apply one supported neutral operation to a statevector."""

    np = _numpy()
    gate = operation.gate
    q = operation.qubits
    params = operation.params

    if gate in {"BARRIER", "DELAY"}:
        return state
    if gate == "RESET":
        return _reset_qubit(state, n_qubits, q[0])
    if gate in {"H", "X", "Y", "Z", "S", "T", "SX", "P", "PHASE", "RX", "RY", "RZ", "U"}:
        return _single_qubit_operator(n_qubits, q[0], _single_qubit_gate(gate, params)) @ state
    if gate == "CNOT":
        return _controlled_permutation(state, n_qubits, q[0], q[1])
    if gate == "CCX":
        return _toffoli(state, n_qubits, q[0], q[1], q[2])
    if gate in {"CRX", "CRY", "CRZ"}:
        return _controlled_single_qubit(
            state,
            n_qubits,
            q[0],
            q[1],
            _single_qubit_gate(gate[1:], params),
        )
    if gate == "CZ":
        return _controlled_phase(state, n_qubits, q[0], q[1], phase=-1.0)
    if gate == "SWAP":
        return _swap(state, n_qubits, q[0], q[1])
    if gate == "CPHASE":
        return _controlled_phase(state, n_qubits, q[0], q[1], phase=np.exp(1j * params["theta"]))
    raise ValueError(f"Unsupported neutral simulator gate: {gate}")


def _reset_qubit(state: Any, n_qubits: int, qubit: int) -> Any:
    np = _numpy()
    output = np.zeros_like(state)
    for index, amplitude in enumerate(state):
        bits = list(format(index, f"0{n_qubits}b"))
        bits[qubit] = "0"
        output[int("".join(bits), 2)] += amplitude
    norm = np.linalg.norm(output)
    return output / norm if norm else output


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
    if gate == "SX":
        return 0.5 * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]], dtype=complex)
    if gate in {"P", "PHASE"}:
        return np.array([[1, 0], [0, np.exp(1j * params["theta"])]], dtype=complex)
    if gate == "U":
        theta = params["theta"]
        phi = params["phi"]
        lam = params["lambda"]
        return np.array(
            [
                [math.cos(theta / 2), -cmath.exp(1j * lam) * math.sin(theta / 2)],
                [
                    cmath.exp(1j * phi) * math.sin(theta / 2),
                    cmath.exp(1j * (phi + lam)) * math.cos(theta / 2),
                ],
            ],
            dtype=complex,
        )
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
    raise ValueError(f"Unsupported neutral one-qubit gate: {gate}")


def _single_qubit_operator(n_qubits: int, qubit: int, gate: Any) -> Any:
    np = _numpy()
    operator = np.array([[1]], dtype=complex)
    identity = np.eye(2, dtype=complex)
    for index in range(n_qubits):
        operator = np.kron(operator, gate if index == qubit else identity)
    return operator


def _controlled_permutation(state: Any, n_qubits: int, control: int, target: int) -> Any:
    np = _numpy()
    output = np.zeros_like(state)
    for index, amplitude in enumerate(state):
        bits = list(format(index, f"0{n_qubits}b"))
        if bits[control] == "1":
            bits[target] = "0" if bits[target] == "1" else "1"
        output[int("".join(bits), 2)] += amplitude
    return output


def _controlled_single_qubit(
    state: Any,
    n_qubits: int,
    control: int,
    target: int,
    gate: Any,
) -> Any:
    output = state.copy()
    affected_indexes = []
    for index in range(len(state)):
        bits = list(format(index, f"0{n_qubits}b"))
        if bits[control] == "1" and bits[target] == "0":
            bits[target] = "1"
            affected_indexes.append((index, int("".join(bits), 2)))
    for zero_index, one_index in affected_indexes:
        zero_amp = state[zero_index]
        one_amp = state[one_index]
        output[zero_index] = gate[0, 0] * zero_amp + gate[0, 1] * one_amp
        output[one_index] = gate[1, 0] * zero_amp + gate[1, 1] * one_amp
    return output


def _toffoli(
    state: Any,
    n_qubits: int,
    left_control: int,
    right_control: int,
    target: int,
) -> Any:
    np = _numpy()
    output = np.zeros_like(state)
    for index, amplitude in enumerate(state):
        bits = list(format(index, f"0{n_qubits}b"))
        if bits[left_control] == "1" and bits[right_control] == "1":
            bits[target] = "0" if bits[target] == "1" else "1"
        output[int("".join(bits), 2)] += amplitude
    return output


def _controlled_phase(
    state: Any,
    n_qubits: int,
    control: int,
    target: int,
    phase: complex,
) -> Any:
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


def _numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "NumPy is required for exact neutral-circuit verification. "
            'Install with: pip install "numpy".'
        ) from exc
    return np
