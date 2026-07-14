"""Shared benchmark and circuit data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CircuitOperation:
    """Backend-neutral quantum operation."""

    gate: str
    qubits: tuple[int, ...]
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NoiseInstruction:
    """Backend-neutral local noise channel annotation."""

    channel: str
    targets: tuple[int, ...]
    probability: float


@dataclass(slots=True)
class InternalCircuit:
    """Minimal circuit description used by all backends."""

    n_qubits: int
    operations: list[CircuitOperation]
    measurements: list[int] = field(default_factory=list)
    quantum_registers: dict[str, list[int]] = field(default_factory=dict)
    classical_registers: dict[str, list[int]] = field(default_factory=dict)
    measurement_keys: dict[str, str] = field(default_factory=dict)
    bit_order: str = "measurement-list"
    global_phase: float = 0.0
    noise: list[NoiseInstruction] = field(default_factory=list)


@dataclass(slots=True)
class BenchmarkSpec:
    """Description of a benchmark instance."""

    name: str
    n_qubits: int
    parameters: dict[str, Any]
    circuit_data: Any
    ideal_distribution: dict[str, float] | None = None
    metadata: dict[str, Any] | None = None
