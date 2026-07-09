# Roadmap

This roadmap tracks the next product direction for `quantum-backend-bench`. The
project remains local-first and reproducibility-focused, but the next major area
of work is making the package more useful for users moving small quantum
workloads across multiple SDKs.

## 0.3 Interop and Translation Stabilization

The recommended next release theme is a verified SDK interop layer:

> Define a neutral, verified contract for moving small quantum workloads across
> Qiskit, Cirq, PennyLane, and Braket LocalSimulator.

Planned work:

- Version the neutral schemas for `internal-circuit`, `pauli-json`,
  `workflow-json`, and `result-json`, including explicit `schema_version`
  fields and documented compatibility expectations.
- Publish JSON Schema files and examples for the neutral circuit, Pauli
  Hamiltonian, workflow, and result-object formats.
- Generate a translation coverage matrix that reports supported gates,
  parameter forms, measurements, Hamiltonian terms, result shapes, workflow
  features, diagnostics, and verification modes per SDK target.
- Add a higher-level `translate-all` workflow that emits translated source,
  neutral JSON, verification reports, diagnostics, and a compact Markdown
  summary for all selected SDK targets.
- Keep translation conservative: reject unsupported dynamic Python constructs
  with structured diagnostics instead of producing approximate rewrites.
- Extend supported semantics carefully, starting with parameter expressions,
  controlled rotations, richer register and wire naming, a broader OpenQASM 3
  subset, and neutral noise-model descriptions.
- Refactor translation internals toward SDK adapter modules with explicit
  import, emit, capability, and diagnostic hooks.
- Tighten optional SDK compatibility with tested version ranges, constraints
  files, and scheduled optional-SDK CI coverage.

## Longer-Term Directions

- Consider additional local SDK targets only when they fit the same neutral
  contract and verification model.
- Keep cloud hardware and provider-service workflows optional and outside the
  default onboarding path.
- Add new benchmark families only when they strengthen reproducible SDK
  comparison or translation validation.

## Non-Goals

- Arbitrary Python program migration.
- Hardware performance claims, cloud queue benchmarking, or provider billing
  workflows in the default path.
- Broad speed rankings that are not tied to captured environment metadata and
  explicit adapter caveats.
