"""Small neutral statevector simulator used for translation verification."""

from __future__ import annotations

import cmath
import math
import random
from collections import Counter
from typing import Any

from quantum_backend_bench.core.benchmark_spec import CircuitOperation, NoiseInstruction
from quantum_backend_bench.core.noise import (
    noise_after_circuit,
    noise_after_operation,
    readout_noise,
    validate_noise,
)


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


def simulate_density_matrix(
    n_qubits: int,
    operations: list[CircuitOperation],
    noise: list[NoiseInstruction] | None = None,
) -> Any:
    """Return the exact density matrix for a neutral circuit and noise schedule."""

    np = _numpy()
    scheduled_noise = noise or []
    validate_noise(scheduled_noise, n_qubits, len(operations))
    dimension = 2**n_qubits
    density = np.zeros((dimension, dimension), dtype=complex)
    density[0, 0] = 1.0
    for operation_index, operation in enumerate(operations):
        density = _apply_density_operation(density, n_qubits, operation)
        for instruction in noise_after_operation(scheduled_noise, operation_index, operation):
            density = _apply_noise_instruction(density, n_qubits, instruction)
    for instruction in noise_after_circuit(scheduled_noise):
        density = _apply_noise_instruction(density, n_qubits, instruction)
    return density


def simulate_density_probabilities(
    n_qubits: int,
    operations: list[CircuitOperation],
    measurements: list[int],
    noise: list[NoiseInstruction] | None = None,
) -> dict[str, float]:
    """Return exact measurement probabilities, including readout confusion."""

    scheduled_noise = noise or []
    density = simulate_density_matrix(n_qubits, operations, scheduled_noise)
    probabilities: dict[str, float] = {}
    for index, probability in enumerate(_numpy().real(_numpy().diag(density))):
        basis = format(index, f"0{n_qubits}b")
        measured = "".join(basis[qubit] for qubit in measurements)
        probabilities[measured] = probabilities.get(measured, 0.0) + max(0.0, float(probability))
    for instruction in readout_noise(scheduled_noise):
        probabilities = _apply_readout_error(
            probabilities, measurements, instruction.targets, instruction.probability
        )
    return probabilities


def density_matrix_trace_distance(left: Any, right: Any) -> float:
    """Return the quantum trace distance between two density matrices."""

    np = _numpy()
    if left.shape != right.shape:
        return float("inf")
    delta = left - right
    delta = (delta + delta.conjugate().T) / 2
    return float(0.5 * np.sum(np.abs(np.linalg.eigvalsh(delta))))


def _apply_density_operation(density: Any, n_qubits: int, operation: CircuitOperation) -> Any:
    if operation.gate in {"BARRIER", "DELAY"}:
        return density
    if operation.gate == "RESET":
        np = _numpy()
        zero = np.array([[1, 0], [0, 0]], dtype=complex)
        lower = np.array([[0, 1], [0, 0]], dtype=complex)
        return _apply_kraus(
            density,
            [_single_qubit_operator(n_qubits, operation.qubits[0], item) for item in (zero, lower)],
        )
    operator = _operation_operator(n_qubits, operation)
    return operator @ density @ operator.conjugate().T


def _operation_operator(n_qubits: int, operation: CircuitOperation) -> Any:
    np = _numpy()
    dimension = 2**n_qubits
    operator = np.zeros((dimension, dimension), dtype=complex)
    for column in range(dimension):
        basis = np.zeros(dimension, dtype=complex)
        basis[column] = 1.0
        operator[:, column] = apply_operation(basis, n_qubits, operation)
    return operator


def _apply_noise_instruction(density: Any, n_qubits: int, instruction: NoiseInstruction) -> Any:
    np = _numpy()
    identity = np.eye(2, dtype=complex)
    x = np.array([[0, 1], [1, 0]], dtype=complex)
    y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    z = np.array([[1, 0], [0, -1]], dtype=complex)
    p = instruction.probability
    if instruction.channel == "depolarizing":
        local_kraus = [np.sqrt(1 - p) * identity]
        local_kraus.extend(np.sqrt(p / 3) * pauli for pauli in (x, y, z))
    elif instruction.channel == "bit_flip":
        local_kraus = [np.sqrt(1 - p) * identity, np.sqrt(p) * x]
    elif instruction.channel == "phase_flip":
        local_kraus = [np.sqrt(1 - p) * identity, np.sqrt(p) * z]
    elif instruction.channel == "amplitude_damping":
        local_kraus = [
            np.array([[1, 0], [0, np.sqrt(1 - p)]], dtype=complex),
            np.array([[0, np.sqrt(p)], [0, 0]], dtype=complex),
        ]
    else:
        raise ValueError(f"Noise channel '{instruction.channel}' is not a quantum channel.")
    output = density
    for target in instruction.targets:
        output = _apply_kraus(
            output,
            [_single_qubit_operator(n_qubits, target, item) for item in local_kraus],
        )
    return output


def _apply_kraus(density: Any, operators: list[Any]) -> Any:
    np = _numpy()
    output = np.zeros_like(density)
    for operator in operators:
        output += operator @ density @ operator.conjugate().T
    return output


def _apply_readout_error(
    probabilities: dict[str, float],
    measurements: list[int],
    targets: tuple[int, ...],
    probability: float,
) -> dict[str, float]:
    output = dict(probabilities)
    for target in targets:
        if target not in measurements:
            continue
        position = measurements.index(target)
        updated: dict[str, float] = {}
        for bitstring, value in output.items():
            flipped = list(bitstring)
            flipped[position] = "1" if flipped[position] == "0" else "0"
            flipped_key = "".join(flipped)
            updated[bitstring] = updated.get(bitstring, 0.0) + (1 - probability) * value
            updated[flipped_key] = updated.get(flipped_key, 0.0) + probability * value
        output = updated
    return output


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
