"""Abstract backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from quantum_backend_bench.backends.tket_analysis import analyze_with_tket
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec


class BaseBackend(ABC):
    """Base class for all execution backends."""

    name: str

    @abstractmethod
    def run(self, benchmark: BenchmarkSpec, shots: int = 1024) -> dict[str, Any]:
        """Execute a benchmark and return counts plus runtime metadata."""

    @abstractmethod
    def build_native_circuit(self, benchmark: BenchmarkSpec) -> Any:
        """Build the backend's native circuit object."""

    def draw(self, benchmark: BenchmarkSpec, save_path: str | None = None) -> str:
        """Render a textual circuit diagram and optionally save it."""

        diagram = str(self.build_native_circuit(benchmark))
        if save_path is not None:
            destination = Path(save_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(diagram + "\n", encoding="utf-8")
        return diagram

    def structural_metrics(self, benchmark: BenchmarkSpec) -> dict[str, Any]:
        """Return structure-only metrics using pytket analysis."""

        return analyze_with_tket(benchmark)
