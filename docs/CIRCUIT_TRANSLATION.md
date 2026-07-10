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

The JSON neutral formats are versioned in `docs/SCHEMA.md`: `internal-circuit`, `pauli-json`, `workflow-json`, and `result-json` currently use `schema_version: "0.1"`.

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

quantum-bench translate-check examples/translation/qiskit_registers.py \
  --from-format qiskit \
  --to-format cirq \
  --explain

quantum-bench translate-check examples/translation/qiskit_registers.py \
  --from-format qiskit \
  --to-format cirq \
  --save-markdown artifacts/translation_check.md
```

## Semantic Contract and Migration Audit

Translation commands are lossless only within the declared neutral semantic subset. Saved reports include a `semantic_contract` object that lists preserved semantics, syntax rewrites, rejected constructs, behavior that is not modeled, verification modes, and the free local SDK target scope. This makes the translation promise explicit for CI and migration reviews.

`translate-check --to-format ... --explain` adds a target-aware `migration_audit` for circuit sources. It reports the supported source/target status, gate inventory, preserved circuit semantics, SDK syntax rewrites, constructs that would be rejected if present, behavior outside the model, and the recommended verification mode. This is a preflight audit; it does not broaden the supported subset or attempt approximate Python program migration.

Save a translation report containing diagnostics and verification metrics:

```bash
quantum-bench translate examples/translation/ghz.qasm \
  --from-format openqasm \
  --to-format cirq \
  --verify exact \
  --save-report artifacts/translation_report.json
```

Translate one source to all selected local SDK targets, neutral `internal-json`, per-target reports, a combined JSON report, and a compact Markdown summary:

```bash
quantum-bench translate-all examples/translation/qiskit_registers.py \
  --from-format qiskit \
  --output-dir artifacts/qiskit_registers_all

quantum-bench translate-all examples/translation/qiskit_registers.py \
  --from-format qiskit \
  --targets cirq qiskit_aer \
  --output-dir artifacts/qiskit_registers_subset \
  --fail-on-verification
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

## Observable and Hamiltonian Translation

`translate-hamiltonian` and `translate-observable` extend SDK translation beyond circuits for the first safe semantic layer: weighted sums of Pauli `I`, `X`, `Y`, and `Z` products. Observables are represented as the single-term case of the same neutral model.

Supported inputs:

- `pauli-json`: neutral weighted Pauli terms
- `qiskit`: static `SparsePauliOp.from_list(...)` snippets
- `cirq`: static sums of `cirq.X/Y/Z(qubits[i])` products
- `pennylane`: static `qml.Hamiltonian([...], [...])` snippets
- `braket`: static `hamiltonian_terms = [(coefficient, Observable..., targets)]` snippets

Supported outputs:

- `qiskit_aer`: Qiskit `SparsePauliOp`
- `cirq`: Cirq Pauli-string expression
- `pennylane`: PennyLane `qml.Hamiltonian`
- `braket_local`: Braket observable terms with explicit targets
- `pauli-json`: neutral JSON

Examples:

```bash
quantum-bench translate-hamiltonian examples/translation/ising_hamiltonian.json \
  --from-format pauli-json \
  --to-format pennylane \
  --output artifacts/ising_pennylane.py \
  --save-report artifacts/ising_translation_report.json

quantum-bench translate-observable examples/translation/ising_hamiltonian.json \
  --from-format pauli-json \
  --to-format qiskit_aer

quantum-bench translation-audit
quantum-bench translation-audit --from-format qiskit --to-format qiskit_aer --json
```

Verification supports two modes. `canonical` reimports generated SDK source and compares neutral qubit-indexed Pauli terms. `matrix` additionally compares dense matrices for small Hamiltonians up to 6 qubits, which is useful for stronger confidence during SDK migration. Non-Pauli operator algebra, symbolic coefficients, and noise models remain future work.

## Workflow-Level Translation

`translate-workflow` covers the next semantic layer around circuits. It accepts neutral `workflow-json` plus a first-pass static subset of Qiskit, Cirq, PennyLane, and Braket parameterized workflow snippets, then emits free local SDK Python for Qiskit Aer, Cirq, PennyLane, or Braket LocalSimulator. The workflow JSON can include:

