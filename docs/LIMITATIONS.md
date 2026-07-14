# Known Limitations

This project is useful for reproducible local SDK comparison, but it has important limits.

For the theory behind the benchmark families, metrics, noise model terminology, and statistical interpretation, see [THEORY.md](./THEORY.md).

## Table of Contents

- [Not a Hardware Benchmark](#not-a-hardware-benchmark)
- [Hardware Preparation Is Export Only](#hardware-preparation-is-export-only)
- [SDK Runtimes Are Not Perfectly Equivalent](#sdk-runtimes-are-not-perfectly-equivalent)
- [Noise Models Are Adapter-Specific](#noise-models-are-adapter-specific)
- [Circuit Support Is Intentionally Small](#circuit-support-is-intentionally-small)
- [Discovery-Only SDKs Are Informational](#discovery-only-sdks-are-informational)
- [Heavy or External Runtime SDKs Stay Optional](#heavy-or-external-runtime-sdks-stay-optional)
- [pyQuil Requires Local Runtime Support](#pyquil-requires-local-runtime-support)
- [Quantum-Volume-Style Is Not Certification](#quantum-volume-style-is-not-certification)
- [Statistical Interpretation Needs Care](#statistical-interpretation-needs-care)
- [Seeds Are Best Effort](#seeds-are-best-effort)

## Not a Hardware Benchmark

The package does not measure QPU performance, cloud queue time, calibration quality, or provider service reliability.

## Hardware Preparation Is Export Only

The `hardware` command writes preparation artifacts and caveats for external provider workflows. It does not submit jobs, manage credentials, inspect queues, estimate billing, or measure QPU performance.

## SDK Runtimes Are Not Perfectly Equivalent

Adapters differ in what their runtime includes. Some include compilation or transpilation work, while others mostly measure local simulation and sampling. Use `quantum-bench info` to inspect these caveats.

## Noise Models Are Adapter-Specific

Cirq, PennyLane, and Qiskit Aer currently inject several local noise models in this project: depolarizing, bit flip, phase flip, and amplitude damping. Qiskit Aer also supports a readout-error model; Cirq and PennyLane map readout-error requests through bit-flip-style channel injection rather than a separate measurement-confusion matrix. Other adapters may execute noisy benchmark wrappers without injecting noise. Result metadata reports `noise_supported` and `noise_applied` where available, and `quantum-bench noise-audit` reports the current matrix.

## Circuit Support Is Intentionally Small

The internal circuit representation supports a focused gate set used by the built-in benchmarks. It is not a full quantum IR.

## Discovery-Only SDKs Are Informational

qBraid and Q# / QDK are reported as optional ecosystem integrations only. They are not execution backends, translation targets, or verification engines in the current local SDK contract.

## Heavy or External Runtime SDKs Stay Optional

CUDA-Q and pyQuil fit local SDK comparison only when their platform or runtime requirements are already satisfied. They are intentionally outside the fastest default onboarding path.

## pyQuil Requires Local Runtime Support

The pyQuil adapter is pip-installable, but execution depends on local QVM/quilc runtime availability.

## Quantum-Volume-Style Is Not Certification

The quantum-volume-style benchmark is a portable randomized workload. It is not formal quantum volume certification.

## Statistical Interpretation Needs Care

`--repeats` gives mean/stddev/min/max for local runtime samples. These are useful for reproducibility and regression checks, but should not be treated as universal performance claims.

## Seeds Are Best Effort

Some backend SDKs expose deterministic simulator seed controls and others do not. Result metadata reports `seed_supported` and `seed_applied` so seeded and unseeded comparisons can be separated.
