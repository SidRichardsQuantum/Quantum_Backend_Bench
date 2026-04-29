"""Packaging metadata tests."""

from __future__ import annotations

import tomllib
from pathlib import Path

REQUIRED_SDIST_DOCS = {
    "README.md",
    "THEORY.md",
    "METHODOLOGY.md",
    "SCHEMA.md",
    "LIMITATIONS.md",
    "USAGE.md",
    "PROBLEM.md",
}


def test_backend_dependencies_are_optional_extras() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    extras = project["optional-dependencies"]

    assert "dependencies" not in project
    assert extras["cirq"] == ["cirq"]
    assert extras["pennylane"] == ["pennylane"]
    assert extras["braket"] == ["amazon-braket-sdk"]
    assert extras["qiskit"] == ["qiskit", "qiskit-aer"]
    assert extras["cudaq"] == ["cudaq"]
    assert extras["pyquil"] == ["pyquil"]
    assert extras["qutip"] == ["qutip"]
    assert extras["qbraid"] == ["qbraid"]
    assert extras["qsharp"] == ["qsharp"]
    assert extras["yaml"] == ["PyYAML"]
    assert "cirq" in extras["all"]
    assert "qbraid" in extras["all"]
    assert "qiskit-aer" in extras["all"]
    assert "pytket" in extras["all"]
    assert "PyYAML" in extras["all"]
    assert "cudaq" not in extras["all"]
    assert "pyquil" not in extras["all"]
    assert "cudaq" in extras["full"]
    assert "pyquil" in extras["full"]


def test_required_docs_are_included_in_sdist_manifest() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")
    for document in REQUIRED_SDIST_DOCS:
        assert f"include {document}" in manifest
