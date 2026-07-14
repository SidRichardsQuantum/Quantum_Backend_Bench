# Translation Examples

These fixtures exercise the SDK translation surface used by `quantum-bench translate`, `translate-hamiltonian`, `translate-workflow`, `translate-result`, and `group-pauli-terms`. They are intentionally small, static, and CI-friendly. The goal is stable semantic coverage, not large application examples. Neutral JSON fixtures use the v0.1 schemas documented in [`docs/SCHEMA.md`](../../docs/SCHEMA.md); regenerated neutral outputs include `schema_version`.

## Run the Corpus

```bash
python examples/translation/verify_examples.py
python examples/translation/update_expected.py --check
python scripts/check_translation_artifacts.py
```

Regenerate pinned outputs after intentional code-generation changes:

```bash
python examples/translation/update_expected.py
```

## Directory Roles

- Executable corpus: top-level circuit/Hamiltonian/workflow/result fixtures plus `accepted/`, `portable/`, `purpose_workflows/`, and `results/` are covered by `verify_examples.py` or focused tests.
- Generated expectations: `expected/`, `migration_audit/expected/`, and `roundtrip_audit/expected/` are committed regression artifacts. Update them only through their generator scripts after intentional output changes.
- Diagnostic-only fixtures: `rejected/` pins unsupported constructs and expected diagnostic categories.
- Roadmap-only fixtures: `roadmap/` is reserved for useful SDK intent that is deliberately excluded from executable verification until the neutral model and static importers support that purpose.

## Fixture Map

