"""CLI tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from quantum_backend_bench.cli import main

ROOT = Path(__file__).resolve().parents[1]


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _fake_result(benchmark, backend: str = "cirq", shots: int = 8) -> dict:
    zero_state = "0" * benchmark.n_qubits
    one_state = "1" * benchmark.n_qubits
    counts = {zero_state: shots // 2, one_state: shots - shots // 2}
    return {
        "benchmark": benchmark.name,
        "backend": backend,
        "n_qubits": benchmark.n_qubits,
        "shots": shots,
        "repeats": 1,
        "total_shots": shots,
        "parameters": benchmark.parameters,
        "metrics": {
            "runtime_seconds": 0.001,
            "runtime_seconds_stddev": 0.0,
            "measurement_distribution": {
                zero_state: counts[zero_state] / shots,
                one_state: counts[one_state] / shots,
            },
            "depth": 3,
            "gate_count": 4,
            "two_qubit_gate_count": 2,
            "success_probability": 1.0,
            "total_variation_distance": 0.0,
        },
        "counts": counts,
        "metadata": {
            "case_label": f"{benchmark.name} n={benchmark.n_qubits}",
            "benchmark_family": benchmark.metadata.get("benchmark_family", "test"),
            "noise_level": benchmark.parameters.get("noise_level"),
            "backend_noise_support": "depolarizing",
        },
    }


def _patch_cli_run_benchmark(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_benchmark(benchmark, backends, shots=1024, repeats=1):  # type: ignore[no-untyped-def]
        del repeats
        return [_fake_result(benchmark, backend=backend, shots=shots) for backend in backends]

    monkeypatch.setattr("quantum_backend_bench.cli.run_benchmark", fake_run_benchmark)


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


def test_cli_doctor_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["doctor"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Diagnostics" in captured.out
    assert "cirq" in captured.out
    assert "quantum-backend-bench" in captured.out


def test_cli_recommend_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["recommend", "--use-case", "research"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Recommended installed backends" in captured.out
    assert "cirq" in captured.out
    assert (
        "Other execution backends" in captured.out
        or "Recommended installed backends" in captured.out
    )


def test_cli_compatibility_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["compatibility"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Compatibility" in captured.out
    assert "Python:" in captured.out
    assert "cirq" in captured.out


def test_cli_bundle_command_writes_artifacts(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    result_path = tmp_path / "results.json"
    output_dir = tmp_path / "bundle"
    result_path.write_text(
        json.dumps(
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 3,
                    "shots": 8,
                    "repeats": 1,
                    "total_shots": 8,
                    "parameters": {"n_qubits": 3},
                    "metrics": {"runtime_seconds": 0.1, "depth": 4},
                    "counts": {"000": 4, "111": 4},
                    "metadata": {"case_label": "ghz n=3"},
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["bundle", str(result_path), "--output", str(output_dir), "--no-plots"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Created bundle" in captured.out
    assert (output_dir / "results.json").exists()
    assert (output_dir / "results.csv").exists()
    assert (output_dir / "report.md").exists()


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


def test_cli_diff_command_reports_regression(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(
        json.dumps(
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 3,
                    "parameters": {},
                    "metrics": {"runtime_seconds": 0.1},
                }
            ]
        ),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 3,
                    "parameters": {},
                    "metrics": {"runtime_seconds": 0.2},
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "diff",
            str(baseline_path),
            str(candidate_path),
            "--metric",
            "runtime_seconds",
            "--fail-on-regression",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "regressed" in captured.out


def test_cli_report_command_writes_markdown(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    result_path = tmp_path / "results.json"
    report_path = tmp_path / "report.md"
    result_path.write_text(
        json.dumps(
            [
                {
                    "benchmark": "ghz",
                    "backend": "cirq",
                    "n_qubits": 3,
                    "shots": 8,
                    "repeats": 1,
                    "parameters": {"n_qubits": 3},
                    "metrics": {"runtime_seconds": 0.1, "depth": 3},
                    "metadata": {
                        "case_label": "ghz n=3",
                        "backend_noise_support": "depolarizing",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["report", str(result_path), "--output", str(report_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Saved report" in captured.out
    assert "ghz n=3" in report_path.read_text(encoding="utf-8")


def test_cli_preset_list_and_show(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    output_path = tmp_path / "preset.json"
    assert main(["preset", "list"]) == 0
    captured = capsys.readouterr()
    assert "algorithmic" in captured.out

    assert main(["preset", "show", "algorithmic", "--save-json", str(output_path)]) == 0
    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    assert manifest["benchmarks"][-1]["benchmark"] == "qaoa-maxcut"


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


def test_cli_rejects_invalid_shots(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["run", "ghz", "--backend", "cirq", "--shots", "0"])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert "must be at least 1" in captured.err


def test_cli_rejects_invalid_repeats(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["suite", "smoke", "--repeats", "0"])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert "must be at least 1" in captured.err


def test_cli_rejects_invalid_noise_level(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["noise-sweep", "ghz", "--backend", "cirq", "--noise-levels", "1.5"])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert "must be between 0 and 1" in captured.err


def test_cli_rejects_invalid_success_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["validate", "--success-threshold", "-0.1"])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert "must be between 0 and 1" in captured.err


def test_cli_run_command(
    capsys: pytest.CaptureFixture[str], tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_cli_run_benchmark(monkeypatch)
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
            "8",
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


def test_cli_suite_command(
    capsys: pytest.CaptureFixture[str], tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_cli_run_benchmark(monkeypatch)
    output_path = tmp_path / "suite.csv"
    exit_code = main(
        [
            "suite",
            "smoke",
            "--backends",
            "cirq",
            "--shots",
            "8",
            "--save-csv",
            str(output_path),
            "--summary",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ghz" in output_path.read_text(encoding="utf-8")
    assert "Summary" in captured.out


def test_cli_new_oracle_benchmark(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_cli_run_benchmark(monkeypatch)
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
            "8",
            "--summary",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "success_prob" in captured.out
    assert "1.000000" in captured.out


def test_cli_plot_artifacts(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_cli_run_benchmark(monkeypatch)
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
                "8",
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
                "8",
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
                "8",
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


def test_cli_export_openqasm3(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["export", "ghz", "--n-qubits", "2", "--format", "openqasm3"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "OPENQASM 3.0;" in captured.out
    assert "qubit[2] q;" in captured.out


def test_cli_import_qasm_round_trip(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    qasm_path = tmp_path / "ghz.qasm"
    qasm_path.write_text(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n',
        encoding="utf-8",
    )

    exit_code = main(["import-qasm", str(qasm_path), "--name", "roundtrip"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"benchmark": "roundtrip"' in captured.out
    assert '"gate": "CNOT"' in captured.out


def test_cli_translate_qasm_to_sdk_file(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    qasm_path = tmp_path / "ghz.qasm"
    output_path = tmp_path / "ghz_cirq.py"
    qasm_path.write_text(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n',
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate",
            str(qasm_path),
            "--from-format",
            "openqasm",
            "--to-format",
            "cirq",
            "--output",
            str(output_path),
            "--verify",
            "exact",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Saved translated circuit" in captured.out
    assert "input_format=openqasm" in captured.out
    assert "verification=passed" in captured.out
    translated = output_path.read_text(encoding="utf-8")
    assert "import cirq" in translated
    assert "cirq.CNOT(qubits[0], qubits[1])" in translated


def test_cli_translate_check_reports_supported_source(
    capsys: pytest.CaptureFixture[str], tmp_path
) -> None:
    source_path = tmp_path / "registers.py"
    source_path.write_text(
        "from qiskit import QuantumCircuit\n"
        "circuit = QuantumCircuit(2)\n"
        "circuit.h(0)\n"
        "circuit.cx(0, 1)\n"
        "circuit.measure_all()\n",
        encoding="utf-8",
    )

    exit_code = main(["translate-check", str(source_path), "--from-format", "qiskit"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Translation check" in captured.out
    assert "input_format: qiskit" in captured.out
    assert "verification_available: yes" in captured.out
    assert '"CNOT": 1' in captured.out


def test_cli_translate_save_report(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    qasm_path = tmp_path / "ghz.qasm"
    report_path = tmp_path / "translate_report.json"
    qasm_path.write_text(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n',
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate",
            str(qasm_path),
            "--from-format",
            "openqasm",
            "--to-format",
            "cirq",
            "--verify",
            "exact",
            "--save-report",
            str(report_path),
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "Saved translation report" in captured.out
    assert report["to_format"] == "cirq"
    assert report["verification"]["passed"] is True
    assert any(
        item["code"] == "translation.caveat.measurement_order" for item in report["diagnostics"]
    )


def test_cli_translate_check_json_stdout(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    source_path = tmp_path / "registers.py"
    source_path.write_text(
        "from qiskit import QuantumCircuit\n"
        "circuit = QuantumCircuit(2)\n"
        "circuit.h(0)\n"
        "circuit.cx(0, 1)\n"
        "circuit.measure_all()\n",
        encoding="utf-8",
    )

    exit_code = main(["translate-check", str(source_path), "--from-format", "qiskit", "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == 0
    assert report["input_format"] == "qiskit"
    assert report["gate_counts"] == {"CNOT": 1, "H": 1}
    assert "Translation check" not in captured.out


def test_cli_translate_check_save_report(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    source_path = tmp_path / "registers.py"
    report_path = tmp_path / "check_report.json"
    source_path.write_text(
        "from qiskit import QuantumCircuit\n"
        "circuit = QuantumCircuit(2)\n"
        "circuit.h(0)\n"
        "circuit.cx(0, 1)\n"
        "circuit.measure_all()\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate-check",
            str(source_path),
            "--from-format",
            "qiskit",
            "--save-report",
            str(report_path),
        ]
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["input_format"] == "qiskit"
    assert report["gate_counts"] == {"CNOT": 1, "H": 1}
    assert report["verification_available"] is True


def test_cli_translate_include_runner(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    qasm_path = tmp_path / "ghz.qasm"
    output_path = tmp_path / "ghz_runner.py"
    qasm_path.write_text(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n',
        encoding="utf-8",
    )

    exit_code = main(
        [
            "translate",
            str(qasm_path),
            "--from-format",
            "openqasm",
            "--to-format",
            "cirq",
            "--include-runner",
            "--runner-shots",
            "16",
            "--output",
            str(output_path),
            "--verify",
            "exact",
        ]
    )

    assert exit_code == 0
    assert 'if __name__ == "__main__":' in output_path.read_text(encoding="utf-8")
    assert "repetitions=16" in output_path.read_text(encoding="utf-8")


def test_translation_update_expected_check_script() -> None:
    result = subprocess.run(
        [sys.executable, "examples/translation/update_expected.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "translation expected outputs are current" in result.stdout


def test_cli_exact_top_k_amplitudes_and_observable(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["exact", "ghz", "--n-qubits", "2", "--top-k", "1", "--amplitudes", "--observable", "ZZ"]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert len(payload["probabilities"]) == 1
    assert "amplitudes" in payload
    assert payload["expectation"]["ZZ"] == pytest.approx(1.0)


def test_cli_hardware_provider_artifacts(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    exit_code = main(
        [
            "hardware",
            "ghz",
            "--n-qubits",
            "2",
            "--output",
            str(tmp_path),
            "--provider",
            "ibm",
            "--qasm-version",
            "openqasm3",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Created hardware artifacts" in captured.out
    assert (tmp_path / "ghz.qasm3").exists()
    assert "provider: `ibm`" in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_cli_run_sweep_uses_all_cases(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_cli_run_benchmark(monkeypatch)

    exit_code = main(
        [
            "run",
            "random-circuit",
            "--backend",
            "cirq",
            "--sweep",
            "n-qubits=2:3",
            "--shots",
            "8",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "random_circuit n=2" in captured.out
    assert "random_circuit n=3" in captured.out


def test_cli_noise_sweep_accepts_noise_type(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_cli_run_benchmark(monkeypatch)

    exit_code = main(
        [
            "noise-sweep",
            "ghz",
            "--backend",
            "cirq",
            "--noise-type",
            "phase_flip",
            "--noise-levels",
            "0",
            "0.01",
            "--shots",
            "8",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "phase_flip" in captured.out or "ghz_noise" in captured.out


def test_cli_diagnose_reports_findings(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    results_path = tmp_path / "results.json"
    results_path.write_text(
        json.dumps(
            [
                {"benchmark": "demo", "backend": "left", "counts": {"01": 1}, "metadata": {}},
                {"benchmark": "demo", "backend": "right", "counts": {"10": 1}, "metadata": {}},
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["diagnose", str(results_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "endian" in captured.out
