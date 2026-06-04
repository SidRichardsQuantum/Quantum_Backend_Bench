# Circuit Translation

`quantum-bench translate` converts supported circuit descriptions through the package's neutral `InternalCircuit` model. It is intended for circuit portability, not arbitrary Python program migration.

## Supported Inputs

- `openqasm`: the OpenQASM 2/3 subset emitted by this project
- `internal-json`: the project's neutral circuit JSON format
- `qiskit`: static `QuantumCircuit` construction snippets
- `cirq`: static `cirq.Circuit` snippets using line qubits
- `pennylane`: static QNode-style operation snippets
- `braket`: static `braket.circuits.Circuit` snippets

Use `--from-format auto` for basic detection, or set `--from-format` explicitly for predictable CI behavior.

## Supported Outputs

SDK outputs are limited to free local Python SDK APIs for now:

- `cirq`
- `qiskit_aer` circuit source using Qiskit `QuantumCircuit`
- `pennylane`
- `braket_local`

Neutral outputs are also available:

- `internal-json`
- `openqasm`

## Examples

Translate OpenQASM to Cirq:

```bash
quantum-bench translate artifacts/ghz.qasm \
  --from-format openqasm \
  --to-format cirq \
  --output artifacts/ghz_cirq.py
```

Translate a static Qiskit snippet to PennyLane and verify exact probabilities:

```bash
quantum-bench translate examples/qiskit_circuit.py \
  --from-format qiskit \
  --to-format pennylane \
  --verify exact \
  --output artifacts/circuit_pennylane.py
```

Use sample-based verification when an exact comparison is too strict for the workflow:

```bash
quantum-bench translate examples/braket_circuit.py \
  --from-format braket \
  --to-format qiskit_aer \
  --verify samples \
  --sample-shots 4096 \
  --verify-tolerance 0.02
```

Inspect a source file before writing translated output and save a CI-readable report:

```bash
quantum-bench translate-check examples/translation/qiskit_registers.py \
  --from-format qiskit \
  --save-report artifacts/translation_check.json

quantum-bench translate-check examples/translation/qiskit_registers.py \
  --from-format qiskit \
  --json
```

Save a translation report containing diagnostics and verification metrics:

```bash
quantum-bench translate examples/translation/ghz.qasm \
  --from-format openqasm \
  --to-format cirq \
  --verify exact \
  --save-report artifacts/translation_report.json
```

Emit a runnable local script as well as circuit construction code:

```bash
quantum-bench translate examples/translation/ghz.qasm \
  --from-format openqasm \
  --to-format cirq \
  --include-runner \
  --runner-shots 1024 \
  --output artifacts/ghz_cirq_runner.py
```

## Tutorial Notebook

`notebooks/09_circuit_translation_workflow.ipynb` provides the end-to-end local workflow: import one static Qiskit circuit, preflight it, draw SDK-native diagrams for Qiskit Aer, Cirq, PennyLane, and Braket LocalSimulator, translate to all four local SDK targets, verify exact probabilities, save per-target source artifacts and a combined report, emit a runnable Cirq script, and inspect unsupported diagnostics.

## Supported Gates

The first supported gate set matches the existing internal circuit model:

- Single-qubit gates: `H`, `X`, `Y`, `Z`, `S`, `T`
- Rotations: `RX`, `RY`, `RZ` with static numeric parameters
- Two-qubit gates: `CNOT`, `CZ`, `SWAP`
- Controlled phase: `CPHASE`
- Measurements over static integer wires

## Static Python Support

The Python snippet importers support static circuit construction only. They can resolve:

- numeric constants such as `theta = 0.25`
- integer constants such as `n = 3`
- simple loops such as `for i in range(n): circuit.h(i)`
- static wire lists such as `[0, 1]`

Unsupported constructs produce structured diagnostics and fail instead of rewriting approximately. Unsupported examples include dynamic parameters from function calls, nonliteral wire expressions, custom gates, classical control, provider runtime calls, transpiler settings, and arbitrary result-processing code.

## Reports

`--save-report` writes JSON for both `translate` and `translate-check`. Reports include detected formats, diagnostics, gate inventory for checks, verification total variation distance for translations, and supported outputs. These reports are intended for CI and migration audits.

## Verification

`--verify exact` reimports the generated circuit source and compares exact measurement probabilities with total variation distance.

`--verify samples` samples both neutral distributions with a deterministic local sampler and compares the sampled distributions. Use `--sample-shots` and `--verify-tolerance` to tune this check.

A failed verification exits with status 1. The translated source is still produced so users can inspect it, but the command reports the failed semantic check.

## Caveats

Translation reports include warning diagnostics for backend-specific behavior that users should review: measurement bit ordering, Braket probability targets versus measurement counts, PennyLane QNode sampling, and controlled-phase conventions. Exact verification compares neutral measurement probabilities and is the recommended guardrail for these caveats.

## Golden Outputs

Expected generated outputs for selected fixtures live in `examples/translation/expected/`. Regenerate them intentionally after codegen changes:

```bash
python examples/translation/update_expected.py
```

Check that committed expected outputs are current:

```bash
python examples/translation/update_expected.py --check
```
