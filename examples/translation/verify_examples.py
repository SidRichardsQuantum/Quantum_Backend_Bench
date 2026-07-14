from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum_backend_bench.core.circuit_translate import translate_circuit_source  # noqa: E402
from quantum_backend_bench.core.observable_translate import (  # noqa: E402
    translate_hamiltonian_source,
)
from quantum_backend_bench.core.workflow_translate import (  # noqa: E402
    normalize_result_source,
    translate_workflow_source,
)

CIRCUIT_CASES = [
    ("qiskit_registers.py", "qiskit", "cirq"),
    ("cirq_nested.py", "cirq", "qiskit_aer"),
    ("pennylane_positional.py", "pennylane", "braket_local"),
    ("braket_local.py", "braket", "pennylane"),
    ("ghz.qasm", "openqasm", "cirq"),
    ("internal_ghz.json", "internal-json", "qiskit_aer"),
    ("accepted/qiskit_static_rotations.py", "qiskit", "cirq"),
    ("accepted/cirq_measurement_keys.py", "cirq", "qiskit_aer"),
    ("accepted/braket_probability_result_type.py", "braket", "pennylane"),
    ("portable/custom_gate_decomposed_qiskit.py", "qiskit", "cirq"),
    ("portable/runtime_removed_qiskit.py", "qiskit", "cirq"),
]
WORKFLOW_CASES = [
    ("parameterized_workflow.json", "workflow-json", "qiskit_aer"),
    ("parameterized_workflow.json", "workflow-json", "cirq"),
    ("parameterized_workflow.json", "workflow-json", "pennylane"),
    ("parameterized_workflow.json", "workflow-json", "braket_local"),
    ("accepted/pennylane_qnode_probabilities.py", "pennylane", "qiskit_aer"),
    ("accepted/pennylane_qnode_observable.py", "pennylane", "qiskit_aer"),
    ("accepted/braket_expectation_result_type.py", "braket", "qiskit_aer"),
    ("purpose_workflows/sampler_workflow.json", "workflow-json", "cirq"),
    ("purpose_workflows/estimator_workflow.json", "workflow-json", "qiskit_aer"),
    ("purpose_workflows/parameter_sweep_workflow.json", "workflow-json", "pennylane"),
    ("purpose_workflows/qaoa_workflow.json", "workflow-json", "braket_local"),
]
HAMILTONIAN_CASES = [
    ("ising_hamiltonian.json", "pauli-json", "qiskit_aer"),
    ("qiskit_hamiltonian.py", "qiskit", "cirq"),
    ("cirq_hamiltonian.py", "cirq", "pennylane"),
    ("pennylane_hamiltonian.py", "pennylane", "braket_local"),
    ("braket_hamiltonian.py", "braket", "pauli-json"),
]
RESULT_CASES = [
    ("qiskit_counts_result.json", "qiskit-counts-json"),
    ("cirq_counts_result.json", "cirq-counts-json"),
    ("pennylane_samples_result.json", "pennylane-samples-json"),
    ("braket_counts_result.json", "braket-counts-json"),
    ("results/qiskit_spaced_counts_no_shots.json", "qiskit-counts-json"),
    ("results/cirq_multi_key_counts.json", "cirq-counts-json"),
    ("results/pennylane_nested_samples.json", "pennylane-samples-json"),
    ("results/braket_counts_fallback.json", "braket-counts-json"),
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
    for filename, from_format in RESULT_CASES:
        result = normalize_result_source(
            (ROOT / filename).read_text(encoding="utf-8"),
            from_format=from_format,
        )
        if '"probabilities"' not in result.source:
            print(f"FAILED {filename} -> result-json")
            return 1
        print(f"PASS {filename} -> result-json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
