"""Qiskit Aer local simulator backend."""

from __future__ import annotations

import time
from collections import Counter
from typing import Any

from quantum_backend_bench.backends.base_backend import BaseBackend
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


class QiskitAerBackend(BaseBackend):
    """Execute benchmarks with Qiskit AerSimulator."""

    name = "qiskit_aer"

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        try:
            from qiskit import QuantumCircuit
        except ImportError as exc:
            raise RuntimeError(
                'Qiskit is not installed. Install with: pip install "quantum-backend-bench[qiskit]"'
            ) from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("Qiskit backend requires InternalCircuit benchmark data.")

        measurements = circuit_data.measurements or list(range(circuit_data.n_qubits))
        circuit = QuantumCircuit(circuit_data.n_qubits, len(measurements))
        for operation in circuit_data.operations:
            _apply_qiskit_op(circuit, operation)
        for classical_index, qubit in enumerate(measurements):
            circuit.measure(qubit, len(measurements) - classical_index - 1)
        return circuit

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        try:
            from qiskit import transpile
            from qiskit_aer import AerSimulator
        except ImportError as exc:
            raise RuntimeError(
                'Qiskit Aer is not installed. Install with: pip install "quantum-backend-bench[qiskit]"'
            ) from exc

        circuit = self.build_native_circuit(benchmark)
        seed = benchmark.parameters.get("seed")
        metadata = benchmark.metadata or {}
        noise_model = _qiskit_noise_model(metadata)
        simulator_kwargs = {}
        if seed is not None:
            simulator_kwargs["seed_simulator"] = seed
        if noise_model is not None:
            simulator_kwargs["noise_model"] = noise_model
        simulator = AerSimulator(**simulator_kwargs)

        start = time.perf_counter()
        compiled = (
            transpile(circuit, simulator, seed_transpiler=seed)
            if seed is not None
            else transpile(circuit, simulator)
        )
        result = simulator.run(compiled, shots=shots).result()
        runtime = time.perf_counter() - start

        noise_applied = noise_model is not None
        return {
            "counts": dict(Counter(result.get_counts(compiled))),
            "runtime_seconds": runtime,
            "noise_supported": True,
            "noise_applied": noise_applied,
            "seed_supported": True,
            "seed_applied": seed is not None,
            "notes": (
                "Qiskit Aer execution completed with depolarizing noise."
                if noise_applied
                else "Qiskit Aer execution completed."
            ),
        }


def _apply_qiskit_op(circuit: Any, operation: CircuitOperation) -> None:
    gate = operation.gate
    q = operation.qubits
    params = operation.params

    if gate == "H":
        circuit.h(q[0])
    elif gate == "X":
        circuit.x(q[0])
    elif gate == "Y":
        circuit.y(q[0])
    elif gate == "Z":
        circuit.z(q[0])
    elif gate == "S":
        circuit.s(q[0])
    elif gate == "T":
        circuit.t(q[0])
    elif gate == "RX":
        circuit.rx(params["theta"], q[0])
    elif gate == "RY":
        circuit.ry(params["theta"], q[0])
    elif gate == "RZ":
        circuit.rz(params["theta"], q[0])
    elif gate == "CNOT":
        circuit.cx(q[0], q[1])
    elif gate == "CZ":
        circuit.cz(q[0], q[1])
    elif gate == "SWAP":
        circuit.swap(q[0], q[1])
    elif gate == "CPHASE":
        circuit.cp(params["theta"], q[0], q[1])
    else:
        raise ValueError(f"Unsupported Qiskit gate: {gate}")


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)


def _qiskit_noise_model(metadata: dict[str, Any]) -> Any | None:
    if metadata.get("noise_type") != "depolarizing":
        return None
    probability = float(metadata.get("noise_level", 0.0))
    if probability <= 0:
        return None
    try:
        from qiskit_aer.noise import NoiseModel, depolarizing_error
    except ImportError as exc:
        raise RuntimeError(
            'Qiskit Aer noise support requires qiskit-aer. Install with: pip install "quantum-backend-bench[qiskit]"'
        ) from exc

    noise_model = NoiseModel()
    one_qubit_error = depolarizing_error(probability, 1)
    two_qubit_error = depolarizing_error(probability, 2)
    noise_model.add_all_qubit_quantum_error(
        one_qubit_error, ["h", "x", "y", "z", "s", "t", "rx", "ry", "rz"]
    )
    noise_model.add_all_qubit_quantum_error(two_qubit_error, ["cx", "cz", "swap", "cp"])
    return noise_model
