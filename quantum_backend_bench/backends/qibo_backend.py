"""Qibo local NumPy simulator backend."""

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


class QiboNumpyBackend(BaseBackend):
    """Execute benchmarks with Qibo's bundled NumPy backend."""

    name = "qibo_numpy"

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        try:
            from qibo import Circuit, gates
        except ImportError as exc:
            raise RuntimeError(
                'Qibo is not installed. Install with: pip install "quantum-backend-bench[qibo]"'
            ) from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("Qibo backend requires InternalCircuit benchmark data.")

        metadata = benchmark.metadata or {}
        noise_type = str(metadata.get("noise_type", ""))
        noise_level = float(metadata.get("noise_level", 0.0))
        metadata_noise = noise_level > 0 and noise_type in _SUPPORTED_NOISE_TYPES
        needs_density_matrix = (
            metadata_noise
            or bool(circuit_data.noise)
            or any(operation.gate == "RESET" for operation in circuit_data.operations)
        )
        circuit = Circuit(circuit_data.n_qubits, density_matrix=needs_density_matrix)
        for operation in circuit_data.operations:
            for gate in _qibo_gates(gates, operation):
                circuit.add(gate)
            if metadata_noise and noise_type != "readout_error":
                for qubit in operation.qubits:
                    circuit.add(_qibo_noise_gate(gates, noise_type, qubit, noise_level))

        for instruction in circuit_data.noise:
            for target in instruction.targets:
                circuit.add(
                    _qibo_noise_gate(gates, instruction.channel, target, instruction.probability)
                )

        measurements = circuit_data.measurements or list(range(circuit_data.n_qubits))
        measurement_options: dict[str, float] = {}
        if metadata_noise and noise_type == "readout_error":
            measurement_options = {"p0": noise_level, "p1": noise_level}
        circuit.add(gates.M(*measurements, register_name="m", **measurement_options))
        return circuit

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        try:
            import qibo
        except ImportError as exc:
            raise RuntimeError(
                'Qibo is not installed. Install with: pip install "quantum-backend-bench[qibo]"'
            ) from exc

        circuit = self.build_native_circuit(benchmark)
        backend = qibo.construct_backend("numpy")
        seed = benchmark.parameters.get("seed")
        if seed is not None:
            backend.set_seed(int(seed))

        start = time.perf_counter()
        result = backend.execute_circuit(circuit, nshots=shots)
        runtime = time.perf_counter() - start

        counts = Counter({str(state): int(count) for state, count in result.frequencies().items()})
        metadata = benchmark.metadata or {}
        noise_type = str(metadata.get("noise_type", ""))
        noise_level = float(metadata.get("noise_level", 0.0))
        noise_applied = (noise_level > 0 and noise_type in _SUPPORTED_NOISE_TYPES) or bool(
            _unwrap_noise_benchmark(benchmark).noise
        )
        gate_counts = {str(name): int(count) for name, count in circuit.gate_names.items()}
        return {
            "counts": dict(counts),
            "runtime_seconds": runtime,
            "noise_supported": True,
            "noise_applied": noise_applied,
            "seed_supported": True,
            "seed_applied": seed is not None,
            "compile_seconds": 0.0,
            "compiled_depth": circuit.depth,
            "compiled_gate_count": len(circuit.queue),
            "compiled_two_qubit_gate_count": sum(
                count
                for name, count in gate_counts.items()
                if name in {"cx", "cz", "swap", "cu1", "crx", "cry", "crz"}
            ),
            "compiled_basis_gates": gate_counts,
            "compile_toolchain": "qibo.Circuit with numpy backend",
            "notes": "Qibo execution used the explicitly constructed local NumPy backend.",
        }


_SUPPORTED_NOISE_TYPES = {
    "depolarizing",
    "bit_flip",
    "phase_flip",
    "amplitude_damping",
    "readout_error",
}


def _qibo_gates(gates: Any, operation: CircuitOperation) -> list[Any]:
    gate = operation.gate
    q = operation.qubits
    params = operation.params
    one_qubit = {name: getattr(gates, name) for name in ("H", "X", "Y", "Z", "S", "T", "SX")}
    if gate in one_qubit:
        return [one_qubit[gate](q[0])]
    if gate in {"P", "PHASE"}:
        return [gates.U1(q[0], theta=params["theta"])]
    if gate in {"RX", "RY", "RZ"}:
        return [getattr(gates, gate)(q[0], theta=params["theta"])]
    if gate == "U":
        return [
            gates.U3(
                q[0],
                theta=params["theta"],
                phi=params["phi"],
                lam=params["lambda"],
            )
        ]
    if gate == "CNOT":
        return [gates.CNOT(q[0], q[1])]
    if gate in {"CZ", "SWAP"}:
        return [getattr(gates, gate)(q[0], q[1])]
    if gate == "CCX":
        return [gates.TOFFOLI(q[0], q[1], q[2])]
    if gate in {"CRX", "CRY", "CRZ"}:
        return [getattr(gates, gate)(q[0], q[1], theta=params["theta"])]
    if gate == "CPHASE":
        return [gates.CU1(q[0], q[1], theta=params["theta"])]
    if gate == "RESET":
        return [gates.ResetChannel(q[0], [1.0, 0.0])]
    if gate == "BARRIER":
        return [gates.Align(qubit, delay=0) for qubit in q]
    if gate == "DELAY":
        delay = int(float(params.get("duration", 0)))
        return [gates.Align(qubit, delay=delay) for qubit in q]
    raise ValueError(f"Unsupported Qibo gate: {gate}")


def _qibo_noise_gate(gates: Any, noise_type: str, qubit: int, probability: float) -> Any:
    if noise_type == "depolarizing":
        return gates.DepolarizingChannel(qubit, 4.0 * probability / 3.0)
    if noise_type == "bit_flip":
        return gates.PauliNoiseChannel(qubit, [("X", probability)])
    if noise_type == "phase_flip":
        return gates.PauliNoiseChannel(qubit, [("Z", probability)])
    if noise_type == "amplitude_damping":
        return gates.AmplitudeDampingChannel(qubit, probability)
    if noise_type == "readout_error":
        return gates.ReadoutErrorChannel(
            qubit, [[1.0 - probability, probability], [probability, 1.0 - probability]]
        )
    raise ValueError(f"Unsupported Qibo noise type: {noise_type}")


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)
