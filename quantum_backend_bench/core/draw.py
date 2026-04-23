"""Circuit drawing helpers."""

from __future__ import annotations

from quantum_backend_bench.backends import get_backend
from quantum_backend_bench.backends.tket_analysis import draw_tket
from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec


def draw_benchmark(
    benchmark: BenchmarkSpec,
    backend: str,
    save_path: str | None = None,
) -> str:
    """Render a benchmark circuit using a backend-native drawer."""

    if backend == "tket":
        return draw_tket(benchmark, save_path=save_path)
    return get_backend(backend).draw(benchmark, save_path=save_path)
