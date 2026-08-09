"""Packaging metadata tests."""

from __future__ import annotations

import json
import py_compile
import tomllib
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

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
    "docs/RELEASE_POLICY.md",
}


def test_backend_dependencies_are_optional_extras() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    extras = project["optional-dependencies"]

    assert project["dependencies"] == ["numpy>=1.26"]
    assert extras["cirq"] == ["cirq"]
    assert extras["pennylane"] == ["pennylane"]
    assert extras["braket"] == ["amazon-braket-sdk"]
    assert extras["qiskit"] == ["qiskit", "qiskit-aer"]
    assert extras["qibo"] == ["qibo"]
    assert extras["cudaq"] == ["cudaq"]
    assert "cirq" in extras["dev"]
    assert "jsonschema" in extras["dev"]
    assert "mypy" in extras["dev"]
    assert "pandas" in extras["dev"]
    assert extras["docs"] == ["markdown", "matplotlib", "pymdown-extensions"]
    assert extras["pyquil"] == ["pyquil"]
    assert extras["notebooks"] == ["ipykernel", "matplotlib", "pandas"]
    assert extras["yaml"] == ["PyYAML"]
    assert "cirq" in extras["all"]
    assert "qiskit-aer" in extras["all"]
    assert "qibo" in extras["all"]
    assert "pytket" in extras["all"]
    assert "PyYAML" in extras["all"]
    assert "cudaq" not in extras["all"]
    assert "pyquil" not in extras["all"]
    assert "cudaq" in extras["full"]
    assert "pyquil" in extras["full"]

    mypy = metadata["tool"]["mypy"]
    assert mypy["files"] == ["quantum_backend_bench"]
    assert mypy["disallow_untyped_defs"] is True


def test_required_docs_are_included_in_sdist_manifest() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")
    for document in REQUIRED_SDIST_DOCS:
        assert f"include {document}" in manifest


def test_ci_constraints_exist_for_reproducible_validation() -> None:
    constraints = Path("constraints/ci.txt").read_text(encoding="utf-8")

    for package in (
        "mypy",
        "pytest",
        "ruff",
        "jsonschema",
        "cirq",
        "qiskit-aer",
        "pennylane",
        "qibo",
    ):
        assert package in constraints
    assert "cirq>=1.4,<2" in constraints
    assert "matplotlib==3.11.1" in constraints
    assert "pillow==12.3.0" in constraints
    assert "qiskit-aer>=0.15,<1" in constraints
    assert "qibo>=0.3,<0.4" in constraints


def test_release_policy_and_constraints_are_included_in_sdist_manifest() -> None:
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")

    assert "include docs/RELEASE_POLICY.md" in manifest
    assert "recursive-include constraints *.txt" in manifest


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


def test_release_scripts_compile() -> None:
    for path in sorted(Path("scripts").glob("*.py")):
        py_compile.compile(path, doraise=True)


def test_neutral_json_schemas_publish_draft_ids_and_shared_references() -> None:
    schemas = {
        path.stem.removesuffix(".schema"): json.loads(path.read_text(encoding="utf-8"))
        for path in Path("docs/schemas").glob("*.schema.json")
    }

    assert set(schemas) == {"internal-circuit", "pauli-json", "result-json", "workflow-json"}
    for name, schema in schemas.items():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"].endswith(f"/schemas/{name}.schema.json")
        assert "" not in schema

    observable = schemas["workflow-json"]["properties"]["measurements"]["items"]["properties"][
        "observable"
    ]
    assert observable == {"$ref": "pauli-json.schema.json"}


def test_neutral_schema_examples_validate_against_published_schemas() -> None:
    schema_paths = sorted(Path("docs/schemas").glob("*.schema.json"))
    example_paths = sorted(Path("docs/schema_examples").glob("*.example.json"))
    schemas = {
        path.name.removesuffix(".schema.json"): json.loads(path.read_text(encoding="utf-8"))
        for path in schema_paths
    }
    examples = {
        path.name.removesuffix(".example.json"): json.loads(path.read_text(encoding="utf-8"))
        for path in example_paths
    }

    assert schemas.keys() == examples.keys()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    for name, example in examples.items():
        Draft202012Validator(schemas[name], registry=registry).validate(example)
