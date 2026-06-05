# Translation Examples

These fixtures exercise the SDK translation surface used by `quantum-bench translate`, `translate-hamiltonian`, `translate-workflow`, `translate-result`, and `group-pauli-terms`. They are intentionally small, static, and CI-friendly. The goal is stable semantic coverage, not large application examples.

## Run the Corpus

```bash
python examples/translation/verify_examples.py
python examples/translation/update_expected.py --check
```

Regenerate pinned outputs after intentional code-generation changes:

```bash
python examples/translation/update_expected.py
```

## Fixture Map

| Fixture | Layer | Source format | Main command | Why it exists |
| --- | --- | --- | --- | --- |
| `qiskit_registers.py` | circuit | `qiskit` | `translate --to-format cirq` | Static Qiskit registers and measurements. |
| `cirq_nested.py` | circuit | `cirq` | `translate --to-format qiskit_aer` | Static Cirq nesting and simple loop handling. |
| `pennylane_positional.py` | circuit | `pennylane` | `translate-check` or `translate --to-format braket_local` | PennyLane positional wire syntax. |
| `braket_local.py` | circuit | `braket` | `translate --to-format pennylane` | Braket LocalSimulator circuit construction syntax. |
| `ghz.qasm` | circuit | `openqasm` | `translate --to-format cirq` | OpenQASM import coverage. |
| `internal_ghz.json` | circuit | `internal-json` | `translate --to-format qiskit_aer` | Neutral circuit JSON import coverage. |
| `ising_hamiltonian.json` | observable/Hamiltonian | `pauli-json` | `translate-hamiltonian` | Neutral weighted Pauli-term source. |
| `qiskit_hamiltonian.py` | observable/Hamiltonian | `qiskit` | `translate-hamiltonian --to-format cirq` | Qiskit `SparsePauliOp` import coverage. |
| `cirq_hamiltonian.py` | observable/Hamiltonian | `cirq` | `translate-hamiltonian --to-format pennylane` | Cirq Pauli-expression import coverage. |
| `pennylane_hamiltonian.py` | observable/Hamiltonian | `pennylane` | `translate-hamiltonian --to-format braket_local` | PennyLane `qml.Hamiltonian` import coverage. |
| `braket_hamiltonian.py` | observable/Hamiltonian | `braket` | `translate-hamiltonian --to-format pauli-json` | Braket observable-term import coverage. |
| `parameterized_workflow.json` | workflow | `workflow-json` | `translate-workflow` | Parameterized circuit, bindings, measurements, execution wrapper, result object, and Pauli expectation coverage. |
| `qiskit_counts_result.json` | result | `qiskit-counts-json` | `translate-result` | Qiskit-style counts, including spaced bitstring normalization and backend metadata. |
| `cirq_counts_result.json` | result | `cirq-counts-json` | `translate-result` | Counts plus Cirq-style measurement-key metadata. |
| `pennylane_samples_result.json` | result | `pennylane-samples-json` | `translate-result` | Sample-list normalization to counts/probabilities. |
| `braket_counts_result.json` | result | `braket-counts-json` | `translate-result` | Braket-style `measurement_counts` normalization. |

## Expected Outputs

`expected/` contains generated golden outputs for representative circuit, Hamiltonian, and workflow translations. These files intentionally duplicate generated source so formatting and code-generation drift are caught by tests.

## Rejected Fixtures

`rejected/` contains unsupported static-analysis cases. They are not user examples to copy; they pin diagnostics for unsupported dynamic or non-Pauli behavior.

| Fixture | Rejection category |
| --- | --- |
| `conditional_qiskit.py` | Classical control / conditional execution. |
| `custom_gate_qiskit.py` | Custom or opaque gate construction. |
| `dynamic_wires_pennylane.py` | Dynamic wire selection. |
| `function_built_cirq.py` | Circuit construction hidden behind runtime function calls. |
| `non_range_loop_qiskit.py` | Non-static loop iteration. |
| `runtime_call_qiskit.py` | Runtime value used during circuit construction. |
| `wire_arithmetic_qiskit.py` | Nonliteral wire arithmetic. |
| `dynamic_hamiltonian_coeff_qiskit.py` | Nonliteral Hamiltonian coefficient. |
| `non_pauli_hamiltonian_qiskit.py` | Non-Pauli operator content. |
| `symbolic_hamiltonian_pennylane.py` | Symbolic Hamiltonian coefficient. |

## Notes on Redundancy

Some fixtures are intentionally similar because they cover different input formats for the same neutral semantics. For example, `ghz.qasm` and `internal_ghz.json` both represent compact GHZ-style circuits, but they exercise different import paths. The counts-result fixtures are also intentionally small, but each now includes one SDK-specific shape or metadata field.
