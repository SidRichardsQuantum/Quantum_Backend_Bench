"""CLI tests."""

from __future__ import annotations

import importlib.util
import json

import pytest

from quantum_backend_bench.cli import main


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def test_cli_list_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["list"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Benchmarks" in captured.out
    assert "bernstein-vazirani" in captured.out
    assert "Suites" in captured.out
    assert "standard" in captured.out


def test_cli_info_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["info"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Integrations" in captured.out
    assert "cirq" in captured.out
    assert "matplotlib" in captured.out


def test_cli_recommend_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["recommend", "--use-case", "research"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Recommended installed backends" in captured.out
    assert "cirq" in captured.out


def test_cli_validate_command_with_fake_checks(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "quantum_backend_bench.core.validation.validate_backends",
        lambda backends=None, shots=64, success_threshold=0.95: [
            {
                "backend": "fake",
                "benchmark": "ghz",
                "status": "pass",
                "message": "ok",
                "metrics": {},
            }
        ],
    )
    monkeypatch.setattr(
        "quantum_backend_bench.core.validation.validation_passed",
        lambda checks: True,
    )
    exit_code = main(["validate", "--backends", "cirq"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Validation" in captured.out
    assert "fake" in captured.out


def test_cli_suite_list_cases_writes_manifest(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    output_path = tmp_path / "suite_manifest.json"
    exit_code = main(["suite", "smoke", "--list-cases", "--save-json", str(output_path)])
    captured = capsys.readouterr()
    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "Suite: smoke" in captured.out
    assert manifest[0]["suite"] == "smoke"
    assert manifest[0]["benchmark"] == "ghz"
    assert manifest[1]["result_name"] == "bernstein_vazirani"


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
    result = json.loads(output_path.read_text(encoding="utf-8"))[0]
    assert result["benchmark"] == "ghz"
    assert result["metadata"]["case_label"] == "ghz n=3"
    csv_text = csv_path.read_text(encoding="utf-8")
    assert "runtime_seconds" in csv_text
    assert "case_label" in csv_text


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


@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cli_new_oracle_benchmark(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "run",
            "bernstein-vazirani",
            "--backend",
            "cirq",
            "--n-qubits",
            "4",
            "--secret-string",
            "101",
            "--shots",
            "32",
            "--summary",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "success_prob" in captured.out
    assert "1.000000" in captured.out


@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cli_plot_artifacts(tmp_path) -> None:
    distribution_path = tmp_path / "distribution.png"
    heatmap_path = tmp_path / "heatmap.png"
    suite_path = tmp_path / "suite.png"
    quality_path = tmp_path / "quality.png"

    assert (
        main(
            [
                "run",
                "grover",
                "--backend",
                "cirq",
                "--n-qubits",
                "3",
                "--marked-state",
                "101",
                "--shots",
                "32",
                "--save-distribution",
                str(distribution_path),
                "--save-heatmap",
                str(heatmap_path),
            ]
        )
        == 0
    )
    assert distribution_path.exists()
    assert heatmap_path.exists()

    assert (
        main(
            [
                "suite",
                "smoke",
                "--backends",
                "cirq",
                "--shots",
                "32",
                "--save-suite-plot",
                str(suite_path),
            ]
        )
        == 0
    )
    assert suite_path.exists()

    assert (
        main(
            [
                "noise-sweep",
                "ghz",
                "--backend",
                "cirq",
                "--n-qubits",
                "3",
                "--shots",
                "32",
                "--noise-levels",
                "0.0",
                "0.001",
                "--save-quality-plot",
                str(quality_path),
            ]
        )
        == 0
    )
    assert quality_path.exists()
