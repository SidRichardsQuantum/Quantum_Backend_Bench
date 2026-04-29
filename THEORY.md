# Theoretical Background

This document summarizes the core quantum-computing and benchmarking concepts needed to interpret `quantum-backend-bench` results. It is a conceptual reference. For how this package applies these concepts in experiments, see [METHODOLOGY.md](./METHODOLOGY.md). For known caveats, see [LIMITATIONS.md](./LIMITATIONS.md).

## Table of Contents

- [Scope](#scope)
- [Quantum States, Qubits, and Measurement](#quantum-states-qubits-and-measurement)
- [Circuits and Gates](#circuits-and-gates)
- [Shots, Counts, and Distributions](#shots-counts-and-distributions)
- [Circuit Structure Metrics](#circuit-structure-metrics)
- [Runtime Metrics](#runtime-metrics)
- [Success Probability](#success-probability)
- [Total Variation Distance](#total-variation-distance)
- [Sampling Error and Repeats](#sampling-error-and-repeats)
- [Noise Models](#noise-models)
- [Benchmark Families](#benchmark-families)
  - [GHZ](#ghz)
  - [Quantum Fourier Transform](#quantum-fourier-transform)
  - [Bernstein-Vazirani](#bernstein-vazirani)
  - [Deutsch-Jozsa](#deutsch-jozsa)
  - [Grover Search](#grover-search)
  - [Random Circuits](#random-circuits)
  - [Quantum-Volume-Style Circuits](#quantum-volume-style-circuits)
  - [Hamiltonian Simulation](#hamiltonian-simulation)
- [Backend Comparability](#backend-comparability)
- [Reading Results Safely](#reading-results-safely)
- [Related Project Documents](#related-project-documents)
- [Author](#author)
- [License](#license)

## Scope

`quantum-backend-bench` compares local quantum SDK simulator behavior on a shared set of benchmark circuits. The project measures practical simulator workflow outputs: circuit structure, runtime, sampled bitstring counts, and distribution-level quality metrics.

The package does not benchmark quantum hardware, certify quantum volume, or prove that two SDKs implement physically identical simulation models.

## Quantum States, Qubits, and Measurement

A qubit is a two-level quantum system with computational basis states `|0>` and `|1>`. A multi-qubit computational basis state is a bitstring such as `|000>` or `|101>`. Before measurement, a quantum state may be a superposition of many basis states with complex amplitudes.

Measurement converts a quantum state into classical bits. Repeating the same circuit many times produces a sample of bitstrings. Each repetition is called a shot. A finite number of shots gives an empirical distribution, not the exact mathematical probability distribution.

For example, a 3-qubit GHZ circuit ideally produces only `000` and `111`, each with probability `0.5`. With 1024 shots, observed counts might be close to `{"000": 512, "111": 512}`, but sampling variation is expected.

## Circuits and Gates

A quantum circuit is an ordered sequence of operations applied to qubits. This project uses a small backend-neutral circuit representation covering the gates needed by the built-in benchmarks:

- Single-qubit gates: `H`, `X`, `Y`, `Z`, `S`, `T`, `RX`, `RY`, `RZ`
- Two-qubit gates: `CNOT`, `CZ`, `SWAP`, `CPHASE`
- Measurement operations over selected qubits

Different SDKs may represent, decompose, optimize, or draw the same logical circuit differently. The internal circuit representation keeps the benchmark definition portable, while each backend adapter converts it into that SDK's native circuit object.

## Shots, Counts, and Distributions

Backends return measurement counts such as:

```json
{
  "000": 510,
  "111": 514
}
```

Counts are converted into a measurement distribution by dividing by the total number of shots:

```json
{
  "000": 0.498046875,
  "111": 0.501953125
}
```

When `--repeats` is greater than 1, this project aggregates counts across repeats. If `shots=1024` and `repeats=3`, then `total_shots=3072`.

## Circuit Structure Metrics

Structural metrics describe the logical circuit, not the wall-clock behavior of a simulator.

- `depth`: how many sequential layers of operations are needed when independent operations can run in parallel
- `gate_count`: total number of internal circuit operations
- `two_qubit_gate_count`: number of two-qubit operations, often a useful proxy for circuit interaction complexity
- `gate_histogram`: counts by operation type when structural analysis is available

This project uses `pytket` for structural analysis when installed. If `pytket` is unavailable, it falls back to internal structural estimates. These metrics are useful for comparing benchmark cases, but they are not a complete model of simulator cost.

## Runtime Metrics

`runtime_seconds` is the mean elapsed time of repeated local backend executions. Raw runtime samples are stored in `metadata.runtime_seconds_samples`, with min, max, and standard deviation stored in `metrics`.

Runtime is affected by more than theoretical circuit complexity:

- SDK import and setup behavior
- circuit conversion inside the adapter
- compilation or transpilation steps
- simulator implementation and default method
- local CPU, memory, and process scheduling
- external local services such as QVM/quilc for pyQuil

Because adapters differ, runtime comparisons should be read as local workflow measurements rather than universal simulator rankings.

## Success Probability

Some benchmarks have a known target bitstring. `success_probability` is the empirical probability of observing that target state:

```text
success_probability = target_state_count / total_shots
```

For example, Grover search defines a marked state such as `101`. If `101` appears 900 times out of 1024 shots, the success probability is about `0.879`.

Not every benchmark has a single target state. GHZ, QFT, random circuits, and Hamiltonian simulation may be better interpreted through full distributions or benchmark-specific expectations.

## Total Variation Distance

Total variation distance, or TVD, measures how far an observed distribution is from an ideal distribution:

```text
TVD(P, Q) = 0.5 * sum_x |P(x) - Q(x)|
```

TVD is `0.0` when distributions match exactly and approaches `1.0` as they become maximally different. In this project, TVD is computed when a benchmark defines an ideal distribution.

Finite-shot sampling means TVD is rarely exactly zero, even for a correct noiseless simulator. More shots usually reduce sampling noise but increase runtime.

## Sampling Error and Repeats

Shot-based simulation produces random samples from a probability distribution. A result from 64 shots has much higher sampling uncertainty than a result from 4096 shots.

Repeats serve a different purpose:

- More shots reduce uncertainty in measured bitstring probabilities.
- More repeats help estimate runtime variability across independent executions.

For distribution-quality studies, increase `shots`. For timing stability studies, increase `repeats`. For research reports, record both.

## Noise Models

Noise models approximate ways real quantum states and operations can deviate from ideal behavior. This project currently focuses on depolarizing noise where supported.

Depolarizing noise replaces part of a quantum state with a more random state. As noise increases, target-state probability often decreases and TVD from the ideal distribution often increases.

Noise support is adapter-specific:

- Cirq and PennyLane inject depolarizing noise in this project.
- Other adapters may run the wrapped benchmark without injecting noise.
- Result metadata reports whether noise was supported and applied when the adapter exposes that information.

Noise comparisons across SDKs should be treated as comparisons of adapter behavior, not proof that all SDKs used the same physical channel.

## Benchmark Families

### GHZ

GHZ circuits create entanglement across all qubits. The ideal distribution is split between all-zero and all-one bitstrings. GHZ is useful for checking measurement ordering, entangling gates, and simple distribution quality.

### Quantum Fourier Transform

QFT is a structured transform using Hadamard and controlled-phase operations. It is useful for exercising controlled rotations and circuit-depth growth.

### Bernstein-Vazirani

Bernstein-Vazirani is an oracle benchmark that recovers a hidden bitstring with one oracle query in the ideal algorithm. In this project, the final qubit is used as the oracle work qubit, so the secret string length is `n_qubits - 1`.

### Deutsch-Jozsa

Deutsch-Jozsa distinguishes constant functions from balanced functions in an idealized oracle setting. This project includes constant and linear balanced cases.

### Grover Search

Grover search amplifies the probability of a marked state. This implementation is intentionally small and supports 2 to 4 qubits. It is useful for target-state success probability, not large-scale search claims.

### Random Circuits

Random circuits provide reproducible synthetic workloads from a fixed gate set and seed. They are useful for stress-testing conversion and execution paths, but they do not represent a specific application algorithm.

### Quantum-Volume-Style Circuits

Quantum-volume-style circuits use randomized layers and shuffled qubit pairs. In this package they are portable workloads inspired by quantum volume circuits, not formal quantum volume certification.

### Hamiltonian Simulation

Hamiltonian simulation approximates time evolution under a model Hamiltonian. This project uses a simple first-order Trotterized Ising-style model:

```text
H = sum_i Z_i Z_{i+1} + 0.5 * sum_i X_i
```

Trotterization approximates continuous evolution with repeated discrete gate layers. More Trotter steps can improve approximation quality but increase circuit size.

## Backend Comparability

Two backends can run the same logical benchmark while still differing in important ways:

- Native gate sets and decomposition choices
- Qubit and bitstring ordering conventions
- Whether runtime includes compilation or transpilation
- Statevector, density-matrix, tensor-network, or shot-sampling methods
- Random number generation and seeding behavior
- Local service requirements
- Optional noise support

For this reason, backend comparisons are most defensible when they disclose environment metadata, backend capability notes, benchmark parameters, shots, repeats, and known adapter caveats.

## Reading Results Safely

Prefer statements like:

- "On this machine and environment, backend A was faster than backend B for this workload."
- "The observed distribution was closer to the ideal distribution at this shot count."
- "Runtime variance increased for this benchmark family under this setup."
- "A higher success probability is better for this target-state benchmark, but the estimate depends on shots."
- "A lower TVD is better for this ideal-distribution benchmark, but finite-shot sampling prevents exact conclusions."

Avoid statements like:

- "Backend A is universally faster."
- "This proves hardware performance."
- "This quantum-volume-style result is a certified quantum volume."
- "Noise results are physically equivalent across SDKs."

## Related Project Documents

- [README.md](./README.md): project overview and quickstart
- [USAGE.md](./USAGE.md): CLI and Python workflows
- [METHODOLOGY.md](./METHODOLOGY.md): measurement methodology and research workflow
- [SCHEMA.md](./SCHEMA.md): JSON and CSV result fields
- [LIMITATIONS.md](./LIMITATIONS.md): known boundaries and caveats

---

## Author

Sid Richards

- LinkedIn: [sid-richards-21374b30b](https://www.linkedin.com/in/sid-richards-21374b30b/)
- GitHub: [SidRichardsQuantum](https://github.com/SidRichardsQuantum)

## License

MIT. See [LICENSE](LICENSE).
