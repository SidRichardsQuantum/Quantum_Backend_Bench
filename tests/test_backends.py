"""Backend interface tests."""

from __future__ import annotations

import importlib.util
import builtins
import json
import shutil

import pytest

from quantum_backend_bench.backends import get_backend
from quantum_backend_bench.backends.base_backend import BaseBackend
from quantum_backend_bench.backends.cirq_backend import CirqBackend
from quantum_backend_bench.backends.cudaq_backend import CudaQBackend
from quantum_backend_bench.backends.pyquil_backend import PyQuilQVMBackend
from quantum_backend_bench.backends.qiskit_backend import QiskitAerBackend
from quantum_backend_bench.backends.qutip_backend import QuTiPBackend
from quantum_backend_bench.benchmarks.bernstein_vazirani import (
    build_benchmark as build_bernstein_vazirani,
)
from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench.core.workflow_translate import translate_workflow_source


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _has_pyquil_runtime() -> bool:
    return (
        _has_module("pyquil")
        and shutil.which("qvm") is not None
        and shutil.which("quilc") is not None
    )


WORKFLOW_EXECUTION_JSON = json.dumps(
    {
        "schema_version": "0.1",
        "name": "optional_sdk_result_contract",
        "n_qubits": 2,
        "parameters": [],
        "parameter_bindings": {},
        "operations": [
            {"gate": "H", "targets": [0]},
            {"gate": "CNOT", "controls": [0], "targets": [1]},
        ],
        "measurements": [
            {"type": "counts", "targets": [0, 1]},
            {
                "type": "expectation",
                "targets": [0, 1],
                "observable": {
                    "schema_version": "0.1",
                    "n_qubits": 2,
                    "terms": [
                        {
                            "coefficient": 1.0,
                            "paulis": {"0": "Z", "1": "Z"},
                        }
                    ],
                },
            },
        ],
        "shots": 64,
        "seed": 1234,
    }
)


def _execute_generated_workflow(target: str) -> dict[str, object]:
    translated = translate_workflow_source(
        WORKFLOW_EXECUTION_JSON, to_format=target, verify="semantic"
    )
    assert translated.verification is not None
    assert translated.verification.passed
    namespace: dict[str, object] = {}
    exec(compile(translated.source, f"<generated-{target}-workflow>", "exec"), namespace)
    result = namespace["neutral_result"]
    assert isinstance(result, dict)
    return result


def _assert_generated_workflow_result(result: dict[str, object]) -> None:
    assert result["schema_version"] == "0.1"
    assert result["shots"] == 64
    counts = result["counts"]
    assert isinstance(counts, dict)
    assert sum(counts.values()) == 64
    assert set(counts).issubset({"00", "11"})
    expectations = result["expectations"]
    assert isinstance(expectations, dict)
    assert expectations["expectation_1"] == pytest.approx(1.0)


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cirq_generated_workflow_emits_valid_neutral_result() -> None:
    _assert_generated_workflow_result(_execute_generated_workflow("cirq"))


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("pennylane"), reason="PennyLane not installed")
def test_pennylane_generated_workflow_emits_valid_neutral_result() -> None:
    _assert_generated_workflow_result(_execute_generated_workflow("pennylane"))


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("braket"), reason="Braket SDK not installed")
def test_braket_generated_workflow_emits_valid_neutral_result() -> None:
    _assert_generated_workflow_result(_execute_generated_workflow("braket_local"))


