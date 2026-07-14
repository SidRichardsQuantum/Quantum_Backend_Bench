"""Base types for SDK translation adapters."""

from __future__ import annotations

import ast
from typing import Protocol

from quantum_backend_bench.core.benchmark_spec import InternalCircuit
from quantum_backend_bench.core.circuit_translate import TranslationDiagnostic


class CircuitTranslationAdapter(Protocol):
    """Import, emit, capability, and diagnostic hooks for one circuit SDK."""

    input_format: str
    output_format: str

    def parse_ast(self, tree: ast.AST) -> InternalCircuit:
        """Import a static SDK AST into the neutral circuit representation."""

    def emit(
        self,
        circuit: InternalCircuit,
        *,
        include_runner: bool = False,
        runner_shots: int = 1024,
    ) -> str:
        """Emit SDK source from the neutral circuit representation."""

    def capabilities(self) -> dict[str, object]:
        """Return adapter capability metadata."""

    def diagnostics(self) -> list[TranslationDiagnostic]:
        """Return SDK-specific caveats."""
