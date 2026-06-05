from __future__ import annotations

import argparse
from pathlib import Path

from quantum_backend_bench.core.circuit_translate import translate_circuit_source
from quantum_backend_bench.core.observable_translate import translate_hamiltonian_source
from quantum_backend_bench.core.workflow_translate import translate_workflow_source

ROOT = Path(__file__).resolve().parent
CIRCUIT_CASES = [
    ("qiskit_registers.py", "qiskit", "cirq", "expected/qiskit_registers_to_cirq.py"),
    ("cirq_nested.py", "cirq", "qiskit_aer", "expected/cirq_nested_to_qiskit.py"),
    ("ghz.qasm", "openqasm", "pennylane", "expected/ghz_qasm_to_pennylane.py"),
]
WORKFLOW_CASES = [
    (
        "parameterized_workflow.json",
        "workflow-json",
        "qiskit_aer",
        "expected/parameterized_workflow_to_qiskit.py",
    ),
    (
        "parameterized_workflow.json",
        "workflow-json",
        "cirq",
        "expected/parameterized_workflow_to_cirq.py",
    ),
    (
        "parameterized_workflow.json",
        "workflow-json",
        "pennylane",
        "expected/parameterized_workflow_to_pennylane.py",
    ),
    (
        "parameterized_workflow.json",
        "workflow-json",
        "braket_local",
        "expected/parameterized_workflow_to_braket.py",
    ),
]
HAMILTONIAN_CASES = [
    (
        "ising_hamiltonian.json",
        "pauli-json",
        "qiskit_aer",
        "expected/ising_hamiltonian_to_qiskit.py",
    ),
    ("qiskit_hamiltonian.py", "qiskit", "cirq", "expected/qiskit_hamiltonian_to_cirq.py"),
    ("cirq_hamiltonian.py", "cirq", "pennylane", "expected/cirq_hamiltonian_to_pennylane.py"),
    (
        "pennylane_hamiltonian.py",
        "pennylane",
        "braket_local",
        "expected/pennylane_hamiltonian_to_braket.py",
    ),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate translation expected outputs.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero if generated outputs differ instead of updating files.",
    )
    args = parser.parse_args(argv)

    changed: list[Path] = []
    for source_name, from_format, to_format, expected_name in CIRCUIT_CASES:
        source = (ROOT / source_name).read_text(encoding="utf-8")
        result = translate_circuit_source(
            source, from_format=from_format, to_format=to_format, verify="exact"
        )
        expected_path = ROOT / expected_name
        if args.check:
            existing = expected_path.read_text(encoding="utf-8")
            if existing != result.source:
                changed.append(expected_path)
        else:
            expected_path.write_text(result.source, encoding="utf-8")
            print(f"updated {expected_path.relative_to(ROOT)}")
    for source_name, from_format, to_format, expected_name in HAMILTONIAN_CASES:
        source = (ROOT / source_name).read_text(encoding="utf-8")
        result = translate_hamiltonian_source(
            source, from_format=from_format, to_format=to_format, verify="matrix"
        )
        expected_path = ROOT / expected_name
        if args.check:
            existing = expected_path.read_text(encoding="utf-8")
            if existing != result.source:
                changed.append(expected_path)
        else:
            expected_path.write_text(result.source, encoding="utf-8")
            print(f"updated {expected_path.relative_to(ROOT)}")
    for source_name, from_format, to_format, expected_name in WORKFLOW_CASES:
        source = (ROOT / source_name).read_text(encoding="utf-8")
        result = translate_workflow_source(
            source, from_format=from_format, to_format=to_format, verify="canonical"
        )
        expected_path = ROOT / expected_name
        if args.check:
            existing = expected_path.read_text(encoding="utf-8")
            if existing != result.source:
                changed.append(expected_path)
        else:
            expected_path.write_text(result.source, encoding="utf-8")
            print(f"updated {expected_path.relative_to(ROOT)}")

    if changed:
        for path in changed:
            print(f"out of date: {path.relative_to(ROOT)}")
        return 1
    if args.check:
        print("translation expected outputs are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
