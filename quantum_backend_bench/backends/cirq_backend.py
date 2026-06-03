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

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        try:
            import cirq
        except ImportError as exc:
            raise RuntimeError(
                'Cirq is not installed. Install with: pip install "quantum-backend-bench[cirq]"'
            ) from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("Cirq backend requires InternalCircuit benchmark data.")

        qubits = cirq.LineQubit.range(circuit_data.n_qubits)
        circuit = cirq.Circuit()
        for operation in circuit_data.operations:
            circuit.append(_to_cirq_operation(cirq, operation, qubits))

        noise_metadata = benchmark.metadata or {}
        probability = float(noise_metadata.get("noise_level", 0.0))
        noise_type = noise_metadata.get("noise_type")
        if probability > 0:
            noise = _cirq_noise(cirq, str(noise_type), probability)
            if noise is not None:
                circuit = circuit.with_noise(noise)

        if circuit_data.measurements:
            circuit.append(
                cirq.measure(*[qubits[index] for index in circuit_data.measurements], key="m")
            )

        return circuit

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        circuit = self.build_native_circuit(benchmark)
        import cirq

        noise_metadata = benchmark.metadata or {}
        noise_applied = (
            _cirq_noise(
                cirq,
                str(noise_metadata.get("noise_type")),
                float(noise_metadata.get("noise_level", 0.0)),
            )
            is not None
        )

        start = time.perf_counter()
        seed = benchmark.parameters.get("seed")
        simulator = cirq.Simulator(seed=seed) if seed is not None else cirq.Simulator()
        result = simulator.run(circuit, repetitions=shots)
        runtime = time.perf_counter() - start

        counts = Counter(
            "".join(str(bit) for bit in row) for row in result.measurements.get("m", [])
        )
        return {
            "counts": dict(counts),
            "runtime_seconds": runtime,
            "noise_supported": True,
            "noise_applied": noise_applied,
            "seed_supported": True,
            "seed_applied": seed is not None,
            "compile_seconds": 0.0,
            "compiled_depth": len(circuit),
            "compiled_gate_count": sum(1 for _ in circuit.all_operations()),
            "compiled_two_qubit_gate_count": sum(
                1 for operation in circuit.all_operations() if len(operation.qubits) == 2
            ),
            "compiled_basis_gates": _cirq_gate_counts(circuit),
            "compile_toolchain": "cirq.Circuit",
        }


def _cirq_gate_counts(circuit: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for operation in circuit.all_operations():
        name = str(operation.gate).split("(", 1)[0]
        counts[name] = counts.get(name, 0) + 1
    return counts


def _cirq_noise(cirq_module: Any, noise_type: str, probability: float) -> Any | None:
    if probability <= 0:
        return None
    if noise_type == "depolarizing":
        return cirq_module.depolarize(probability)
    if noise_type in {"bit_flip", "readout_error"}:
        return cirq_module.bit_flip(probability)
    if noise_type == "phase_flip":
        return cirq_module.phase_flip(probability)
    if noise_type == "amplitude_damping":
        return cirq_module.amplitude_damp(probability)
    return None


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
