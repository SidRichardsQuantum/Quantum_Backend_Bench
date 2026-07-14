"""Compatibility matrix helpers."""

from __future__ import annotations

import platform
import sys
from typing import Any

from quantum_backend_bench.core.discovery import BackendCapability, backend_capabilities

SUPPORTED_PYTHON = {(3, 11), (3, 12)}
TESTED_VERSION_BANDS = {
    "amazon-braket-sdk": ">=1.85,<2",
    "cirq": ">=1.4,<2",
    "cudaq": ">=0.8,<1",
    "pennylane": ">=0.38,<1",
    "pyquil": ">=4,<5",
    "pytket": ">=1.30,<3",
    "qbraid": ">=0.9,<1",
    "qiskit": ">=1,<3",
    "qiskit-aer": ">=0.15,<1",
    "qsharp": ">=1,<2",
    "qutip": ">=5,<6",
}
_INTEGRATION_TESTED_PACKAGES = {
    "braket_local": ("amazon-braket-sdk",),
    "cirq": ("cirq",),
    "cudaq": ("cudaq",),
    "pennylane": ("pennylane",),
    "pyquil_qvm": ("pyquil",),
    "pytket": ("pytket",),
    "qbraid": ("qbraid",),
    "qiskit_aer": ("qiskit", "qiskit-aer"),
    "qsharp": ("qsharp",),
    "qutip": ("qutip",),
}


def compatibility_rows() -> list[dict[str, Any]]:
    """Return compatibility rows for known integrations."""

    rows = [_row_from_capability(capability) for capability in backend_capabilities()]
    rows.append(
        {
            "name": "notebooks",
            "role": "tutorials",
            "installed": _module_installed("ipykernel") and _module_installed("pandas"),
            "install_extra": "notebooks",
            "account_required": "no",
            "local_runtime": "Python packages only",
            "ci_coverage": "not executed in CI",
            "notes": "Optional helpers for running tutorial notebooks.",
            "tested_versions": "ipykernel/pandas from docs and notebook extras under CI constraints",
        }
    )
    return rows


def python_compatibility() -> dict[str, Any]:
    """Return current Python compatibility metadata."""

    version = sys.version_info
    supported = (version.major, version.minor) in SUPPORTED_PYTHON
    return {
        "version": platform.python_version(),
        "supported": supported,
        "supported_versions": ["3.11", "3.12"],
        "message": "supported" if supported else "not part of the current supported matrix",
    }


def format_compatibility_report(rows: list[dict[str, Any]] | None = None) -> str:
    """Format compatibility rows as a human-readable CLI report."""

    rows = rows or compatibility_rows()
    python = python_compatibility()
    lines = [
        "Compatibility",
        f"Python: {python['version']} ({python['message']}; supported: {', '.join(python['supported_versions'])})",
        "",
        "name          role             installed  extra       account/status         local/runtime              CI coverage",
    ]
    for row in rows:
        installed = "yes" if row["installed"] else "no"
        lines.append(
            f"{row['name']:<13} {row['role']:<16} {installed:<10} "
            f"{row['install_extra']:<11} {row['account_required']:<22} "
            f"{row['local_runtime']:<26} {row['ci_coverage']}"
        )
        if row.get("tested_versions"):
            lines.append(f"  tested versions: {row['tested_versions']}")
        if row.get("notes"):
            lines.append(f"  notes: {row['notes']}")
    return "\n".join(lines)


def _row_from_capability(capability: BackendCapability) -> dict[str, Any]:
    return {
        "name": capability.name,
        "role": capability.role,
        "installed": capability.installed,
        "install_extra": capability.install_extra,
        "account_required": "no" if capability.local_only else "not for core workflow",
        "local_runtime": _local_runtime(capability),
        "ci_coverage": _ci_coverage(capability),
        "tested_versions": _tested_versions(capability.name),
        "notes": capability.notes,
    }


def _local_runtime(capability: BackendCapability) -> str:
    if capability.name == "pyquil_qvm":
        return "Python plus qvm/quilc"
    if capability.external_process:
        return "external local process"
    return "Python packages only"


def _tested_versions(name: str) -> str:
    packages = _INTEGRATION_TESTED_PACKAGES.get(name, ())
    return ", ".join(
        f"{package}{TESTED_VERSION_BANDS[package]}"
        for package in packages
        if package in TESTED_VERSION_BANDS
    )


def _ci_coverage(capability: BackendCapability) -> str:
    if capability.name == "cirq":
        return "main CI"
    if capability.name == "pytket":
        return "main CI install"
    if capability.name in {"pennylane", "braket_local", "qiskit_aer", "qutip"}:
        return "optional smoke"
    if capability.name == "cudaq":
        return "experimental optional smoke"
    if capability.name == "pyquil_qvm":
        return "optional smoke when runtime exists"
    return "dependency metadata only"


def _module_installed(module_name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(module_name) is not None
