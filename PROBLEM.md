# Problem Statement

Quantum users often need to answer a practical question:

> How does the same circuit workload behave across local quantum SDK simulators, and can I reproduce the comparison later?

Today that is harder than it should be. A student, researcher, or SDK maintainer usually has to:

- rewrite the same circuit in several SDKs
- decide how to measure runtime
- remember package versions and machine details
- repeat runs manually
- export results into ad hoc formats
- explain which SDKs injected noise and which did not
- document caveats after the fact

`quantum-backend-bench` solves this by providing a local-first, reproducible benchmark harness for common quantum workloads.

## Who It Serves

- Researchers comparing local simulator behavior across SDKs.
- Students learning how quantum frameworks differ without cloud accounts.
- SDK users choosing a simulator for a workload.
- Maintainers checking whether dependency upgrades changed behavior.
- Instructors building reproducible quantum computing labs.

## Problems Solved

### Benchmark Portability

Benchmarks are defined once in a backend-neutral representation, then executed through SDK adapters.

### Teaching

The same GHZ, QFT, Grover, oracle, Hamiltonian, random-circuit, and quantum-volume-style workloads can be run locally with simple CLI commands.

### Methodology

Experiment manifests define backends, shots, repeats, seeds, benchmark parameters, and output paths.

### SDK Regression Checks

`quantum-bench validate` runs known-correct GHZ and Bernstein-Vazirani checks against installed or selected backends.

### Noise-Model Comparison

Noise sweeps and manifests report whether adapters actually injected noise, so comparisons can be interpreted honestly.

### Backend Selection

`quantum-bench info` and `quantum-bench recommend` expose local-only status, external-process usage, shot sampling, statevector support, noise support, and transpilation caveats.

## Core Promise

The core promise is reproducibility, not universal speed ranking.

Speed numbers are environment-sensitive and adapter-dependent. This project makes those comparisons auditable by capturing runtime samples, environment metadata, package versions, git state, backend caveats, and stable result schemas.
