"""Rigetti pyQuil QVM backend."""

from __future__ import annotations

import math
import time
from collections import Counter
from typing import Any

from quantum_backend_bench.backends.base_backend import BaseBackend
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


class PyQuilQVMBackend(BaseBackend):
    """Execute benchmarks with pyQuil and a local QVM/quilc runtime."""

    name = "pyquil_qvm"

    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        try:
            from pyquil import Program
            from pyquil.quilbase import Declare
        except ImportError as exc:
            raise RuntimeError(
                'pyQuil is not installed. Install with: pip install "quantum-backend-bench[pyquil]"'
            ) from exc

        circuit_data = _unwrap_noise_benchmark(benchmark)
        if not isinstance(circuit_data, InternalCircuit):
            raise TypeError("pyQuil backend requires InternalCircuit benchmark data.")

        measurements = circuit_data.measurements or list(range(circuit_data.n_qubits))
        program = Program(Declare("ro", "BIT", len(measurements)))
        for operation in circuit_data.operations:
            _apply_pyquil_op(program, operation)
        for classical_index, qubit in enumerate(measurements):
            _apply_measure(program, qubit, classical_index)
        return program

    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        try:
            from pyquil import get_qc
            from pyquil.api import local_forest_runtime
        except ImportError as exc:
            raise RuntimeError(
                'pyQuil is not installed. Install with: pip install "quantum-backend-bench[pyquil]"'
            ) from exc

        program = self.build_native_circuit(benchmark).wrap_in_numshots_loop(shots)
        metadata = benchmark.metadata or {}

        try:
            start = time.perf_counter()
            with local_forest_runtime():
                qc = get_qc(f"{benchmark.n_qubits}q-qvm")
                result = qc.run(qc.compile(program))
            runtime = time.perf_counter() - start
        except Exception as exc:
            raise RuntimeError(
                "pyQuil QVM execution requires local Forest runtime support "
                "with qvm and quilc available."
            ) from exc

        readout = result.get_register_map()["ro"]
        counts = Counter("".join(str(int(bit)) for bit in row) for row in readout)
        return {
            "counts": dict(counts),
            "runtime_seconds": runtime,
            "noise_supported": False,
            "noise_applied": False,
            "notes": (
                "pyQuil QVM execution completed without noise injection in this adapter."
                if metadata.get("noise_level", 0.0) > 0
                else "pyQuil QVM execution completed."
            ),
        }


def _apply_pyquil_op(program: Any, operation: CircuitOperation) -> None:
    from pyquil import gates

    gate = operation.gate
    q = operation.qubits
    params = operation.params

    if gate == "H":
        program += gates.H(q[0])
    elif gate == "X":
        program += gates.X(q[0])
    elif gate == "Y":
        program += gates.Y(q[0])
    elif gate == "Z":
        program += gates.Z(q[0])
    elif gate == "S":
        program += gates.PHASE(math.pi / 2, q[0])
    elif gate == "T":
        program += gates.PHASE(math.pi / 4, q[0])
    elif gate == "RX":
        program += gates.RX(params["theta"], q[0])
    elif gate == "RY":
        program += gates.RY(params["theta"], q[0])
    elif gate == "RZ":
        program += gates.RZ(params["theta"], q[0])
    elif gate == "CNOT":
        program += gates.CNOT(q[0], q[1])
    elif gate == "CZ":
        program += gates.CZ(q[0], q[1])
    elif gate == "SWAP":
        program += gates.SWAP(q[0], q[1])
    elif gate == "CPHASE":
        program += gates.CPHASE(params["theta"], q[0], q[1])
    else:
        raise ValueError(f"Unsupported pyQuil gate: {gate}")


def _apply_measure(program: Any, qubit: int, classical_index: int) -> None:
    from pyquil import gates

    program += gates.MEASURE(qubit, ("ro", classical_index))


def _unwrap_noise_benchmark(benchmark: BenchmarkSpec) -> Any:
    return (benchmark.metadata or {}).get("base_circuit", benchmark.circuit_data)
