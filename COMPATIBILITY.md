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

| Integration | Extra | Role | Account or payment required | Local runtime requirement | CI coverage |
|---|---|---|---|---|---|
| Cirq | `cirq` | Execution backend | No | Python package only | Main CI and smoke workflow |
| PennyLane | `pennylane` | Execution backend | No | Python package only | Optional backend smoke |
| Amazon Braket SDK | `braket` | LocalSimulator execution backend | No for `LocalSimulator` | Python package only | Optional backend smoke |
| Qiskit Aer | `qiskit` | Execution backend | No | Python package only | Optional backend smoke |
| QuTiP | `qutip` | Execution backend | No | Python package only | Optional backend smoke |
| pytket | `tket` | Structural analysis and drawing | No | Python package only | Main CI install |
| CUDA-Q | `cudaq` | Execution backend | No for local simulator use | Platform-sensitive Python package | Experimental optional smoke |
| pyQuil QVM | `pyquil` | Execution backend | No for local QVM use | Python package plus local `qvm` and `quilc` executables | Optional smoke, external runtime skipped unless available |
| qBraid | `qbraid` | Discovery only | Not used for execution | Python package only | Dependency metadata only |
| Q# / QDK | `qsharp` | Discovery only | Not used for execution | Python package only | Dependency metadata only |
| Notebook helpers | `notebooks` | Tutorial notebooks | No | Python packages only | Not executed in CI |

## Extras Policy

- The base package has no required quantum SDK dependencies.
- Use `quantum-backend-bench[cirq]` for the fastest public first run.
- Use `quantum-backend-bench[all]` for the practical local Python-only comparison
  stack. This intentionally excludes CUDA-Q and pyQuil because they are heavier or
  depend on external local runtime support.
- Use `quantum-backend-bench[full]` only when explicitly testing every optional
  Python SDK extra.

## Backend Scope

The default project scope is local simulator benchmarking. SDKs that require cloud
accounts, billing, remote queues, or private provider services should not be part of
the default onboarding path. They may be considered later as clearly optional
provider adapters if the local, free workflow remains the primary experience.

## Validation Commands

```bash
quantum-bench doctor
quantum-bench validate
quantum-bench run ghz --backend cirq --n-qubits 3 --shots 128 --summary
quantum-bench suite smoke --backends cirq --shots 128 --summary
```

For reproducible example artifacts from the Cirq smoke path, see
[`examples/reference_results/cirq_smoke_2026-06-03/`](./examples/reference_results/cirq_smoke_2026-06-03/).
