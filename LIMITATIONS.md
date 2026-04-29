# Known Limitations

This project is useful for reproducible local SDK comparison, but it has important limits.

For the theory behind the benchmark families, metrics, noise model terminology, and statistical interpretation, see [THEORY.md](./THEORY.md).

## Table of Contents

- [Not a Hardware Benchmark](#not-a-hardware-benchmark)
- [SDK Runtimes Are Not Perfectly Equivalent](#sdk-runtimes-are-not-perfectly-equivalent)
- [Noise Models Are Adapter-Specific](#noise-models-are-adapter-specific)
- [Circuit Support Is Intentionally Small](#circuit-support-is-intentionally-small)
- [pyQuil Requires Local Runtime Support](#pyquil-requires-local-runtime-support)
- [Quantum-Volume-Style Is Not Certification](#quantum-volume-style-is-not-certification)
- [Statistical Interpretation Needs Care](#statistical-interpretation-needs-care)

## Not a Hardware Benchmark

The package does not measure QPU performance, cloud queue time, calibration quality, or provider service reliability.

## SDK Runtimes Are Not Perfectly Equivalent

Adapters differ in what their runtime includes. Some include compilation or transpilation work, while others mostly measure local simulation and sampling. Use `quantum-bench info` to inspect these caveats.

## Noise Models Are Adapter-Specific

Cirq and PennyLane currently inject depolarizing noise in this project. Other adapters may execute noisy benchmark wrappers without injecting noise. Result metadata reports `noise_supported` and `noise_applied` where available.

## Circuit Support Is Intentionally Small

The internal circuit representation supports a focused gate set used by the built-in benchmarks. It is not a full quantum IR.

## pyQuil Requires Local Runtime Support

The pyQuil adapter is pip-installable, but execution depends on local QVM/quilc runtime availability.

## Quantum-Volume-Style Is Not Certification

The quantum-volume-style benchmark is a portable randomized workload. It is not formal quantum volume certification.

## Statistical Interpretation Needs Care

`--repeats` gives mean/stddev/min/max for local runtime samples. These are useful for reproducibility and regression checks, but should not be treated as universal performance claims.
