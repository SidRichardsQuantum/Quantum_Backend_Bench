"""Runtime environment capture for reproducible benchmark results."""

from __future__ import annotations

import importlib.metadata
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PACKAGE_NAMES = {
    "amazon-braket-sdk": "amazon-braket-sdk",
    "cirq": "cirq",
    "cudaq": "cudaq",
    "matplotlib": "matplotlib",
    "numpy": "numpy",
    "pennylane": "pennylane",
    "pyquil": "pyquil",
    "pytket": "pytket",
    "qbraid": "qbraid",
    "qiskit": "qiskit",
    "qiskit-aer": "qiskit-aer",
    "qsharp": "qsharp",
    "qutip": "qutip",
}


def capture_environment(cwd: str | Path | None = None) -> dict[str, Any]:
    """Capture package, platform, Python, and git metadata."""

    root = Path(cwd or os.getcwd())
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "packages": _package_versions(),
        "git": _git_metadata(root),
    }


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for label, distribution in PACKAGE_NAMES.items():
        try:
            versions[label] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[label] = None
    return versions


def _git_metadata(cwd: Path) -> dict[str, Any]:
    commit = _run_git(["git", "rev-parse", "HEAD"], cwd)
    branch = _run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    dirty = _run_git(["git", "status", "--porcelain"], cwd)
    return {
        "commit": commit,
        "branch": branch,
        "dirty": bool(dirty),
    }


def _run_git(command: list[str], cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    output = completed.stdout.strip()
    return output or None
