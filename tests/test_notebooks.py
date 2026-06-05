"""Notebook consistency tests."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
EXPECTED_KERNEL = {"display_name": "Python 3", "language": "python", "name": "python3"}
SDK_NOTEBOOK_PATTERN = re.compile(r"^0[4-8]_sdk_.*_workflow\.ipynb$")


def test_notebook_numbering_is_unique_and_contiguous() -> None:
    notebooks = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
    numbers = [path.name.split("_", 1)[0] for path in notebooks]

    assert len(numbers) == len(set(numbers))
    assert numbers == [f"{index:02d}" for index in range(1, len(notebooks) + 1)]


def test_notebooks_are_clean_and_use_standard_kernel() -> None:
    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = _load_notebook(path)
        assert notebook.get("metadata", {}).get("kernelspec") == EXPECTED_KERNEL

        for cell in notebook.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            assert cell.get("execution_count") is None, path.name
            assert cell.get("outputs", []) == [], path.name


def test_notebook_code_cells_parse() -> None:
    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = _load_notebook(path)
        for index, cell in enumerate(notebook.get("cells", []), start=1):
            if cell.get("cell_type") != "code":
                continue
            ast.parse(
                "".join(cell.get("source", [])),
                filename=f"{path.name}:cell-{index}",
            )


def test_sdk_notebooks_use_shared_notebook_helpers() -> None:
    sdk_notebooks = [
        path
        for path in sorted(NOTEBOOK_DIR.glob("*.ipynb"))
        if SDK_NOTEBOOK_PATTERN.match(path.name)
    ]
    assert [path.name for path in sdk_notebooks] == [
        "04_sdk_cirq_workflow.ipynb",
        "05_sdk_qiskit_workflow.ipynb",
        "06_sdk_pennylane_workflow.ipynb",
        "07_sdk_braket_workflow.ipynb",
        "08_sdk_qutip_workflow.ipynb",
    ]

    for path in sdk_notebooks:
        source = _code_source(_load_notebook(path))
        assert "from quantum_backend_bench.utils.notebook import" in source
        assert "save_result_artifacts" in source
        assert "top_measurement_states" in source
        assert "verification_frame" in source


def test_notebooks_define_variables_and_parameters_near_top() -> None:
    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = _load_notebook(path)
        markdown_sources = [
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "markdown"
        ]
        matching_indexes = [
            index
            for index, source in enumerate(markdown_sources)
            if "## Variables and Parameters" in source
        ]

        assert matching_indexes, f"{path.name} is missing Variables and Parameters"
        assert matching_indexes[0] <= 3, f"{path.name} should define variables near the top"


def test_notebook_readme_links_existing_notebooks() -> None:
    readme = NOTEBOOK_DIR / "README.md"
    text = readme.read_text(encoding="utf-8")
    linked_notebooks = [
        (readme.parent / unquote(urlparse(target).path)).resolve()
        for target in re.findall(r"`([^`]+\.ipynb)`", text)
    ]

    assert linked_notebooks
    for linked in linked_notebooks:
        assert linked.exists(), f"notebooks/README.md references missing {linked.name}"


def _load_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _code_source(notebook: dict) -> str:
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    )


def test_translation_notebook_uses_translation_helpers() -> None:
    path = NOTEBOOK_DIR / "09_circuit_translation_workflow.ipynb"
    notebook = _load_notebook(path)
    source = _code_source(notebook)

    assert "translate_circuit_source" in source
    assert "translation_check_report" in source
    assert "translation_result_report" in source
    assert "translation_error_report" in source
    assert "verification_frame" in source
    assert "draw_benchmark" in source
    for target in ("qiskit_aer", "cirq", "pennylane", "braket_local"):
        assert target in source


def test_hamiltonian_translation_notebook_uses_translation_helpers() -> None:
    path = NOTEBOOK_DIR / "10_observable_hamiltonian_translation_workflow.ipynb"
    notebook = _load_notebook(path)
    source = _code_source(notebook)

    assert "translate_hamiltonian_source" in source
    assert "hamiltonian_check_report" in source
    assert "hamiltonian_translation_report" in source
    assert "translation_capability_rows" in source
    assert "verification_frame" in source
    assert "import matplotlib.pyplot as plt" in source
    assert "Pauli Hamiltonian coefficients" in source
    assert "${pauli}_{wire}$" in source
    for target in ("qiskit_aer", "cirq", "pennylane", "braket_local", "pauli-json"):
        assert target in source


def test_workflow_translation_notebook_uses_workflow_helpers() -> None:
    path = NOTEBOOK_DIR / "11_parameterized_workflow_translation.ipynb"
    notebook = _load_notebook(path)
    source = _code_source(notebook)

    assert "translate_workflow_source" in source
    assert "verify_workflow_translation" in source
    assert "workflow_translation_report" in source
    assert "normalize_result_source" in source
    assert "group_pauli_terms_source" in source
    assert "verification_frame" in source
    for target in ("qiskit_aer", "cirq", "pennylane", "braket_local"):
        assert target in source
