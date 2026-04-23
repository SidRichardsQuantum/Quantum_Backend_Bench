"""Cirq execution backend."""

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


class CirqBackend(BaseBackend):
    """Execute benchmarks with cirq.Simulator."""

    name = "cirq"

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        try:
            import cirq
        except ImportError as exc:
            raise RuntimeError("Cirq is not installed.") from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("Cirq backend requires InternalCircuit benchmark data.")

        qubits = cirq.LineQubit.range(circuit_data.n_qubits)
        circuit = cirq.Circuit()
        for operation in circuit_data.operations:
            circuit.append(_to_cirq_operation(cirq, operation, qubits))

        noise_metadata = benchmark.metadata or {}
        noise_applied = False
        if noise_metadata.get("noise_type") == "depolarizing":
            probability = float(noise_metadata.get("noise_level", 0.0))
            if probability > 0:
                circuit = circuit.with_noise(cirq.depolarize(probability))
                noise_applied = True

        if circuit_data.measurements:
            circuit.append(
                cirq.measure(*[qubits[index] for index in circuit_data.measurements], key="m")
            )

        start = time.perf_counter()
        result = cirq.Simulator().run(circuit, repetitions=shots)
        runtime = time.perf_counter() - start

        counts = Counter(
            "".join(str(bit) for bit in row) for row in result.measurements.get("m", [])
        )
        return {
            "counts": dict(counts),
            "runtime_seconds": runtime,
            "noise_supported": True,
            "noise_applied": noise_applied,
        }


def _to_cirq_operation(cirq_module: Any, operation: CircuitOperation, qubits: list[Any]) -> Any:
    gate = operation.gate
    q = [qubits[index] for index in operation.qubits]
    params = operation.params

    if gate == "H":
        return cirq_module.H(q[0])
    if gate == "X":
        return cirq_module.X(q[0])
    if gate == "Y":
        return cirq_module.Y(q[0])
    if gate == "Z":
        return cirq_module.Z(q[0])
    if gate == "S":
        return cirq_module.S(q[0])
    if gate == "T":
        return cirq_module.T(q[0])
    if gate == "RX":
        return cirq_module.rx(params["theta"])(q[0])
    if gate == "RY":
        return cirq_module.ry(params["theta"])(q[0])
    if gate == "RZ":
        return cirq_module.rz(params["theta"])(q[0])
    if gate == "CNOT":
        return cirq_module.CNOT(q[0], q[1])
    if gate == "CZ":
        return cirq_module.CZ(q[0], q[1])
    if gate == "SWAP":
        return cirq_module.SWAP(q[0], q[1])
    if gate == "CPHASE":
        return cirq_module.CZPowGate(exponent=params["theta"] / 3.141592653589793)(q[0], q[1])
    raise ValueError(f"Unsupported Cirq gate: {gate}")


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)
