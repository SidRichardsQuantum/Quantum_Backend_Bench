# Roundtrip Audit

- rows: `30`
- passed: `True`

| audit | target | case | status | verification_mode | total_variation_distance | canonical_match | statevector_distance | details | detected_format | expectation_max_abs_error | expectation_tolerance | measurements | operations | result_schema_valid | terms | tolerance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| circuit_roundtrip | cirq | ghz | passed | exact | 0 | - | - | - | cirq | - | - | - | 3 | - | - | 1e-09 |
| circuit_roundtrip | cirq | qft | passed | exact | 0 | - | - | - | cirq | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | cirq | bernstein-vazirani | passed | exact | 0 | - | - | - | cirq | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | cirq | gate-coverage | passed | exact | 0 | - | - | - | cirq | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | qiskit_aer | ghz | passed | exact | 0 | - | - | - | qiskit | - | - | - | 3 | - | - | 1e-09 |
| circuit_roundtrip | qiskit_aer | qft | passed | exact | 0 | - | - | - | qiskit | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | qiskit_aer | bernstein-vazirani | passed | exact | 0 | - | - | - | qiskit | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | qiskit_aer | gate-coverage | passed | exact | 0 | - | - | - | qiskit | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | pennylane | ghz | passed | exact | 0 | - | - | - | pennylane | - | - | - | 3 | - | - | 1e-09 |
| circuit_roundtrip | pennylane | qft | passed | exact | 0 | - | - | - | pennylane | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | pennylane | bernstein-vazirani | passed | exact | 0 | - | - | - | pennylane | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | pennylane | gate-coverage | passed | exact | 0 | - | - | - | pennylane | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | braket_local | ghz | passed | exact | 0 | - | - | - | braket | - | - | - | 3 | - | - | 1e-09 |
| circuit_roundtrip | braket_local | qft | passed | exact | 0 | - | - | - | braket | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | braket_local | bernstein-vazirani | passed | exact | 0 | - | - | - | braket | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | braket_local | gate-coverage | passed | exact | 0 | - | - | - | braket | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | qibo_numpy | ghz | passed | exact | 0 | - | - | - | qibo | - | - | - | 3 | - | - | 1e-09 |
| circuit_roundtrip | qibo_numpy | qft | passed | exact | 0 | - | - | - | qibo | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | qibo_numpy | bernstein-vazirani | passed | exact | 0 | - | - | - | qibo | - | - | - | 7 | - | - | 1e-09 |
| circuit_roundtrip | qibo_numpy | gate-coverage | passed | exact | 0 | - | - | - | qibo | - | - | - | 7 | - | - | 1e-09 |
| hamiltonian_roundtrip | cirq | pauli_hamiltonian | passed | - | - | - | - | Canonical Pauli-term verification passed. | cirq | - | - | - | - | - | 3 | - |
| hamiltonian_roundtrip | qiskit_aer | pauli_hamiltonian | passed | - | - | - | - | Canonical Pauli-term verification passed. | qiskit | - | - | - | - | - | 3 | - |
| hamiltonian_roundtrip | pennylane | pauli_hamiltonian | passed | - | - | - | - | Canonical Pauli-term verification passed. | pennylane | - | - | - | - | - | 3 | - |
| hamiltonian_roundtrip | braket_local | pauli_hamiltonian | passed | - | - | - | - | Canonical Pauli-term verification passed. | braket | - | - | - | - | - | 3 | - |
| hamiltonian_roundtrip | qibo_numpy | pauli_hamiltonian | passed | - | - | - | - | Canonical Pauli-term verification passed. | qibo | - | - | - | - | - | 3 | - |
| workflow_roundtrip | cirq | parameterized_expectation_workflow | passed | canonical | - | True | - | Canonical workflow verification passed. | cirq | - | - | 3 | 3 | - | - | 0 |
| workflow_roundtrip | qiskit_aer | parameterized_expectation_workflow | passed | canonical | - | True | - | Canonical workflow verification passed. | qiskit | - | - | 3 | 3 | - | - | 0 |
| workflow_roundtrip | pennylane | parameterized_expectation_workflow | passed | canonical | - | True | - | Canonical workflow verification passed. | pennylane | - | - | 3 | 3 | - | - | 0 |
| workflow_roundtrip | braket_local | parameterized_expectation_workflow | passed | canonical | - | True | - | Canonical workflow verification passed. | braket | - | - | 3 | 3 | - | - | 0 |
| workflow_roundtrip | qibo_numpy | parameterized_expectation_workflow | passed | canonical | - | True | - | Canonical workflow verification passed. | qibo | - | - | 3 | 3 | - | - | 0 |
