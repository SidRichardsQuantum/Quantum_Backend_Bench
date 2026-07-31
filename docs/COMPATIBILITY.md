# Compatibility Matrix

This project prioritizes free, local, credential-free simulator workflows. The
matrix below documents the supported Python versions, optional SDK extras, and
runtime expectations for the current package line.

## Python Support

| Python | Status | Notes |
|---|---|---|
| 3.11 | Supported | Main local development and optional-backend smoke target |
| 3.12 | Supported | CI test, lint, build, and docs target |
| 3.13 | Not claimed | Not part of the current CI matrix |

## Backend and SDK Compatibility

| Integration | Extra | Role | Account or payment required | Local runtime requirement | CI coverage | Tested version band |
|---|---|---|---|---|---|---|
| Cirq | `cirq` | Execution backend | No | Python package only | Main CI and smoke workflow; auditable with `sdk-parity`, `semantic-audit`, `noise-audit`, `compile-audit`, and `roundtrip-audit` | `cirq>=1.4,<2` |
| PennyLane | `pennylane` | Execution backend | No | Python package only | Optional backend smoke | `pennylane>=0.38,<1` |
| Amazon Braket SDK | `braket` | LocalSimulator execution backend | No for `LocalSimulator` | Python package only | Optional backend smoke | `amazon-braket-sdk>=1.85,<2` |
| Qiskit Aer | `qiskit` | Execution backend | No | Python package only | Optional backend smoke | `qiskit>=1,<3`, `qiskit-aer>=0.15,<1` |
| pytket | `tket` | Structural analysis and drawing | No | Python package only | Main CI install | `pytket>=1.30,<3` |
| CUDA-Q | `cudaq` | Optional execution backend | No for local simulator use | Platform-sensitive Python package | Experimental optional smoke; outside default onboarding | `cudaq>=0.8,<1` |
| pyQuil QVM | `pyquil` | Optional execution backend | No for local QVM use | Python package plus local `qvm` and `quilc` executables | Package smoke in CI; external QVM runtime skipped unless available; outside default onboarding | `pyquil>=4,<5` |
| Notebook helpers | `notebooks` | Tutorial notebooks | No | Python packages only | Static notebook checks plus quickstart execution smoke in main CI | CI constraints for notebook extras |
| Documentation tooling | `docs` | Pages build and link validation | No | Python packages only | Main CI docs validation | CI constraints for docs extras |

## Extras Policy

- The base package requires NumPy for neutral exact verification but no quantum SDK.
- Use `quantum-backend-bench[cirq]` for the fastest public first run.
- Use `quantum-backend-bench[all]` for the practical local Python-only comparison
  stack. This intentionally excludes CUDA-Q and pyQuil because they are heavier or
  depend on external local runtime support.
- Use `quantum-backend-bench[full]` only when explicitly testing every optional
  Python SDK extra, including platform-sensitive or external-runtime adapters.

## Backend Scope

The default project scope is local SDK comparison, translation, and verification
on free local simulator workflows. SDKs that require cloud accounts, billing,
remote queues, or private provider services should not be part of the default
onboarding path. Heavyweight or external-runtime-backed SDKs stay optional
unless they can support the same neutral contract without weakening the local-first workflow.

## CI Dependency Constraints

Project metadata keeps optional SDK requirements broad for package users. CI installs through `constraints/ci.txt`, and `quantum-bench compatibility` reports those reviewed major-version bands so tooling and optional SDK smoke jobs adopt upstream releases deliberately. Review these bands before each release that changes translation or adapter behavior, and refresh scheduled optional-SDK smoke coverage when upstream SDK major versions approach the configured upper bounds.

## Validation Commands

```bash
quantum-bench doctor
quantum-bench compatibility
quantum-bench sdk-parity
quantum-bench semantic-audit --backends cirq qiskit_aer
quantum-bench compile-audit --backends cirq qiskit_aer
quantum-bench roundtrip-audit --include-hamiltonian --include-workflow
quantum-bench noise-audit
quantum-bench validate
quantum-bench run ghz --backend cirq --n-qubits 3 --shots 128 --summary
quantum-bench suite smoke --backends cirq --shots 128 --summary
```

For reproducible example artifacts from the Cirq smoke path, see
[`examples/reference_results/cirq_smoke_2026-06-03/`](../examples/reference_results/cirq_smoke_2026-06-03/).
