"""Abstract backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from quantum_backend_bench.backends.tket_analysis import analyze_with_tket
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec


class BaseBackend(ABC):
    """Base class for all execution backends."""

    name: str

    @abstractmethod
    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        """Execute a benchmark and return counts plus runtime metadata."""

    def structural_metrics(self, benchmark: BenchmarkSpec) -> dict[str, Any]:
        """Return structure-only metrics using pytket analysis."""

        return analyze_with_tket(benchmark)
