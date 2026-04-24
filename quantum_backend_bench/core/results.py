"""Result dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class BenchmarkResult:
    """Standardized output for a benchmark execution."""

    benchmark: str
    backend: str
    n_qubits: int
    shots: int
    parameters: dict[str, Any]
    repeats: int = 1
    total_shots: int | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""

        return asdict(self)
