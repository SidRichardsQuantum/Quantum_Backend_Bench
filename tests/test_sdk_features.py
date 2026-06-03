"""Tests for SDK utility workflows."""

from __future__ import annotations

import json

import pytest

from quantum_backend_bench.core.circuit_export import (
    export_benchmark_circuit,
    import_openqasm_circuit,
)
from quantum_backend_bench.core.diagnostics import diagnose_result_parity
from quantum_backend_bench.core.exact import (
    exact_amplitudes,
    exact_probabilities,
    pauli_z_expectation,
)
from quantum_backend_bench.core.factory import build_benchmark_from_config
from quantum_backend_bench.core.hardware import write_hardware_artifacts
from quantum_backend_bench.core.dataframe import results_to_records
from quantum_backend_bench.core.report import format_markdown_report
from quantum_backend_bench.core.sweeps import expand_benchmark_sweep, parse_sweep_specs


def test_openqasm_export_contains_measurements() -> None:
    benchmark = build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 3})

    exported = export_benchmark_circuit(benchmark, "openqasm")

    assert "OPENQASM 2.0;" in exported
    assert "h q[0];" in exported
    assert "cx q[0],q[1];" in exported
    assert "measure q[2] -> c[2];" in exported


def test_internal_json_export_is_parseable() -> None:
    benchmark = build_benchmark_from_config({"benchmark": "vqe-ansatz", "n_qubits": 3})

    payload = json.loads(export_benchmark_circuit(benchmark, "internal-json"))

    assert payload["benchmark"] == "vqe_ansatz"
    assert payload["n_qubits"] == 3
    assert payload["operations"]


def test_exact_probabilities_for_ghz() -> None:
    benchmark = build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 2})

    probabilities = exact_probabilities(benchmark)

    assert probabilities["00"] == pytest.approx(0.5)
    assert probabilities["11"] == pytest.approx(0.5)
    assert probabilities["01"] == pytest.approx(0.0)
    assert probabilities["10"] == pytest.approx(0.0)


def test_parameter_sweep_expands_cases() -> None:
    specs = parse_sweep_specs(["n-qubits=2:4", "depth=1,2"])
    benchmarks = expand_benchmark_sweep({"benchmark": "random-circuit"}, specs)

    assert len(benchmarks) == 6
    assert {item.n_qubits for item in benchmarks} == {2, 3, 4}
    assert {item.parameters["depth"] for item in benchmarks} == {1, 2}


def test_diagnostics_flags_reversed_bitstrings() -> None:
    findings = diagnose_result_parity(
        [
            {"benchmark": "demo", "backend": "left", "counts": {"01": 1}, "metadata": {}},
            {"benchmark": "demo", "backend": "right", "counts": {"10": 1}, "metadata": {}},
        ]
    )

    assert any("endian" in finding for finding in findings)


def test_hardware_artifacts_include_qasm(tmp_path) -> None:
    benchmark = build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 2})

    paths = write_hardware_artifacts(benchmark, tmp_path, backend_hint="ibm", shots=128)

    assert paths["qasm"].read_text().startswith("OPENQASM 2.0;")
    assert "suggested_shots: `128`" in paths["readme"].read_text()


def test_applied_benchmarks_build_internal_circuits() -> None:
    for name in (
        "amplitude-estimation",
        "phase-estimation",
        "quantum-kernel",
        "vqe-ansatz",
    ):
        benchmark = build_benchmark_from_config({"benchmark": name, "n_qubits": 3})
        assert benchmark.n_qubits == 3
        assert benchmark.circuit_data.operations


def test_openqasm3_export_and_import_round_trip() -> None:
    benchmark = build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 2})

    exported = export_benchmark_circuit(benchmark, "openqasm3")
    imported = import_openqasm_circuit(exported, name="roundtrip")

    assert "OPENQASM 3.0;" in exported
    assert imported.name == "roundtrip"
    assert imported.n_qubits == 2
    assert [op.gate for op in imported.circuit_data.operations] == ["H", "CNOT"]


def test_exact_amplitudes_and_pauli_expectation() -> None:
    benchmark = build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 2})

    amplitudes = exact_amplitudes(benchmark, top_k=1)

    assert len(amplitudes) == 1
    assert pauli_z_expectation(benchmark, "ZZ") == pytest.approx(1.0)


def test_hardware_artifacts_are_provider_aware(tmp_path) -> None:
    benchmark = build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 2})

    paths = write_hardware_artifacts(
        benchmark, tmp_path, provider="ibm", qasm_version="openqasm3", shots=256
    )

    assert paths["qasm"].suffix == ".qasm3"
    readme = paths["readme"].read_text(encoding="utf-8")
    assert "provider: `ibm`" in readme
    assert "QuantumCircuit.from_qasm_file" in readme


def test_compile_metrics_flatten_and_report() -> None:
    result = {
        "benchmark": "ghz",
        "backend": "qiskit_aer",
        "n_qubits": 2,
        "shots": 16,
        "repeats": 1,
        "parameters": {"n_qubits": 2},
        "metrics": {
            "runtime_seconds": 0.2,
            "compile_seconds": 0.05,
            "compiled_depth": 3,
            "compiled_gate_count": 2,
            "compiled_two_qubit_gate_count": 1,
        },
        "metadata": {
            "case_label": "ghz n=2",
            "compile_toolchain": "qiskit.transpile",
            "compiled_basis_gates": {"cx": 1, "h": 1},
        },
    }

    record = results_to_records([result])[0]
    report = format_markdown_report({"results": [result]})

    assert record["compile_seconds"] == 0.05
    assert record["compiled_depth"] == 3
    assert record["compile_toolchain"] == "qiskit.transpile"
    assert "compile mean" in report
    assert "qiskit.transpile" in report
