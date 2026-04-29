"""Backend metadata helpers for diagnostics and result capture."""

from __future__ import annotations

import importlib.metadata
from typing import Any

from quantum_backend_bench.core.discovery import BackendCapability, backend_capabilities

BACKEND_DISTRIBUTIONS: dict[str, tuple[str, ...]] = {
    "braket_local": ("amazon-braket-sdk",),
    "cirq": ("cirq",),
    "cudaq": ("cudaq",),
    "pennylane": ("pennylane",),
    "pyquil_qvm": ("pyquil",),
    "qiskit_aer": ("qiskit", "qiskit-aer"),
    "qutip": ("qutip",),
}


def backend_capability(name: str) -> BackendCapability | None:
    """Return capability metadata for one backend or integration."""

    return next(
        (capability for capability in backend_capabilities() if capability.name == name), None
    )


def backend_runtime_metadata(name: str) -> dict[str, Any]:
    """Return stable backend metadata suitable for embedding in benchmark results."""

    capability = backend_capability(name)
    package_versions = {
        distribution: _distribution_version(distribution)
        for distribution in BACKEND_DISTRIBUTIONS.get(name, ())
    }
    if capability is None:
        return {
            "runtime_includes_transpilation": None,
            "external_process": None,
            "local_only": None,
            "shot_sampling": None,
            "exact_statevector": None,
            "backend_noise_support": None,
            "backend_package_versions": package_versions,
        }
    return {
        "runtime_includes_transpilation": capability.includes_transpilation_time,
        "external_process": capability.external_process,
        "local_only": capability.local_only,
        "shot_sampling": capability.shot_sampling,
        "exact_statevector": capability.exact_statevector,
        "backend_noise_support": capability.noise_support,
        "backend_package_versions": package_versions,
    }


def _distribution_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None
