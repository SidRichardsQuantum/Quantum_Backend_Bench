# Benchmark Methodology

This project is intended for local, reproducible comparisons of quantum SDK simulator behavior. It is not a hardware benchmark and does not certify quantum volume, hardware fidelity, or vendor performance.

For background on qubits, circuits, shots, distributions, noise, benchmark families, and metric definitions, see [THEORY.md](./THEORY.md). This document focuses on how those concepts are measured and reported by this package.

## Table of Contents

- [What Is Measured](#what-is-measured)
- [What Is Not Measured](#what-is-not-measured)
- [Runtime Interpretation](#runtime-interpretation)
- [Backend Fairness](#backend-fairness)
- [Noise Benchmarks](#noise-benchmarks)
- [Benchmark Validity](#benchmark-validity)
- [Recommended Research Workflow](#recommended-research-workflow)
- [Reproducibility Checklist](#reproducibility-checklist)

## What Is Measured

- Runtime for local SDK execution adapters.
- Circuit structure: depth, gate count, and two-qubit gate count.
- Measurement counts and normalized distributions.
- Target-state success probability for benchmarks with a defined target state.
- Total variation distance from an ideal distribution when available.

## What Is Not Measured

- Cloud queue time or QPU execution time.
- Hardware calibration quality.
- End-to-end provider service reliability.
- Formal quantum volume certification.
- Noise model equivalence across SDKs.

## Runtime Interpretation

`runtime_seconds` is the mean of repeated backend executions when `--repeats` is greater than 1. Raw samples are stored in `metadata.runtime_seconds_samples`, and min/max/stddev are stored in `metrics`.

Adapters differ in what their runtime includes:

- Qiskit Aer and pyQuil include compilation/transpilation work in the adapter runtime.
- Cirq, PennyLane, Braket LocalSimulator, CUDA-Q, and QuTiP primarily measure local sample/simulation execution inside the adapter.
- pyQuil may start or connect to local QVM/quilc processes through its local Forest runtime helper.

These differences are reported by `quantum-bench info` and should be disclosed when comparing backends.

## Backend Fairness

Backend comparisons are useful for practical workflow comparisons, but they are not perfectly controlled simulator benchmarks. SDKs may use different default simulation methods, measurement ordering conventions, compilation passes, and random sampling implementations.

Use the same:

- benchmark parameters
- shot counts
- repeat counts
- random seeds
- Python environment
- machine and OS

Every result captures package versions, Python version, platform metadata, and git commit information to make this easier to audit.

## Noise Benchmarks

Depolarizing noise injection is currently implemented for Cirq, PennyLane, and Qiskit Aer adapters. Other execution adapters may run noisy benchmark wrappers without injecting noise; result metadata reports `noise_supported` and `noise_applied` where available.

Noise comparisons should be treated as adapter-specific behavior, not a claim that two SDKs model identical physical channels.

## Benchmark Validity

- GHZ measures entangling-circuit construction and ideal two-state output concentration.
- QFT measures structured controlled-phase workloads.
- Bernstein-Vazirani and Deutsch-Jozsa measure small oracle workloads with known ideal outputs.
- Grover measures small marked-state amplification and is limited to 2 to 4 qubits in this implementation.
- QAOA MaxCut measures a single-layer optimization circuit and reports probability mass on optimal line or ring graph cut bitstrings.
- Random circuits provide reproducible synthetic workloads, not application-level algorithms.
- Quantum-volume-style circuits provide shuffled-pair random layers, not formal quantum volume certification.
- Hamiltonian simulation uses a simple first-order Trotterized Ising-style model.

## Recommended Research Workflow

1. Write or reuse an experiment manifest under `examples/manifests/`.
2. Run with at least `repeats: 3`; use more for timing studies.
3. Save JSON and CSV outputs.
4. Record the git commit and dirty-state metadata from the result bundle.
5. Report backend capability caveats from `quantum-bench info`.

## Reproducibility Checklist

When publishing or comparing results, record:

- package version and git commit
- whether the git tree was dirty
- Python version, OS, and machine type
- installed backend package versions
- backend caveats from `quantum-bench doctor` or `quantum-bench info`
- benchmark parameters, random seeds, shot counts, and repeat counts
- whether runtime includes transpilation or external local services
- whether noise was requested, supported, and applied
- raw runtime samples, not only the mean
