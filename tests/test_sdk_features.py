"""Tests for SDK utility workflows."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quantum_backend_bench.core.circuit_export import (
    export_benchmark_circuit,
    import_openqasm_circuit,
)
from quantum_backend_bench.core.circuit_translate import (
    TranslationError,
    import_circuit_source,
    translate_circuit_source,
    translation_check_report,
    translation_result_report,
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

ROOT = Path(__file__).resolve().parents[1]
TRANSLATION_EXAMPLES = ROOT / "examples" / "translation"


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


def test_translate_openqasm_to_free_local_sdk_source() -> None:
    source = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""

    result = translate_circuit_source(source, from_format="openqasm", to_format="cirq")

    assert "import cirq" in result.source
    assert "cirq.H(qubits[0])" in result.source
    assert "cirq.CNOT(qubits[0], qubits[1])" in result.source
    assert "input_format=openqasm" in result.notes


def test_translate_qiskit_static_snippet_to_cirq() -> None:
    source = """
from qiskit import QuantumCircuit

circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure(0, 0)
circuit.measure(1, 1)
"""

    result = translate_circuit_source(source, from_format="qiskit", to_format="cirq")

    assert "cirq.H(qubits[0])" in result.source
    assert "cirq.CNOT(qubits[0], qubits[1])" in result.source
    assert 'cirq.measure(qubits[0], qubits[1], key="m")' in result.source


def test_translate_cirq_static_snippet_to_qiskit() -> None:
    source = """
import cirq

qubits = cirq.LineQubit.range(2)
circuit = cirq.Circuit()
circuit.append(cirq.H(qubits[0]))
circuit.append(cirq.CNOT(qubits[0], qubits[1]))
circuit.append(cirq.measure(qubits[0], qubits[1], key="m"))
"""

    result = translate_circuit_source(source, from_format="cirq", to_format="qiskit_aer")

    assert "from qiskit import QuantumCircuit" in result.source
    assert "circuit.h(0)" in result.source
    assert "circuit.cx(0, 1)" in result.source
    assert "circuit.measure(1, 0)" in result.source


def test_translate_pennylane_static_snippet_to_braket() -> None:
    source = """
import pennylane as qml

dev = qml.device("default.qubit", wires=2)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.sample(wires=[0, 1])
"""

    result = translate_circuit_source(source, from_format="pennylane", to_format="braket_local")

    assert "from braket.circuits import Circuit" in result.source
    assert "circuit.h(0)" in result.source
    assert "circuit.cnot(0, 1)" in result.source


def test_translate_braket_static_snippet_to_pennylane() -> None:
    source = """
from braket.circuits import Circuit

circuit = Circuit()
circuit.h(0)
circuit.cnot(0, 1)
circuit.probability(target=[0, 1])
"""

    result = translate_circuit_source(source, from_format="braket", to_format="pennylane")

    assert "import pennylane as qml" in result.source
    assert "qml.Hadamard(wires=0)" in result.source
    assert "qml.CNOT(wires=[0, 1])" in result.source


def test_translate_static_constants_and_simple_range_loop() -> None:
    source = """
from qiskit import QuantumCircuit

theta = 0.25
n = 3
circuit = QuantumCircuit(n)
for i in range(n):
    circuit.rx(theta, i)
