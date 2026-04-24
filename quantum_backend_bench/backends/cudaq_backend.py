"""NVIDIA CUDA-Q local simulator backend."""

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


class CudaQBackend(BaseBackend):
    """Execute benchmarks with CUDA-Q's local simulator target."""

    name = "cudaq"

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        try:
            import cudaq
        except ImportError as exc:
            raise RuntimeError(
                'CUDA-Q is not installed. Install with: pip install "quantum-backend-bench[cudaq]"'
            ) from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("CUDA-Q backend requires InternalCircuit benchmark data.")

        kernel = cudaq.make_kernel()
        qubits = kernel.qalloc(circuit_data.n_qubits)
        for operation in circuit_data.operations:
            _apply_cudaq_op(kernel, qubits, operation)
        for qubit in circuit_data.measurements or list(range(circuit_data.n_qubits)):
            kernel.mz(qubits[qubit])
        return kernel

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        try:
            import cudaq
        except ImportError as exc:
            raise RuntimeError(
                'CUDA-Q is not installed. Install with: pip install "quantum-backend-bench[cudaq]"'
            ) from exc

        kernel = self.build_native_circuit(benchmark)
        metadata = benchmark.metadata or {}

        start = time.perf_counter()
        result = cudaq.sample(kernel, shots_count=shots)
        runtime = time.perf_counter() - start

        return {
            "counts": _cudaq_counts(result),
            "runtime_seconds": runtime,
            "noise_supported": False,
            "noise_applied": False,
            "notes": (
                "CUDA-Q execution completed without noise injection in this adapter."
                if metadata.get("noise_level", 0.0) > 0
                else "CUDA-Q execution completed."
            ),
        }


def _apply_cudaq_op(kernel: Any, qubits: Any, operation: CircuitOperation) -> None:
    gate = operation.gate
    q = operation.qubits
    params = operation.params

    if gate == "H":
        kernel.h(qubits[q[0]])
    elif gate == "X":
        kernel.x(qubits[q[0]])
    elif gate == "Y":
        kernel.y(qubits[q[0]])
    elif gate == "Z":
        kernel.z(qubits[q[0]])
    elif gate == "S":
        kernel.s(qubits[q[0]])
    elif gate == "T":
        kernel.t(qubits[q[0]])
    elif gate == "RX":
        kernel.rx(params["theta"], qubits[q[0]])
    elif gate == "RY":
        kernel.ry(params["theta"], qubits[q[0]])
    elif gate == "RZ":
        kernel.rz(params["theta"], qubits[q[0]])
    elif gate == "CNOT":
        _call_first(kernel, ("cx", "cnot"), qubits[q[0]], qubits[q[1]])
    elif gate == "CZ":
        _call_first(kernel, ("cz",), qubits[q[0]], qubits[q[1]])
    elif gate == "SWAP":
        _call_first(kernel, ("swap",), qubits[q[0]], qubits[q[1]])
    elif gate == "CPHASE":
        _call_first(kernel, ("cr1", "cphase"), params["theta"], qubits[q[0]], qubits[q[1]])
    else:
        raise ValueError(f"Unsupported CUDA-Q gate: {gate}")


def _call_first(target: Any, names: tuple[str, ...], *args: Any) -> None:
    for name in names:
        method = getattr(target, name, None)
        if method is not None:
            method(*args)
            return
    available = ", ".join(names)
    raise ValueError(f"CUDA-Q kernel does not expose any of: {available}")


def _cudaq_counts(result: Any) -> dict[str, int]:
    if hasattr(result, "items"):
        return {str(state): int(count) for state, count in result.items()}
    if hasattr(result, "to_dict"):
        return {str(state): int(count) for state, count in result.to_dict().items()}
    return dict(Counter(str(state) for state in result))


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)
