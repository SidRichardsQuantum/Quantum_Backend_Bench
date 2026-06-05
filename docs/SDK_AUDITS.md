# SDK Audits

This page is generated from committed reference artifacts under `../examples/reference_results/sdk_audits_2026-06-05/`. The artifacts demonstrate the free local SDK audit commands without depending on optional SDK availability during documentation builds.

## Reproduction Commands

```bash
quantum-bench sdk-parity --save-json artifacts/sdk_parity.json --save-csv artifacts/sdk_parity.csv --save-report artifacts/sdk_parity.md
quantum-bench noise-audit --save-json artifacts/noise_matrix.json --save-csv artifacts/noise_matrix.csv --save-report artifacts/noise_matrix.md
quantum-bench roundtrip-audit --targets cirq qiskit_aer pennylane braket_local --include-hamiltonian --include-workflow --save-json artifacts/roundtrip_audit.json --save-csv artifacts/roundtrip_audit.csv --save-report artifacts/roundtrip_audit.md
```

## SDK Parity Scorecard

*Raw assets:* [`sdk_parity.json`](pages/assets/sdk_audits/sdk_parity.json), [`sdk_parity.csv`](pages/assets/sdk_audits/sdk_parity.csv), [`sdk_parity.md`](pages/assets/sdk_audits/sdk_parity.md).

| SDK | circuits | workflows | Pauli terms | result objects | grouping | noise models |
| --- | --- | --- | --- | --- | --- | --- |
| braket_local | yes | yes | yes | yes | yes | none |
| cirq | yes | yes | yes | yes | yes | amplitude_damping, bit_flip, depolarizing, phase_flip, readout_error |
| pennylane | yes | yes | yes | yes | yes | amplitude_damping, bit_flip, depolarizing, phase_flip, readout_error |
| qiskit_aer | yes | yes | yes | yes | yes | amplitude_damping, bit_flip, depolarizing, phase_flip, readout_error |
| qutip | no | no | no | no | no | none |

## Noise Model Matrix

*Raw assets:* [`noise_matrix.json`](pages/assets/sdk_audits/noise_matrix.json), [`noise_matrix.csv`](pages/assets/sdk_audits/noise_matrix.csv), [`noise_matrix.md`](pages/assets/sdk_audits/noise_matrix.md).*

| backend | depolarizing | bit_flip | phase_flip | amplitude_damping | readout_error | scope |
| --- | --- | --- | --- | --- | --- | --- |
| braket_local | not injected | not injected | not injected | not injected | not injected | reported only; noise is not injected by this project |
| cirq | implemented | implemented | implemented | implemented | implemented | project-injected local model |
| cudaq | not injected | not injected | not injected | not injected | not injected | reported only; noise is not injected by this project |
| pennylane | implemented | implemented | implemented | implemented | implemented | project-injected local model |
| pyquil_qvm | not injected | not injected | not injected | not injected | not injected | reported only; noise is not injected by this project |
| qiskit_aer | implemented | implemented | implemented | implemented | implemented | project-injected local model |
| qutip | not injected | not injected | not injected | not injected | not injected | reported only; noise is not injected by this project |

## Round-Trip Translation Audit

*Raw assets:* [`roundtrip_audit.json`](pages/assets/sdk_audits/roundtrip_audit.json), [`roundtrip_audit.csv`](pages/assets/sdk_audits/roundtrip_audit.csv), [`roundtrip_audit.md`](pages/assets/sdk_audits/roundtrip_audit.md).*

| audit | target | rows | passed |
| --- | --- | ---: | --- |
| circuit_roundtrip | braket_local | 4 | yes |
| circuit_roundtrip | cirq | 4 | yes |
| circuit_roundtrip | pennylane | 4 | yes |
| circuit_roundtrip | qiskit_aer | 4 | yes |
| hamiltonian_roundtrip | braket_local | 1 | yes |
| hamiltonian_roundtrip | cirq | 1 | yes |
| hamiltonian_roundtrip | pennylane | 1 | yes |
| hamiltonian_roundtrip | qiskit_aer | 1 | yes |
| workflow_roundtrip | braket_local | 1 | yes |
| workflow_roundtrip | cirq | 1 | yes |
| workflow_roundtrip | pennylane | 1 | yes |
| workflow_roundtrip | qiskit_aer | 1 | yes |

## Interpretation

- `sdk-parity` is a capability scorecard, not an execution benchmark.
- `noise-audit` reports which local adapters receive project-injected noise models. Noise models are adapter-specific and should not be treated as physically identical.
- `roundtrip-audit` verifies neutral circuit, Pauli Hamiltonian, and parameterized workflow semantics through SDK source generation and reimport.
