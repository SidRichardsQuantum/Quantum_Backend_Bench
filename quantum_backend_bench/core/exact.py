"""Exact probability helpers for internal benchmark circuits."""

from __future__ import annotations

from typing import Any

from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec, InternalCircuit


def exact_probabilities(benchmark: BenchmarkSpec, *, top_k: int | None = None) -> dict[str, float]:
    """Return exact measurement probabilities for a benchmark."""

    from quantum_backend_bench.backends.qutip_backend import _simulate_probabilities

    circuit_data = _internal_circuit(benchmark)
    measurements = circuit_data.measurements or list(range(circuit_data.n_qubits))
    probabilities = _simulate_probabilities(
        circuit_data.n_qubits, circuit_data.operations, measurements
    )
    return _top_k(probabilities, top_k)


def exact_amplitudes(
    benchmark: BenchmarkSpec, *, top_k: int | None = None
) -> dict[str, dict[str, float]]:
    """Return exact computational-basis amplitudes for a benchmark."""

    state = _statevector(benchmark)
    circuit_data = _internal_circuit(benchmark)
    amplitudes = {
        format(index, f"0{circuit_data.n_qubits}b"): {
            "real": float(value.real),
            "imag": float(value.imag),
        }
        for index, value in enumerate(state)
        if abs(value) > 1e-12
    }
    if top_k is None:
        return dict(sorted(amplitudes.items()))
    ranked = sorted(
        amplitudes.items(), key=lambda item: -(item[1]["real"] ** 2 + item[1]["imag"] ** 2)
    )
    return dict(ranked[:top_k])


def pauli_z_expectation(benchmark: BenchmarkSpec, observable: str) -> float:
    """Return expectation for a tensor product of I/Z terms, e.g. ``ZZI``."""

    circuit_data = _internal_circuit(benchmark)
    normalized = observable.upper()
    if len(normalized) != circuit_data.n_qubits or set(normalized) - {"I", "Z"}:
        raise ValueError("Observable must contain only I/Z and match n_qubits.")
    state = _statevector(benchmark)
    total = 0.0
    for index, amplitude in enumerate(state):
        bits = format(index, f"0{circuit_data.n_qubits}b")
        eigenvalue = 1
        for bit, term in zip(bits, normalized, strict=True):
            if term == "Z" and bit == "1":
                eigenvalue *= -1
        total += eigenvalue * float(abs(amplitude) ** 2)
    return total


def _statevector(benchmark: BenchmarkSpec) -> Any:
    from quantum_backend_bench.backends.qutip_backend import _apply_operation, _numpy

    circuit_data = _internal_circuit(benchmark)
    np = _numpy()
    state = np.zeros(2**circuit_data.n_qubits, dtype=complex)
    state[0] = 1.0
    for operation in circuit_data.operations:
        state = _apply_operation(state, circuit_data.n_qubits, operation)
    return state


def _internal_circuit(benchmark: BenchmarkSpec) -> InternalCircuit:
    circuit_data = (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)
    if not isinstance(circuit_data, InternalCircuit):
        raise TypeError("Exact probabilities require an InternalCircuit benchmark.")
    return circuit_data


def _top_k(values: dict[str, float], top_k: int | None) -> dict[str, float]:
    if top_k is None:
        return dict(sorted(values.items()))
    ranked = sorted(values.items(), key=lambda item: -item[1])
    return dict(ranked[:top_k])
