"""Notebook consistency tests."""

from __future__ import annotations

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
