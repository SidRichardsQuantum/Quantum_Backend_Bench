from __future__ import annotations

from pathlib import Path

from quantum_backend_bench.core.circuit_translate import translate_circuit_source
from quantum_backend_bench.core.observable_translate import translate_hamiltonian_source
from quantum_backend_bench.core.workflow_translate import translate_workflow_source

ROOT = Path(__file__).resolve().parent
CIRCUIT_CASES = [
    ("qiskit_registers.py", "qiskit", "cirq"),
    ("cirq_nested.py", "cirq", "qiskit_aer"),
    ("pennylane_positional.py", "pennylane", "braket_local"),
    ("braket_local.py", "braket", "pennylane"),
    ("ghz.qasm", "openqasm", "cirq"),
    ("internal_ghz.json", "internal-json", "qiskit_aer"),
]
WORKFLOW_CASES = [
    ("parameterized_workflow.json", "workflow-json", "qiskit_aer"),
    ("parameterized_workflow.json", "workflow-json", "cirq"),
    ("parameterized_workflow.json", "workflow-json", "pennylane"),
    ("parameterized_workflow.json", "workflow-json", "braket_local"),
]
HAMILTONIAN_CASES = [
    ("ising_hamiltonian.json", "pauli-json", "qiskit_aer"),
    ("qiskit_hamiltonian.py", "qiskit", "cirq"),
    ("cirq_hamiltonian.py", "cirq", "pennylane"),
    ("pennylane_hamiltonian.py", "pennylane", "braket_local"),
    ("braket_hamiltonian.py", "braket", "pauli-json"),
]


def main() -> int:
    for filename, from_format, to_format in CIRCUIT_CASES:
        result = translate_circuit_source(
            (ROOT / filename).read_text(encoding="utf-8"),
            from_format=from_format,
            to_format=to_format,
            verify="exact",
        )
        if result.verification is None or not result.verification.passed:
            print(f"FAILED {filename} -> {to_format}")
            return 1
        print(f"PASS {filename} -> {to_format}")
    for filename, from_format, to_format in HAMILTONIAN_CASES:
        result = translate_hamiltonian_source(
            (ROOT / filename).read_text(encoding="utf-8"),
            from_format=from_format,
            to_format=to_format,
            verify="matrix",
        )
        if result.verification is None or not result.verification.passed:
            print(f"FAILED {filename} -> {to_format}")
            return 1
        print(f"PASS {filename} -> {to_format}")
    for filename, from_format, to_format in WORKFLOW_CASES:
        result = translate_workflow_source(
            (ROOT / filename).read_text(encoding="utf-8"),
            from_format=from_format,
            to_format=to_format,
            verify="canonical",
        )
        if result.verification is None or not result.verification.passed:
            print(f"FAILED {filename} -> {to_format}")
            return 1
        print(f"PASS {filename} -> {to_format}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