| Fixture | Layer | Source format | Main command | Why it exists |
| --- | --- | --- | --- | --- |
| `qiskit_registers.py` | circuit | `qiskit` | `translate --to-format cirq` | Static Qiskit registers and measurements. |
| `cirq_nested.py` | circuit | `cirq` | `translate --to-format qiskit_aer` | Static Cirq nesting and simple loop handling. |
| `pennylane_positional.py` | circuit | `pennylane` | `translate-check` or `translate --to-format braket_local` | PennyLane positional wire syntax. |
| `braket_local.py` | circuit | `braket` | `translate --to-format pennylane` | Braket LocalSimulator circuit construction syntax. |
| `accepted/qiskit_static_rotations.py` | circuit | `qiskit` | `translate --to-format cirq` | Realistic static constants, loops, rotations, entanglers, and measurements. |
| `accepted/cirq_measurement_keys.py` | circuit | `cirq` | `translate --to-format qiskit_aer` | Cirq measurement-key syntax normalized through neutral measurements. |
| `accepted/braket_probability_result_type.py` | circuit | `braket` | `translate --to-format pennylane` | Braket probability result-type target handling. |
| `accepted/qiskit_timing_annotations.py` | circuit | `qiskit` | `translate --to-format qiskit_aer --verify canonical` | Reset, barrier, and delay annotations preserved through the neutral timeline. |
| `accepted/openqasm_timing_annotations.qasm` | circuit | `openqasm` | `translate --to-format qiskit_aer --verify canonical` | OpenQASM import/export coverage for reset, barrier, and delay annotations. |
| `portable/custom_gate_decomposed_qiskit.py` | circuit | `qiskit` | `translate --to-format cirq` | Portable rewrite of an unsupported custom-gate fixture. |
| `portable/runtime_removed_qiskit.py` | circuit | `qiskit` | `translate --to-format cirq` | Portable rewrite of an unsupported provider-runtime fixture. |
| `ghz.qasm` | circuit | `openqasm` | `translate --to-format cirq` | OpenQASM import coverage. |
| `internal_ghz.json` | circuit | `internal-json` | `translate --to-format qiskit_aer` | Neutral circuit JSON import coverage. |
| `ising_hamiltonian.json` | observable/Hamiltonian | `pauli-json` | `translate-hamiltonian` | Neutral weighted Pauli-term source. |
| `qiskit_hamiltonian.py` | observable/Hamiltonian | `qiskit` | `translate-hamiltonian --to-format cirq` | Qiskit `SparsePauliOp` import coverage. |
| `cirq_hamiltonian.py` | observable/Hamiltonian | `cirq` | `translate-hamiltonian --to-format pennylane` | Cirq Pauli-expression import coverage. |
| `pennylane_hamiltonian.py` | observable/Hamiltonian | `pennylane` | `translate-hamiltonian --to-format braket_local` | PennyLane `qml.Hamiltonian` import coverage. |
| `braket_hamiltonian.py` | observable/Hamiltonian | `braket` | `translate-hamiltonian --to-format pauli-json` | Braket observable-term import coverage. |
| `parameterized_workflow.json` | workflow | `workflow-json` | `translate-workflow` | Parameterized circuit, bindings, measurements, execution wrapper, result object, and Pauli expectation coverage. |
| `accepted/pennylane_qnode_probabilities.py` | workflow | `pennylane` | `translate-workflow --to-format qiskit_aer` | PennyLane QNode-style local workflow with probability measurement. |
| `accepted/pennylane_qnode_observable.py` | workflow | `pennylane` | `translate-workflow --to-format qiskit_aer` | PennyLane QNode-style local workflow with Pauli expectation measurement. |
| `purpose_workflows/sampler_workflow.json` | workflow | `workflow-json` | `translate-workflow --to-format cirq` | Purpose-level sampler job represented in the current workflow schema. |
| `purpose_workflows/estimator_workflow.json` | workflow | `workflow-json` | `translate-workflow --to-format qiskit_aer` | Purpose-level Pauli expectation/estimator job. |
| `purpose_workflows/parameter_sweep_workflow.json` | workflow | `workflow-json` | `translate-workflow --to-format pennylane` | One representative binding point from a parameter sweep. |
| `purpose_workflows/qaoa_workflow.json` | workflow | `workflow-json` | `translate-workflow --to-format braket_local` | Compact QAOA-style line workflow with counts and expectation requests. |
| `qiskit_counts_result.json` | result | `qiskit-counts-json` | `translate-result` | Qiskit-style counts, including spaced bitstring normalization and backend metadata. |
| `cirq_counts_result.json` | result | `cirq-counts-json` | `translate-result` | Counts plus Cirq-style measurement-key metadata. |
| `pennylane_samples_result.json` | result | `pennylane-samples-json` | `translate-result` | Sample-list normalization to counts/probabilities. |
| `braket_counts_result.json` | result | `braket-counts-json` | `translate-result` | Braket-style `measurement_counts` normalization. |
| `results/qiskit_spaced_counts_no_shots.json` | result | `qiskit-counts-json` | `translate-result` | Shot-count inference from spaced Qiskit-style bitstrings. |
| `results/cirq_multi_key_counts.json` | result | `cirq-counts-json` | `translate-result` | Multiple measurement-key metadata preservation. |
| `results/pennylane_nested_samples.json` | result | `pennylane-samples-json` | `translate-result` | Nested sample-list normalization. |
| `results/braket_counts_fallback.json` | result | `braket-counts-json` | `translate-result` | Braket-compatible counts fallback shape. |
| `migration_audit/qiskit_static_bell.py` | audit | `qiskit` | `translate-check --to-format cirq --explain` | Target-aware migration-audit report examples. |
| `roundtrip_audit/expected/` | audit | report artifacts | `translate --verify exact --save-report` | Round-trip verification report style examples. |

## Expected Outputs

`expected/` contains generated golden outputs for representative circuit, Hamiltonian, and workflow translations. These files intentionally duplicate generated source so formatting and code-generation drift are caught by tests.

## Example Directories

- `accepted/`: realistic snippets that stay within today's supported static subset.
- `migration_audit/`: source plus expected JSON/Markdown `translate-check` audit reports.
- `purpose_workflows/`: workflow-json examples that encode sampler, estimator, parameter-sweep-point, and QAOA-style intent.
- `portable/`: supported rewrites paired with rejected patterns.
- `results/`: result-normalization edge cases.
- `roundtrip_audit/`: committed semantic round-trip report examples.
- `roadmap/`: useful SDK intent examples that are intentionally not verified until the neutral model supports them.

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
| `dynamic_delay_qiskit.py` | Nonliteral delay duration. |
| `dynamic_reset_qiskit.py` | Nonliteral reset target. |

## Roadmap Fixtures

`accepted/braket_expectation_result_type.py` covers a Braket expectation-value workflow shape with canonical workflow reimport verification.

## Notes on Redundancy

Some fixtures are intentionally similar because they cover different input formats for the same neutral semantics. For example, `ghz.qasm` and `internal_ghz.json` both represent compact GHZ-style circuits, but they exercise different import paths. The counts-result fixtures are also intentionally small, but each now includes one SDK-specific shape or metadata field.
