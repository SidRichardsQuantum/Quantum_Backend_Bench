"""Amazon Braket LocalSimulator backend."""

from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any

from quantum_backend_bench.backends.base_backend import BaseBackend
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


class BraketLocalBackend(BaseBackend):
    """Execute benchmarks with Braket's LocalSimulator."""

    name = "braket_local"

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba")
        try:
            from braket.circuits import Circuit
        except ImportError as exc:
            raise RuntimeError("Amazon Braket SDK is not installed.") from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("Braket backend requires InternalCircuit benchmark data.")

        circuit = Circuit()
        for operation in circuit_data.operations:
            _apply_braket_op(circuit, operation)
        circuit.probability(target=circuit_data.measurements or list(range(circuit_data.n_qubits)))
        return circuit

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba")
        try:
            from braket.devices import LocalSimulator
        except ImportError as exc:
            raise RuntimeError("Amazon Braket SDK is not installed.") from exc

        circuit = self.build_native_circuit(benchmark)

        start = time.perf_counter()
        task = LocalSimulator().run(circuit, shots=shots)
        result = task.result()
        runtime = time.perf_counter() - start

        counts = dict(Counter(result.measurement_counts))
        metadata = benchmark.metadata or {}
        noise_supported = False
        return {
            "counts": counts,
            "runtime_seconds": runtime,
            "noise_supported": noise_supported,
            "noise_applied": False,
            "notes": (
                "Braket LocalSimulator execution is offline only. Noise injection is not enabled in this adapter."
                if metadata.get("noise_level", 0.0) > 0
                else "Braket LocalSimulator execution completed."
            ),
        }


def _apply_braket_op(circuit: Any, operation: CircuitOperation) -> None:
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
        circuit.rx(q[0], angle=params["theta"])
    elif gate == "RY":
        circuit.ry(q[0], angle=params["theta"])
    elif gate == "RZ":
        circuit.rz(q[0], angle=params["theta"])
    elif gate == "CNOT":
        circuit.cnot(q[0], q[1])
    elif gate == "CZ":
        circuit.cz(q[0], q[1])
    elif gate == "SWAP":
        circuit.swap(q[0], q[1])
    elif gate == "CPHASE":
        circuit.cphaseshift(q[0], q[1], angle=params["theta"])
    else:
        raise ValueError(f"Unsupported Braket gate: {gate}")


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)
