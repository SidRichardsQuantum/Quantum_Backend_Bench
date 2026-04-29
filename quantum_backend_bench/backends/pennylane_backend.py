"""PennyLane execution backend."""

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


class PennyLaneBackend(BaseBackend):
    """Execute benchmarks with PennyLane local simulators."""

    name = "pennylane"

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        try:
            import pennylane as qml
        except ImportError as exc:
            raise RuntimeError(
                'PennyLane is not installed. Install with: pip install "quantum-backend-bench[pennylane]"'
            ) from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("PennyLane backend requires InternalCircuit benchmark data.")

        metadata = benchmark.metadata or {}
        noise_level = float(metadata.get("noise_level", 0.0))
        use_mixed = metadata.get("noise_type") == "depolarizing" and noise_level > 0
        device_name = "default.mixed" if use_mixed else "default.qubit"
        seed = benchmark.parameters.get("seed")
        dev, seed_applied = _make_device(qml, device_name, wires=circuit_data.n_qubits, seed=seed)

        @qml.qnode(dev)
        def circuit() -> Any:
            for operation in circuit_data.operations:
                _apply_pennylane_op(qml, operation, noise_level=noise_level if use_mixed else 0.0)
            return qml.sample(wires=circuit_data.measurements or list(range(circuit_data.n_qubits)))

        try:
            circuit._qbb_seed_applied = seed_applied  # type: ignore[attr-defined]
        except AttributeError:
            pass
        return circuit

    def draw(self, benchmark: BenchmarkSpec, save_path: str | None = None) -> str:
        import pennylane as qml

        circuit = self.build_native_circuit(benchmark)
        diagram = qml.draw(circuit)()
        if save_path is not None:
            figure, _ = qml.draw_mpl(circuit)()
            figure.savefig(save_path, dpi=150, bbox_inches="tight")
        return diagram

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        import pennylane as qml

        circuit = self.build_native_circuit(benchmark)
        metadata = benchmark.metadata or {}
        noise_level = float(metadata.get("noise_level", 0.0))
        use_mixed = metadata.get("noise_type") == "depolarizing" and noise_level > 0

        start = time.perf_counter()
        sampled_circuit = qml.set_shots(circuit, shots=shots)
        samples = sampled_circuit()
        runtime = time.perf_counter() - start

        if getattr(samples, "ndim", 1) == 1:
            samples = samples.reshape(-1, 1)
        counts = Counter("".join(str(int(bit)) for bit in row) for row in samples)
        return {
            "counts": dict(counts),
            "runtime_seconds": runtime,
            "noise_supported": True,
            "noise_applied": use_mixed,
            "seed_supported": True,
            "seed_applied": bool(getattr(circuit, "_qbb_seed_applied", False)),
        }


def _apply_pennylane_op(qml: Any, operation: CircuitOperation, noise_level: float = 0.0) -> None:
    gate = operation.gate
    q = list(operation.qubits)
    params = operation.params

    if gate == "H":
        qml.Hadamard(wires=q[0])
    elif gate == "X":
        qml.PauliX(wires=q[0])
    elif gate == "Y":
        qml.PauliY(wires=q[0])
    elif gate == "Z":
        qml.PauliZ(wires=q[0])
    elif gate == "S":
        qml.S(wires=q[0])
    elif gate == "T":
        qml.T(wires=q[0])
    elif gate == "RX":
        qml.RX(params["theta"], wires=q[0])
    elif gate == "RY":
        qml.RY(params["theta"], wires=q[0])
    elif gate == "RZ":
        qml.RZ(params["theta"], wires=q[0])
    elif gate == "CNOT":
        qml.CNOT(wires=q)
    elif gate == "CZ":
        qml.CZ(wires=q)
    elif gate == "SWAP":
        qml.SWAP(wires=q)
    elif gate == "CPHASE":
        qml.ControlledPhaseShift(params["theta"], wires=q)
    else:
        raise ValueError(f"Unsupported PennyLane gate: {gate}")

    if noise_level > 0:
        for wire in q:
            qml.DepolarizingChannel(noise_level, wires=wire)


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)


def _make_device(qml: Any, device_name: str, wires: int, seed: object | None) -> tuple[Any, bool]:
    if seed is None:
        return qml.device(device_name, wires=wires), False
    try:
        return qml.device(device_name, wires=wires, seed=int(seed)), True
    except TypeError:
        return qml.device(device_name, wires=wires), False
