# Tutorial Notebooks

These notebooks are succinct package-client examples. They use the public package
API to run local, credential-free quantum simulator benchmarks. Each notebook opens
with the problem, quantum-advantage scope, and variable definitions, then uses
readable tables, useful plots, saved artifacts, and verification checks. Shared
notebook plumbing lives in `quantum_backend_bench.utils.notebook` so repeated
artifact, ket-formatting, top-state, and verification code stays consistent.

## Notebooks

- `01_quickstart_cirq.ipynb`: run GHZ and a tiny smoke suite on Cirq.
- `02_compare_local_simulators.ipynb`: compare installed local simulator SDKs on
  GHZ and QFT.
- `03_hamiltonian_simulation_case_study.ipynb`: vary qubits, evolution time,
  and Trotter steps for a small Ising-style Hamiltonian simulation study.
- `04_sdk_cirq_workflow.ipynb` through `08_sdk_qutip_workflow.ipynb`: compact
  SDK export, execution, plotting, artifact, and verification workflows.
- `09_circuit_translation_workflow.ipynb`: all-target local SDK circuit translation with native diagram comparison, reports, runner output, and diagnostics.
- `10_observable_hamiltonian_translation_workflow.ipynb`: Pauli observable and Hamiltonian translation across local SDK formats with canonical verification.
- `11_parameterized_workflow_translation.ipynb`: parameterized workflow translation across local SDK targets with canonical and semantic verification, executable neutral results, result normalization, Pauli grouping, and purpose-level workflow examples.
- `12_translation_migration_audit_workflow.ipynb`: target-aware migration audits, semantic contracts, accepted/rejected/portable examples, round-trip reports, result edge cases, purpose workflows, and roadmap-only boundaries.

## Suggested Install

```bash
python -m pip install -e ".[cirq,plot,notebooks]"
```

For the broader local comparison notebook, install the optional SDK extras you want
to compare, for example:

```bash
python -m pip install -e ".[all,notebooks]"
```

## SDK Workflows

- `04_sdk_cirq_workflow.ipynb`: circuit export and local Cirq execution workflow.
- `05_sdk_qiskit_workflow.ipynb`: circuit export and Qiskit Aer execution workflow.
- `06_sdk_pennylane_workflow.ipynb`: circuit export and PennyLane execution workflow.
- `07_sdk_braket_workflow.ipynb`: circuit export and Braket LocalSimulator workflow.
- `08_sdk_qutip_workflow.ipynb`: exact-probability workflow using the internal statevector path.
- `09_circuit_translation_workflow.ipynb`: translate supported static circuits to Qiskit Aer, Cirq, PennyLane, and Braket LocalSimulator, compare native diagrams, save reports, emit runnable scripts, and inspect unsupported diagnostics.
- `10_observable_hamiltonian_translation_workflow.ipynb`: translate weighted Pauli observables and Hamiltonians to Qiskit Aer, Cirq, PennyLane, Braket LocalSimulator, and neutral JSON, then verify canonical Pauli terms.
- `11_parameterized_workflow_translation.ipynb`: translate one parameterized workflow to Qiskit Aer, Cirq, PennyLane, and Braket LocalSimulator; save generated source/report artifacts; verify canonical structure or neutral result semantics; normalize SDK-shaped results; group Pauli terms for measurement planning; and compare purpose-level workflow fixtures.
- `12_translation_migration_audit_workflow.ipynb`: inspect source portability with `semantic_contract` and `migration_audit`, compare accepted/rejected/portable fixtures, save a verified round-trip report, normalize result edge cases, and keep roadmap-only examples separate from current support.
