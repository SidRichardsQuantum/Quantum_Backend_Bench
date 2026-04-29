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
        simulator = AerSimulator(seed_simulator=seed) if seed is not None else AerSimulator()

        start = time.perf_counter()
        compiled = (
            transpile(circuit, simulator, seed_transpiler=seed)
            if seed is not None
            else transpile(circuit, simulator)
        )
        result = simulator.run(compiled, shots=shots).result()
        runtime = time.perf_counter() - start

        metadata = benchmark.metadata or {}
        return {
            "counts": dict(Counter(result.get_counts(compiled))),
            "runtime_seconds": runtime,
            "noise_supported": False,
            "noise_applied": False,
            "seed_supported": True,
            "seed_applied": seed is not None,
            "notes": (
                "Qiskit Aer execution completed without noise injection in this adapter."
                if metadata.get("noise_level", 0.0) > 0
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
