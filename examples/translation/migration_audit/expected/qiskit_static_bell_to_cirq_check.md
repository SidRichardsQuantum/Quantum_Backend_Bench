# Qiskit Static Bell to Cirq Audit

- input format: `qiskit`
- target: `cirq`
- status: `target_supported`
- guarantee: Lossless only within the declared neutral semantic subset.
- operations: 2
- gates: `{"CNOT": 1, "H": 1}`

## Preserved
- supported gates and operation order
- static measurement targets
- numeric rotation parameters

## Rewritten
- SDK imports and construction syntax
- wire/register names into neutral integer-wire semantics

## Rejected If Present
- dynamic Python control flow
- custom gates
- classical control
- provider/runtime calls
- transpiler settings
- arbitrary result processing

## Not Modeled
- cloud execution behavior
- noise models
- full Python program state

Verification: Run translate with --verify exact for deterministic circuit semantics or --verify samples for sampled workflows.
