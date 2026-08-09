"""SDK adapter registry for neutral translation helpers."""

from __future__ import annotations

from quantum_backend_bench.core.translation_adapters.base import CircuitTranslationAdapter
from quantum_backend_bench.core.translation_adapters.braket import BraketCircuitAdapter
from quantum_backend_bench.core.translation_adapters.cirq import CirqCircuitAdapter
from quantum_backend_bench.core.translation_adapters.pennylane import PennyLaneCircuitAdapter
from quantum_backend_bench.core.translation_adapters.qibo import QiboCircuitAdapter
from quantum_backend_bench.core.translation_adapters.qiskit import QiskitCircuitAdapter

_CIRCUIT_ADAPTERS: dict[str, CircuitTranslationAdapter] = {
    adapter.output_format: adapter
    for adapter in (
        BraketCircuitAdapter(),
        CirqCircuitAdapter(),
        PennyLaneCircuitAdapter(),
        QiboCircuitAdapter(),
        QiskitCircuitAdapter(),
    )
}
_CIRCUIT_INPUT_ADAPTERS: dict[str, CircuitTranslationAdapter] = {
    adapter.input_format: adapter for adapter in _CIRCUIT_ADAPTERS.values()
}


def circuit_adapter_for_input(input_format: str) -> CircuitTranslationAdapter:
    """Return the adapter that imports a supported SDK circuit format."""

    return _CIRCUIT_INPUT_ADAPTERS[input_format]


def circuit_adapter_for_output(output_format: str) -> CircuitTranslationAdapter:
    """Return the adapter that emits a supported SDK circuit format."""

    return _CIRCUIT_ADAPTERS[output_format]


def circuit_adapter_output_formats() -> tuple[str, ...]:
    """Return supported SDK circuit output formats."""

    return tuple(sorted(_CIRCUIT_ADAPTERS))


def circuit_adapter_input_formats() -> tuple[str, ...]:
    """Return supported SDK circuit input formats."""

    return tuple(sorted(_CIRCUIT_INPUT_ADAPTERS))


def circuit_adapter_capabilities() -> list[dict[str, object]]:
    """Return per-SDK circuit adapter capabilities."""

    return [adapter.capabilities() for adapter in _CIRCUIT_ADAPTERS.values()]


def circuit_adapter_diagnostics() -> list[object]:
    """Return SDK-specific circuit adapter diagnostics."""

    diagnostics: list[object] = []
    for adapter in _CIRCUIT_ADAPTERS.values():
        diagnostics.extend(adapter.diagnostics())
    return diagnostics
