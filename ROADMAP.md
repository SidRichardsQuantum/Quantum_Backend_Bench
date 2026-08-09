# Roadmap

This roadmap tracks planned work for `quantum-backend-bench`. The project is
centered on local quantum SDK comparison, translation, and semantic verification.
Completed work and release history belong in [CHANGELOG.md](./CHANGELOG.md).

## Translation and Interop Priorities

- Broaden the portable OpenQASM 3 subset and make target-specific annotation
  gaps explicit, while keeping neutral local noise channels distinct from
  SDK-specific or provider-calibrated noise semantics.
- Evaluate the official `openqasm3` reference AST and parser behind an internal
  adapter for syntax handling. Keep the project's explicit portable-subset
  validation, semantic checks, and structured diagnostics; a successful parse
  must not imply that the full OpenQASM 3 program is supported.
- Improve static SDK source importers for common Qiskit `QuantumCircuit`, Cirq
  construction and measurement-key, PennyLane QNode/tape, and Braket `Circuit`
  result-type patterns.
- Keep translation conservative: reject unsupported dynamic Python constructs
  with structured diagnostics instead of producing approximate rewrites.
- Grow the accepted and rejected translation corpus with real-world snippets,
  expected diagnostics, verification reports, and per-SDK coverage artifacts.
- Add scheduled optional-SDK compatibility runs and continue reviewing tested
  version bands as upstream SDKs evolve.

## Candidate Local SDK Integrations

New SDKs are candidates rather than commitments. An integration should enter
the supported matrix only after it can build native circuits from the neutral
model, execute the shared local benchmark subset, normalize results and bit
ordering, report capability caveats, and participate in semantic or round-trip
verification. Unsupported operations must fail with structured diagnostics.

- **Qulacs:** candidate for an optional independent execution and statevector or
  sampled-result verification backend. Prioritize native gate mapping, partial
  measurement and endianness tests, deterministic seed reporting, and explicit
  noisy-trajectory semantics. Treat source translation as a later phase, and do
  not position the adapter as a broad simulator-speed ranking feature.

The following tools fit only as narrowly scoped optional audits, not as general
execution targets:

- **Mitiq:** consider an optional cross-SDK conversion or local error-mitigation
  audit after dependency and license review. It should consume existing local
  adapters and normalized results rather than appear in the execution-backend
  registry.
- **QuTiP-QIP:** reconsider only for a native gate-, Hamiltonian-, density-matrix-,
  or pulse-dynamics verification contract. Do not restore a wrapper that merely
  checks for QuTiP while performing simulation in project-owned NumPy code.
- **Stim:** consider only alongside a dedicated Clifford or quantum-error-
  correction semantic-audit suite. It must reject non-Clifford workloads and
  must not be advertised as implementing the repository's general circuit
  contract.

## Scope Guardrails

- Keep the core centered on free, local SDK comparison, translation, and
  verification.
- Prefer deeper support for Qiskit Aer, Cirq, PennyLane, Braket
  `LocalSimulator`, and Qibo's explicit NumPy backend before adding another SDK target.
- Consider another local SDK only when it supports the same neutral contract and
  verification model. Keep CUDA-Q platform-optional and pyQuil optional because
  it requires local QVM/quilc runtimes.
- Keep candidate integrations out of the practical `all` extra and default
  onboarding until Python 3.11/3.12 compatibility, local installation,
  representative semantic audits, and maintenance burden have been reviewed.
- Prefer an independent semantic or interoperability benefit over adding an SDK
  that merely delegates execution to a backend already represented here.
- Add a benchmark family only when it directly strengthens SDK parity,
  translation validation, or a reproducible semantic audit.

## Non-Goals

- Arbitrary Python program migration.
- Cloud job submission, provider credentials, billing workflows, or queue
  benchmarking.
- Quantum hardware performance or certification claims.
- Broad simulator speed rankings without captured environment metadata and
  explicit adapter caveats.
- General quantum algorithm benchmark expansion unrelated to SDK comparison or
  translation verification.
