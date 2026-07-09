"""Packaging metadata tests."""

from __future__ import annotations

import json
import py_compile
import tomllib
from pathlib import Path

REQUIRED_SDIST_DOCS = {
    "README.md",
    "ROADMAP.md",
    "docs/RESULTS.md",
    "docs/SDK_AUDITS.md",
    "docs/THEORY.md",
    "docs/METHODOLOGY.md",
    "docs/SCHEMA.md",
    "docs/LIMITATIONS.md",
    "USAGE.md",
    "docs/PROBLEM.md",
    "docs/COMPATIBILITY.md",
    "docs/CIRCUIT_TRANSLATION.md",
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
    assert "cirq" in extras["dev"]
    assert "pandas" in extras["dev"]
    assert extras["docs"] == ["markdown", "matplotlib", "pymdown-extensions"]
    assert extras["pyquil"] == ["pyquil"]
    assert extras["notebooks"] == ["ipykernel", "matplotlib", "pandas"]
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


def test_neutral_schema_assets_are_included_in_sdist_manifest() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")

    assert "recursive-include docs/schemas *.json" in manifest
    assert "recursive-include docs/schema_examples *.json" in manifest


def test_neutral_schema_assets_are_valid_json() -> None:
    expected_stems = {"internal-circuit", "pauli-json", "workflow-json", "result-json"}
    schema_paths = sorted(Path("docs/schemas").glob("*.schema.json"))
    example_paths = sorted(Path("docs/schema_examples").glob("*.example.json"))

    assert {path.name.removesuffix(".schema.json") for path in schema_paths} == expected_stems
    assert {path.name.removesuffix(".example.json") for path in example_paths} == expected_stems
    for path in [*schema_paths, *example_paths]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if path.name.endswith(".example.json"):
            assert payload["schema_version"] == "0.1"


def test_notebook_result_assets_are_included_in_sdist_manifest() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")
    for extension in ("csv", "json", "png"):
        assert f"recursive-include docs/pages *.{extension}" in manifest


def test_translation_examples_are_included_in_sdist_manifest() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")

    assert "recursive-include examples *.py" in manifest
    assert "recursive-include examples *.json" in manifest
    assert "recursive-include examples *.md" in manifest
    assert "recursive-include examples/translation *.qasm" in manifest


def test_example_scripts_compile() -> None:
    for path in sorted(Path("examples").rglob("*.py")):
        py_compile.compile(path, doraise=True)
