# Qiskit Static Bell to Cirq Round Trip

- from: `qiskit`
- to: `cirq`
- guarantee: Lossless only within the declared neutral semantic subset.
- verification: `exact`
- passed: `True`
- details: Semantic verification passed: exact probabilities TVD=0.0 with tolerance=1e-09.

## Diagnostics
- `translation.scope`: Static circuit translation preserves supported gates, measurements, and supported neutral annotations.
- `translation.caveat.measurement_order`: SDKs may display measurement bitstrings with different endian conventions; verification compares neutral measurement probabilities.
- `translation.caveat.braket_probability`: Braket output emits probability targets for circuit construction; --include-runner uses LocalSimulator measurement counts.
- `translation.caveat.pennylane_sampling`: PennyLane output is a QNode returning qml.sample; runner output wraps it with qml.set_shots.
- `translation.caveat.qibo_numpy`: Qibo runner output explicitly constructs the bundled local NumPy backend.
- `translation.caveat.controlled_phase`: Controlled-phase operations are mapped through each SDK's closest native phase convention and should be verified for nontrivial angles.
- `translation.verify.passed`: Semantic verification passed: exact probabilities TVD=0.0 with tolerance=1e-09.