@pytest.mark.optional_sdk
@pytest.mark.skipif(
    not (_has_module("qiskit") and _has_module("qiskit_aer")),
    reason="Qiskit Aer not installed",
)
def test_qiskit_generated_workflow_emits_valid_neutral_result() -> None:
    _assert_generated_workflow_result(_execute_generated_workflow("qiskit_aer"))


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cirq_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("cirq").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32
    assert set(result["counts"]).issubset({"000", "111"})


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cirq_bernstein_vazirani_finds_secret_string() -> None:
    result = get_backend("cirq").run(
        build_bernstein_vazirani(n_qubits=4, secret_string="101"), shots=32
    )
    assert result["counts"] == {"101": 32}


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("pennylane"), reason="PennyLane not installed")
def test_pennylane_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("pennylane").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32
    assert set(result["counts"]).issubset({"000", "111"})


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("braket"), reason="Braket SDK not installed")
def test_braket_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("braket_local").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32
    assert set(result["counts"]).issubset({"000", "111"})


@pytest.mark.skipif(
    not (_has_module("qiskit") and _has_module("qiskit_aer")),
    reason="Qiskit Aer not installed",
)
@pytest.mark.optional_sdk
def test_qiskit_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("qiskit_aer").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32
    assert set(result["counts"]).issubset({"000", "111"})


@pytest.mark.heavy_sdk
@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("cudaq"), reason="CUDA-Q not installed")
def test_cudaq_backend_runs() -> None:
    result = get_backend("cudaq").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32


@pytest.mark.skipif(
    not _has_pyquil_runtime(),
    reason="pyQuil local Forest runtime not installed",
)
@pytest.mark.external_runtime
@pytest.mark.optional_sdk
def test_pyquil_backend_runs() -> None:
    result = get_backend("pyquil_qvm").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("pyquil"), reason="pyQuil not installed")
def test_pyquil_backend_builds_native_circuit_without_qvm_runtime() -> None:
    program = get_backend("pyquil_qvm").build_native_circuit(build_benchmark(n_qubits=3))
    assert "MEASURE" in program.out()


@pytest.mark.optional_sdk
@pytest.mark.skipif(not _has_module("qutip"), reason="QuTiP not installed")
def test_qutip_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("qutip").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32
    assert set(result["counts"]).issubset({"000", "111"})


def test_backend_structural_metrics_are_available() -> None:
    metrics = get_backend("cirq").structural_metrics(build_benchmark(n_qubits=3))
    assert "depth" in metrics


def test_base_backend_draw_writes_text_diagram(tmp_path) -> None:
    class FakeBackend(BaseBackend):
        name = "fake"

        def run(self, benchmark, shots=1024):  # type: ignore[no-untyped-def]
            del benchmark, shots
            return {}

        def build_native_circuit(self, benchmark):  # type: ignore[no-untyped-def]
            assert benchmark.name == "ghz"
            return "fake native circuit"

    output_path = tmp_path / "nested" / "diagram.txt"
    diagram = FakeBackend().draw(build_benchmark(n_qubits=2), save_path=str(output_path))

    assert diagram == "fake native circuit"
    assert output_path.read_text(encoding="utf-8") == "fake native circuit\n"


def test_missing_backend_dependency_error_mentions_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def block_cirq(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "cirq":
            raise ImportError("blocked")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", block_cirq)
    with pytest.raises(RuntimeError, match=r"quantum-backend-bench\[cirq\]"):
        CirqBackend().build_native_circuit(build_benchmark(n_qubits=2))


def test_new_backend_missing_dependency_errors_mention_extras(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def block_new_sdks(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        blocked = {"qiskit", "cudaq", "pyquil", "qutip"}
        if name in blocked:
            raise ImportError("blocked")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", block_new_sdks)
    benchmark = build_benchmark(n_qubits=2)
    cases = [
        (QiskitAerBackend(), r"quantum-backend-bench\[qiskit\]"),
        (CudaQBackend(), r"quantum-backend-bench\[cudaq\]"),
        (PyQuilQVMBackend(), r"quantum-backend-bench\[pyquil\]"),
        (QuTiPBackend(), r"quantum-backend-bench\[qutip\]"),
    ]
    for backend, pattern in cases:
        with pytest.raises(RuntimeError, match=pattern):
            backend.build_native_circuit(benchmark)
