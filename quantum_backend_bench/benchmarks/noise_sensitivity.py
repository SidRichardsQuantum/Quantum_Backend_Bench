"""Noise sensitivity benchmark wrapper."""

from __future__ import annotations

from typing import Iterable

from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec


def build_benchmark(
    base_benchmark: BenchmarkSpec,
    noise_type: str = "depolarizing",
    noise_levels: Iterable[float] = (0.0, 0.001, 0.005, 0.01, 0.02),
) -> list[BenchmarkSpec]:
    """Build a family of noisy benchmarks from a base benchmark."""

    wrapped: list[BenchmarkSpec] = []
    base_metadata = dict(base_benchmark.metadata or {})
    for noise_level in noise_levels:
        metadata = {
            **base_metadata,
            "base_circuit": base_benchmark.circuit_data,
            "noise_type": noise_type,
            "noise_level": float(noise_level),
        }
        wrapped.append(
            BenchmarkSpec(
                name=f"{base_benchmark.name}_noise",
                n_qubits=base_benchmark.n_qubits,
                parameters={
                    **base_benchmark.parameters,
                    "noise_type": noise_type,
                    "noise_level": float(noise_level),
                },
                circuit_data=base_benchmark.circuit_data,
                ideal_distribution=base_benchmark.ideal_distribution,
                metadata=metadata,
            )
        )
    return wrapped