circuit.cx(0, 1)
circuit.measure_all()
"""

    benchmark, detected = import_circuit_source(source, from_format="qiskit")

    assert detected == "qiskit"
    assert benchmark.n_qubits == 3
    assert [op.gate for op in benchmark.circuit_data.operations] == [
        "RX",
        "RX",
        "RX",
        "CNOT",
    ]
    assert benchmark.circuit_data.operations[0].params["theta"] == pytest.approx(0.25)


def test_translation_reports_include_caveats_and_verification() -> None:
    source = (TRANSLATION_EXAMPLES / "ghz.qasm").read_text(encoding="utf-8")
    result = translate_circuit_source(
        source, from_format="openqasm", to_format="cirq", verify="exact"
    )

    report = translation_result_report(
        result,
        source_path="examples/translation/ghz.qasm",
        from_format="openqasm",
        to_format="cirq",
    )

    assert report["verification"]["passed"] is True
    diagnostic_codes = {item["code"] for item in report["diagnostics"]}
    assert "translation.caveat.measurement_order" in diagnostic_codes
    assert "translation.caveat.controlled_phase" in diagnostic_codes


def test_translation_check_report_includes_gate_inventory() -> None:
    source = (TRANSLATION_EXAMPLES / "qiskit_registers.py").read_text(encoding="utf-8")
    benchmark, detected = import_circuit_source(source, from_format="qiskit")

    report = translation_check_report(benchmark, detected, source_path="qiskit_registers.py")

    assert report["input_format"] == "qiskit"
    assert report["gate_counts"] == {"CNOT": 1, "H": 1, "RX": 1}
    assert "cirq" in report["supported_outputs"]
    diagnostic_codes = {item["code"] for item in report["diagnostics"]}
    assert "translation.caveat.pennylane_sampling" in diagnostic_codes


def test_translate_exact_verification_passes() -> None:
    source = """
from qiskit import QuantumCircuit

circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure(0, 0)
circuit.measure(1, 1)
"""

    result = translate_circuit_source(
        source, from_format="qiskit", to_format="cirq", verify="exact"
    )

    assert result.verification is not None
    assert result.verification.passed
    assert result.verification.total_variation_distance == pytest.approx(0.0)


def test_translate_samples_verification_passes() -> None:
    source = """
from braket.circuits import Circuit

circuit = Circuit()
circuit.h(0)
circuit.cnot(0, 1)
circuit.probability(target=[0, 1])
"""

    result = translate_circuit_source(
        source,
        from_format="braket",
        to_format="qiskit_aer",
        verify="samples",
        sample_shots=128,
    )

    assert result.verification is not None
    assert result.verification.passed


def test_supported_sdk_pair_round_trips_preserve_internal_circuit() -> None:
    source = """
from qiskit import QuantumCircuit

circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.rx(0.125, 1)
circuit.cx(0, 1)
circuit.measure(0, 0)
circuit.measure(1, 1)
"""
    expected, _ = import_circuit_source(source, from_format="qiskit")
    output_to_input = {
        "braket_local": "braket",
        "cirq": "cirq",
        "pennylane": "pennylane",
        "qiskit_aer": "qiskit",
    }

    for output_format, input_format in output_to_input.items():
        translated = translate_circuit_source(
            source, from_format="qiskit", to_format=output_format, verify="exact"
        )
        actual, _ = import_circuit_source(translated.source, from_format=input_format)
        assert actual.circuit_data.operations == expected.circuit_data.operations
        assert actual.circuit_data.measurements == expected.circuit_data.measurements
        assert translated.verification is not None
        assert translated.verification.passed


def test_translate_pennylane_positional_wires() -> None:
    source = """
import pennylane as qml

dev = qml.device("default.qubit", wires=2)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(0)
    qml.RX(0.25, 1)
    qml.CNOT([0, 1])
    return qml.sample(wires=[0, 1])
