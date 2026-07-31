"""Shared helpers for repository examples."""

from __future__ import annotations

from collections.abc import Iterable

from quantum_backend_bench import backend_capabilities

DEFAULT_BACKEND_ORDER = ("cirq", "pennylane", "qiskit_aer", "braket_local")
NOISE_BACKEND_ORDER = ("cirq", "pennylane", "qiskit_aer")


def installed_local_backends(
    preferred: Iterable[str] = DEFAULT_BACKEND_ORDER,
    *,
    limit: int | None = None,
    fallback: tuple[str, ...] = ("cirq",),
) -> list[str]:
    """Return installed local execution backends in a stable example-friendly order."""

    capabilities = {capability.name: capability for capability in backend_capabilities()}
    selected = [
        name
        for name in preferred
        if (capability := capabilities.get(name)) is not None
        and capability.role == "execution"
        and capability.installed
        and capability.local_only
        and not capability.external_process
    ]
    if not selected:
        selected = list(fallback)
    return selected[:limit] if limit is not None else selected


def installed_noise_backends(*, limit: int | None = None) -> list[str]:
    """Return installed local backends that receive project-injected noise models."""

    capabilities = {capability.name: capability for capability in backend_capabilities()}
    selected = [
        name
        for name in NOISE_BACKEND_ORDER
        if (capability := capabilities.get(name)) is not None
        and capability.installed
        and capability.local_only
        and capability.noise_support != "not injected"
    ]
    if not selected:
        selected = ["cirq"]
    return selected[:limit] if limit is not None else selected


def installed_draw_backends() -> list[str]:
    """Return available drawing targets used by circuit diagram examples."""

    capabilities = {capability.name: capability for capability in backend_capabilities()}
    backends = []
    if capabilities.get("cirq") and capabilities["cirq"].installed:
        backends.append("cirq")
    if capabilities.get("pytket") and capabilities["pytket"].installed:
        backends.append("tket")
    if capabilities.get("pennylane") and capabilities["pennylane"].installed:
        backends.append("pennylane")
    return backends or ["cirq"]
