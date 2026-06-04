# Circuit Translation Examples

These fixtures show supported `quantum-bench translate` inputs and expected outputs for free local SDK APIs. They are intentionally small and static so they can be used in tests and CI.

Run all examples with exact verification:

```bash
python examples/translation/verify_examples.py
```

Individual examples:

```bash
quantum-bench translate examples/translation/qiskit_registers.py --from-format qiskit --to-format cirq --verify exact
quantum-bench translate examples/translation/cirq_nested.py --from-format cirq --to-format qiskit_aer --verify exact
quantum-bench translate examples/translation/ghz.qasm --from-format openqasm --to-format pennylane --verify exact
quantum-bench translate-check examples/translation/pennylane_positional.py --from-format pennylane
```

## Maintaining Expected Outputs

Regenerate pinned outputs after intentional codegen changes:

```bash
python examples/translation/update_expected.py
```

CI checks them with:

```bash
python examples/translation/update_expected.py --check
```

Rejected examples live in `rejected/` and pin diagnostics for unsupported constructs.