"""

    benchmark, _ = import_circuit_source(source, from_format="pennylane")

    assert [op.gate for op in benchmark.circuit_data.operations] == ["H", "RX", "CNOT"]
    assert benchmark.circuit_data.operations[1].qubits == (1,)


def test_translate_qiskit_registers_and_pi_expression() -> None:
    source = (TRANSLATION_EXAMPLES / "qiskit_registers.py").read_text(encoding="utf-8")

    benchmark, detected = import_circuit_source(source, from_format="qiskit")

    assert detected == "qiskit"
    assert benchmark.n_qubits == 2
    assert [op.gate for op in benchmark.circuit_data.operations] == ["H", "RX", "CNOT"]
    assert benchmark.circuit_data.operations[1].params["theta"] == pytest.approx(
        3.141592653589793 / 2
    )


def test_translate_cirq_nested_constructor() -> None:
    source = (TRANSLATION_EXAMPLES / "cirq_nested.py").read_text(encoding="utf-8")

    benchmark, detected = import_circuit_source(source, from_format="cirq")

    assert detected == "cirq"
    assert [op.gate for op in benchmark.circuit_data.operations] == ["H", "RZ", "CNOT"]
    assert benchmark.circuit_data.operations[1].params["theta"] == pytest.approx(
        3.141592653589793 / 2
    )


def test_translate_include_runner_emits_runnable_script_footer() -> None:
    source = (TRANSLATION_EXAMPLES / "ghz.qasm").read_text(encoding="utf-8")

    result = translate_circuit_source(
        source,
        from_format="openqasm",
        to_format="cirq",
        include_runner=True,
        runner_shots=32,
        verify="exact",
    )

    assert 'if __name__ == "__main__":' in result.source
    assert "repetitions=32" in result.source
    assert result.verification is not None
    assert result.verification.passed


def test_translation_example_expected_outputs_are_stable() -> None:
    cases = [
        ("qiskit_registers.py", "qiskit", "cirq", "expected/qiskit_registers_to_cirq.py"),
        ("cirq_nested.py", "cirq", "qiskit_aer", "expected/cirq_nested_to_qiskit.py"),
        ("ghz.qasm", "openqasm", "pennylane", "expected/ghz_qasm_to_pennylane.py"),
    ]

    for source_name, from_format, to_format, expected_name in cases:
        source = (TRANSLATION_EXAMPLES / source_name).read_text(encoding="utf-8")
        expected = (TRANSLATION_EXAMPLES / expected_name).read_text(encoding="utf-8")
        result = translate_circuit_source(
            source, from_format=from_format, to_format=to_format, verify="exact"
        )
        assert result.source == expected
        assert result.verification is not None
        assert result.verification.passed


def test_translation_example_corpus_verifies() -> None:
    cases = [
        ("qiskit_registers.py", "qiskit", "cirq"),
        ("cirq_nested.py", "cirq", "qiskit_aer"),
        ("pennylane_positional.py", "pennylane", "braket_local"),
        ("braket_local.py", "braket", "pennylane"),
        ("ghz.qasm", "openqasm", "cirq"),
        ("internal_ghz.json", "internal-json", "qiskit_aer"),
    ]

    for source_name, from_format, to_format in cases:
        result = translate_circuit_source(
            (TRANSLATION_EXAMPLES / source_name).read_text(encoding="utf-8"),
            from_format=from_format,
            to_format=to_format,
            verify="exact",
        )
        assert result.verification is not None
        assert result.verification.passed


@pytest.mark.parametrize(
    ("filename", "from_format", "expected_code"),
    [
        ("custom_gate_qiskit.py", "qiskit", "qiskit.custom_gate"),
        ("conditional_qiskit.py", "qiskit", "python.conditionals"),
        ("non_range_loop_qiskit.py", "qiskit", "python.dynamic_loop"),
        ("runtime_call_qiskit.py", "qiskit", "sdk.runtime_call"),
        ("function_built_cirq.py", "cirq", "python.function_built_circuit"),
        ("dynamic_wires_pennylane.py", "pennylane", "python.dynamic_wires"),
        ("wire_arithmetic_qiskit.py", "qiskit", "python.dynamic_integer"),
    ],
)
def test_rejected_translation_fixtures_have_stable_diagnostics(
    filename: str, from_format: str, expected_code: str
) -> None:
    source = (TRANSLATION_EXAMPLES / "rejected" / filename).read_text(encoding="utf-8")

    with pytest.raises(TranslationError) as exc_info:
        import_circuit_source(source, from_format=from_format)

    assert expected_code in {diagnostic.code for diagnostic in exc_info.value.diagnostics}


def test_static_sdk_import_rejects_dynamic_parameters() -> None:
    source = """
from qiskit import QuantumCircuit

theta = get_theta()
circuit = QuantumCircuit(1)
circuit.rx(theta, 0)
"""

    with pytest.raises(ValueError, match="dynamic_parameter"):
        import_circuit_source(source, from_format="qiskit")


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
