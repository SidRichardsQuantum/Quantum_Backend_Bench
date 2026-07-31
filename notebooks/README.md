# Tutorial Notebooks

These notebooks use the public package API for local SDK comparison, translation, and verification. Shared artifact and display helpers live in `quantum_backend_bench.utils.notebook`.

## Notebooks

- `01_quickstart_cirq.ipynb`: run GHZ and a tiny smoke suite on Cirq.
- `02_compare_local_simulators.ipynb`: compare installed local SDK simulators on GHZ and QFT.
- `03_hamiltonian_simulation_case_study.ipynb`: vary qubits, evolution time, and Trotter steps.
- `04_compare_sdk_workflows.ipynb`: apply one export, execution, artifact, and verification workflow across installed Cirq, Qiskit Aer, PennyLane, and Braket adapters.
- `05_circuit_translation_workflow.ipynb`: translate and verify circuits across core SDK targets.
- `06_observable_hamiltonian_translation_workflow.ipynb`: translate weighted Pauli observables and Hamiltonians.
- `07_parameterized_workflow_translation.ipynb`: translate parameterized workflows and normalize results.
- `08_translation_migration_audit_workflow.ipynb`: inspect migration diagnostics, round trips, and supported boundaries.

## Suggested Install

```bash
python -m pip install -e ".[cirq,plot,notebooks]"
```

For the broader local SDK matrix:

```bash
python -m pip install -e ".[all,notebooks]"
```
