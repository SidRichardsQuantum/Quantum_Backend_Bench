"""Backend interface tests."""

from __future__ import annotations

import importlib.util
import builtins

import pytest

from quantum_backend_bench.backends import get_backend
from quantum_backend_bench.backends.cirq_backend import CirqBackend
from quantum_backend_bench.benchmarks.ghz import build_benchmark


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cirq_backend_runs() -> None:
    result = get_backend("cirq").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32


@pytest.mark.skipif(not _has_module("cirq"), reason="Cirq not installed")
def test_cirq_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("cirq").run(build_benchmark(n_qubits=3), shots=64)
    assert set(result["counts"]).issubset({"000", "111"})


@pytest.mark.skipif(not _has_module("pennylane"), reason="PennyLane not installed")
def test_pennylane_backend_runs() -> None:
    result = get_backend("pennylane").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32


@pytest.mark.skipif(not _has_module("pennylane"), reason="PennyLane not installed")
def test_pennylane_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("pennylane").run(build_benchmark(n_qubits=3), shots=64)
    assert set(result["counts"]).issubset({"000", "111"})


@pytest.mark.skipif(not _has_module("braket"), reason="Braket SDK not installed")
def test_braket_backend_runs() -> None:
    result = get_backend("braket_local").run(build_benchmark(n_qubits=3), shots=32)
    assert sum(result["counts"].values()) == 32


@pytest.mark.skipif(not _has_module("braket"), reason="Braket SDK not installed")
def test_braket_ghz_counts_use_expected_bitstrings() -> None:
    result = get_backend("braket_local").run(build_benchmark(n_qubits=3), shots=64)
    assert set(result["counts"]).issubset({"000", "111"})


def test_backend_structural_metrics_are_available() -> None:
    metrics = get_backend("cirq").structural_metrics(build_benchmark(n_qubits=3))
    assert "depth" in metrics


def test_missing_backend_dependency_error_mentions_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def block_cirq(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "cirq":
            raise ImportError("blocked")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", block_cirq)
    with pytest.raises(RuntimeError, match=r"quantum-backend-bench\[cirq\]"):
        CirqBackend().build_native_circuit(build_benchmark(n_qubits=2))
