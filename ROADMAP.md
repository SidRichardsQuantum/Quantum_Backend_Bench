# Roadmap

This roadmap tracks the next product direction for `quantum-backend-bench`. The
project remains local-first and reproducibility-focused, but the next major area
of work is making the package more useful for users moving small quantum
workloads across multiple SDKs.

## Interop and Translation Stabilization

The recommended next release theme is a verified SDK interop layer:

> Define a neutral, verified contract for moving small quantum workloads across
> Qiskit, Cirq, PennyLane, and Braket LocalSimulator.

Recently completed:

- `translate-check --to-format`, `translate-check --save-markdown`, and
  `translate-all` now provide target-aware migration checks and
  multi-target local SDK artifacts.

Planned work:

- Make the translation promise explicit in CLI and documentation: lossless only
  within the declared neutral semantic subset, with every command reporting the
  supported contract before producing translated output.
- Version the neutral schemas for `internal-circuit`, `pauli-json`,
  `workflow-json`, and `result-json`, including explicit `schema_version`
  fields and documented compatibility expectations.
- Publish JSON Schema files and examples for the neutral circuit, Pauli
  Hamiltonian, workflow, and result-object formats.
- Expand the neutral IR before adding non-local provider integrations. Priority
  fields include named quantum/classical registers, measurement keys, bit
  ordering, global phase, symbolic parameter expressions, richer gate coverage
  (`U`, `SX`, phase gates, `CCX`, controlled rotations), reset/barrier/delay
  annotations where preservable, and optional neutral noise channels.
- Generate a translation coverage matrix that reports supported gates,
  parameter forms, measurements, Hamiltonian terms, result shapes, workflow
  features, diagnostics, and verification modes per SDK target.
- Keep translation conservative: reject unsupported dynamic Python constructs
  with structured diagnostics instead of producing approximate rewrites.
- Extend supported semantics carefully, starting with parameter expressions,
  controlled rotations, richer register and wire naming, a broader OpenQASM 3
  subset, and neutral noise-model descriptions.
- Improve SDK-native source importers while keeping static analysis as the
  default guardrail: broader Qiskit `QuantumCircuit`/OpenQASM handling, Cirq
  construction styles and measurement keys, PennyLane QNode/tape patterns,
  PennyLane `qml.expval(...)`, Braket `Circuit` result types, and Braket
  `circuit.expectation(...)`.
- Strengthen semantic verification with canonical structure checks,
  unitary/statevector comparison up to global phase, measurement-distribution
  TVD, expectation-value comparison, small density-matrix comparison for noisy
  channels, and workflow result-schema validation.
- Add purpose-level workflow specs for common jobs such as sampler, estimator,
  VQE, QAOA, Hamiltonian simulation, parameter sweeps, and measurement
  grouping, so translations can preserve user intent instead of only gate
  syntax.
- Grow the translation corpus with accepted and rejected real-world snippets,
  expected diagnostics, verification reports, and CI-generated per-SDK coverage
  artifacts. Add explicit regression checks that `migration_audit/` and
  `roundtrip_audit/` expected artifacts regenerate cleanly and that `roadmap/`
  examples stay excluded from supported verification until implemented.
- Refactor translation internals toward SDK adapter modules with explicit
  import, emit, capability, and diagnostic hooks.
- Tighten notebook artifact handling for migration-audit notebooks, including
  stable generated artifact names and path scrubbing if notebook outputs are
  later committed as docs assets.
- Add optional self-describing `purpose` or `notes` fields to generated
  translation reports and committed expected-report examples so artifacts remain
  understandable outside the README context.
- Tighten optional SDK compatibility with tested version ranges, constraints
  files, and scheduled optional-SDK CI coverage.

## Longer-Term Directions

- Consider additional local SDK targets only when they fit the same neutral
  contract and verification model.
- Prefer deeper support for free, instantly accessible local SDKs first:
  Qiskit Aer, Cirq, PennyLane, Braket `LocalSimulator`, and QuTiP as an
  independent reference/verifier. Treat CUDA-Q as local-optional when install
  friction is acceptable, and keep pyQuil optional because local QVM/quilc
  runtime requirements make it less instant-accessible.
- Keep cloud hardware and provider-service workflows optional and outside the
  default onboarding path.
- Revisit non-free or non-instant SDK/provider integrations only if a required
  translation capability cannot be modeled or verified with the local/free SDK
  set.
- Add new benchmark families only when they strengthen reproducible SDK
  comparison or translation validation.

## Non-Goals

- Arbitrary Python program migration.
- Hardware performance claims, cloud queue benchmarking, or provider billing
  workflows in the default path.
- Broad speed rankings that are not tied to captured environment metadata and
  explicit adapter caveats.
