# Roadmap

This roadmap tracks planned work for `quantum-backend-bench`. The project is
centered on local quantum SDK comparison, translation, and semantic verification.
Completed work and release history belong in [CHANGELOG.md](./CHANGELOG.md).

## Translation and Interop Priorities

- Broaden the portable OpenQASM 3 subset and make target-specific annotation
  gaps explicit, while keeping neutral local noise channels distinct from
  SDK-specific or provider-calibrated noise semantics.
- Improve static SDK source importers for common Qiskit `QuantumCircuit`, Cirq
  construction and measurement-key, PennyLane QNode/tape, and Braket `Circuit`
  result-type patterns.
- Keep translation conservative: reject unsupported dynamic Python constructs
  with structured diagnostics instead of producing approximate rewrites.
- Add small density-matrix comparisons for neutral noisy channels to strengthen
  verification beyond canonical, statevector, distribution, expectation-value,
  and result-schema checks.
- Grow the accepted and rejected translation corpus with real-world snippets,
  expected diagnostics, verification reports, and per-SDK coverage artifacts.
- Add scheduled optional-SDK compatibility runs and continue reviewing tested
  version bands as upstream SDKs evolve.

## Scope Guardrails

- Keep the core centered on free, local SDK comparison, translation, and
  verification.
- Prefer deeper support for Qiskit Aer, Cirq, PennyLane, and Braket
  `LocalSimulator` before adding another SDK target.
- Consider another local SDK only when it supports the same neutral contract and
  verification model. Keep CUDA-Q platform-optional and pyQuil optional because
  it requires local QVM/quilc runtimes.
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