- parameterized circuits using `H`, `X`, `Y`, `Z`, `RX`, `RY`, `RZ`, and `CNOT`/`CX`
- symbolic parameter names and numeric parameter bindings
- counts, samples, probabilities, and Pauli expectation requests
- local shot-count execution wrappers and result extraction snippets

Example:

```bash
quantum-bench translate-workflow examples/translation/parameterized_workflow.json \
  --to-format qiskit_aer \
  --verify canonical \
  --output artifacts/parameterized_workflow_qiskit.py
```

Generated workflow scripts define `neutral_result` and print it as JSON with `counts`, `shots`, `probabilities`, `expectations`, and `metadata`. They also embed `workflow_spec`, which lets the verifier reimport generated snippets and compare canonical workflow semantics. Golden workflow outputs live in `examples/translation/expected/parameterized_workflow_to_*.py`.

`translate-result` normalizes SDK-shaped result JSON into the same portable result object with `counts`, `shots`, `probabilities`, optional `expectations`, and `metadata`:

```bash
quantum-bench translate-result examples/translation/qiskit_counts_result.json \
  --from-format qiskit-counts-json \
  --output artifacts/neutral_result.json

quantum-bench translate-result examples/translation/pennylane_samples_result.json \
  --from-format pennylane-samples-json
```

`group-pauli-terms` groups weighted Pauli Hamiltonian terms into qubit-wise commuting measurement sets:

```bash
quantum-bench group-pauli-terms examples/translation/ising_hamiltonian.json \
  --from-format pauli-json \
  --output artifacts/ising_measurement_groups.json
```

This is intentionally not arbitrary Python migration. Static SDK workflow imports currently cover generated snippets and common local patterns such as Qiskit `Parameter`, Cirq `sympy.Symbol`, PennyLane QNode arguments/device shots, and Braket `FreeParameter`. Broader user-authored Python migration remains future work; `workflow-json` is still the most precise migration contract for parameterized execution workflows.

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

`--save-report` writes JSON for `translate`, `translate-check`, Hamiltonian, workflow, result, and grouping commands. Reports include detected formats, `schema_metadata` for neutral input/output formats, `semantic_contract` details, diagnostics, gate inventory for checks, verification total variation distance for translations, and supported outputs. `translate-check` reports also include `migration_audit` guidance and can write a compact Markdown review with `--save-markdown`. `translate-all` writes per-target reports, a combined JSON report, neutral `internal-json`, selected target source files, and a Markdown summary. These reports are intended for CI and migration audits.

## Verification

`--verify exact` reimports the generated circuit source and compares exact measurement probabilities with total variation distance.

`--verify samples` samples both neutral distributions with a deterministic local sampler and compares the sampled distributions. Use `--sample-shots` and `--verify-tolerance` to tune this check.

A failed verification exits with status 1. The translated source is still produced so users can inspect it, but the command reports the failed semantic check.

## Caveats

Translation reports include warning diagnostics for backend-specific behavior that users should review: measurement bit ordering, Braket probability targets versus measurement counts, PennyLane QNode sampling, and controlled-phase conventions. Exact verification compares neutral measurement probabilities and is the recommended guardrail for these caveats.

## Golden Outputs

`quantum-bench translation-audit --json` emits the current SDK translation coverage matrix, including neutral schema version, supported gates, parameter forms, measurements, Hamiltonian terms, result shapes, diagnostics, caveats, and verification modes per local SDK target.

Expected generated outputs for selected fixtures live in `examples/translation/expected/`. Regenerate them intentionally after codegen changes:

```bash
python examples/translation/update_expected.py
```

Check that committed expected outputs are current:

```bash
python examples/translation/update_expected.py --check
```


Hamiltonian golden outputs live alongside circuit golden outputs in `examples/translation/expected/`. The maintenance scripts cover both circuit and Hamiltonian examples:

```bash
python examples/translation/verify_examples.py
python examples/translation/update_expected.py --check
```
