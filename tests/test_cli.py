"""CLI tests."""

from __future__ import annotations

import importlib.util
import json

import pytest

from quantum_backend_bench.cli import main


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cli_run_command(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    output_path = tmp_path / "result.json"
    csv_path = tmp_path / "result.csv"
    exit_code = main(
        [
            "run",
            "ghz",
            "--backend",
            "cirq",
            "--n-qubits",
            "3",
            "--shots",
            "32",
            "--save-json",
            str(output_path),
            "--save-csv",
            str(csv_path),
            "--summary",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "backend" in captured.out
    assert "Summary" in captured.out
    assert output_path.exists()
    assert csv_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))[0]["benchmark"] == "ghz"
    assert "runtime_seconds" in csv_path.read_text(encoding="utf-8")


@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cli_draw_command(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    output_path = tmp_path / "ghz_cirq.txt"
    exit_code = main(
        [
            "draw",
            "ghz",
            "--backend",
            "cirq",
            "--n-qubits",
            "3",
            "--save-path",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "H" in captured.out
    assert output_path.exists()


@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cli_suite_command(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    output_path = tmp_path / "suite.csv"
    exit_code = main(
        [
            "suite",
            "smoke",
            "--backends",
            "cirq",
            "--shots",
            "32",
            "--save-csv",
            str(output_path),
            "--summary",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ghz" in output_path.read_text(encoding="utf-8")
    assert "Summary" in captured.out
