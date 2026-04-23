"""Core benchmarking abstractions."""

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)
from quantum_backend_bench.core.runner import run_benchmark

__all__ = ["BenchmarkSpec", "CircuitOperation", "InternalCircuit", "run_benchmark"]
