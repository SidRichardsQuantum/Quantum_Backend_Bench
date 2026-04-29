# Quantum Backend Bench

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.4-green.svg)](./CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![Backends](https://img.shields.io/badge/backends-Cirq%20%7C%20PennyLane%20%7C%20Braket%20%7C%20Qiskit%20%7C%20CUDA--Q-purple.svg)](./USAGE.md)
[![Analysis](https://img.shields.io/badge/analysis-pytket-orange.svg)](./README.md#backend-support)

Backend-agnostic benchmarking toolkit for local quantum circuit simulators. The package runs the same benchmark definitions across local simulator adapters such as Cirq, PennyLane, Amazon Braket `LocalSimulator`, Qiskit Aer, CUDA-Q, pyQuil QVM, and QuTiP, then reports standardized runtime, structural, and distribution metrics. `pytket` is used for circuit analysis and compilation-style metrics, not as an execution backend.

See [USAGE.md](./USAGE.md) for a task-oriented guide to the CLI and Python API, and [CHANGELOG.md](./CHANGELOG.md) for release notes.
For research workflows, see [PROBLEM.md](./PROBLEM.md), [METHODOLOGY.md](./METHODOLOGY.md), [SCHEMA.md](./SCHEMA.md), and [LIMITATIONS.md](./LIMITATIONS.md).

## Features

- Unified `BenchmarkSpec` abstraction for reusable benchmark definitions
- Local-first execution backends with no cloud credentials required
- Built-in benchmarks for GHZ, Bernstein-Vazirani, Deutsch-Jozsa, QFT, random circuits, quantum-volume-style circuits, Grover search, Hamiltonian simulation, and noise sweeps
- Standardized metrics including depth, gate counts, runtime, success probability, and total variation distance
- CLI commands for discovery, backend capability reporting, single runs, backend comparison, and noise sweeps
- Experiment manifests with environment capture and repeated runtime statistics
- Named benchmark suites for smoke, standard, and scaling runs
- Native circuit drawing through Cirq, PennyLane, Braket, and pytket renderers
- JSON/CSV export, summary rankings, and matplotlib plot generation
- Installable in GitHub Codespaces with Python 3.11+

## Backend Support

| Backend | Execution | Notes |
|---|---|---|
| Cirq | `cirq.Simulator` | Supports depolarizing noise injection in this project |
| PennyLane | `default.qubit` / `default.mixed` | Uses local devices only |
| Amazon Braket | `LocalSimulator` only | Offline execution, no AWS credentials required |
| Qiskit Aer | `AerSimulator` | Local Aer simulation, no IBM account required |
| NVIDIA CUDA-Q | local simulator target | Optional local CUDA-Q execution adapter |
| pyQuil QVM | local QVM/quilc runtime | Requires local Forest runtime support |
| QuTiP | local statevector simulation | Useful for physics-oriented local simulation coverage |
| pytket | Analysis only | Used for depth and gate metrics, not execution |
| qBraid | Discovery only | Optional interop/runtime SDK; not used as a local execution backend |
| Q# / QDK | Discovery only | Optional language/runtime SDK; not used as a circuit backend |

## Installation

Install from PyPI:

```bash
python -m pip install quantum-backend-bench
```

Install execution backends as needed:

```bash
python -m pip install "quantum-backend-bench[cirq]"
python -m pip install "quantum-backend-bench[pennylane]"
python -m pip install "quantum-backend-bench[braket]"
python -m pip install "quantum-backend-bench[qiskit]"
python -m pip install "quantum-backend-bench[cudaq]"
python -m pip install "quantum-backend-bench[pyquil]"
python -m pip install "quantum-backend-bench[qutip]"
python -m pip install "quantum-backend-bench[yaml]"
python -m pip install "quantum-backend-bench[all]"
```

Install from a local checkout:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For development tools:

```bash
python -m pip install -e .[dev]
```

For the full local test matrix:

```bash
python -m pip install -e ".[all,dev]"
```

## GitHub Codespaces

The repository includes a Codespaces-ready [`.devcontainer/devcontainer.json`](./.devcontainer/devcontainer.json) using a Python 3.11 base image. On container creation it installs the package in editable mode with development dependencies.

## Quickstart

List available benchmarks, suites, and local integrations:

```bash
quantum-bench list
quantum-bench info
quantum-bench recommend --use-case research
quantum-bench validate
```

Run a single benchmark:

```bash
quantum-bench run ghz --backend cirq --n-qubits 5
quantum-bench run ghz --backend cirq --n-qubits 5 --repeats 5
```

Compare a benchmark across all execution backends and print summary rankings:

```bash
quantum-bench compare qft --backends cirq pennylane braket_local qiskit_aer qutip --n-qubits 5 --summary
```

Run a random circuit:

```bash
quantum-bench run random-circuit --backend braket_local --n-qubits 4 --depth 10 --seed 42
```

Run Grover:

```bash
quantum-bench run grover --backend pennylane --n-qubits 3 --marked-state 101
```

Run Bernstein-Vazirani:

```bash
quantum-bench run bernstein-vazirani --backend cirq --n-qubits 4 --secret-string 101
```

Run Deutsch-Jozsa:

```bash
quantum-bench run deutsch-jozsa --backend cirq --n-qubits 4 --oracle-type balanced --bitmask 101
```

Run Hamiltonian simulation:

```bash
quantum-bench run hamiltonian-sim --backend cirq --n-qubits 4 --time 1.0 --trotter-steps 2
```

Run a noise sweep:

```bash
quantum-bench noise-sweep ghz --backend cirq --n-qubits 5
```

Run a quantum-volume-style circuit:

```bash
quantum-bench run quantum-volume --backend cirq --n-qubits 4 --depth 4 --seed 42
```

Draw a circuit with a native SDK renderer:

```bash
quantum-bench draw ghz --backend cirq --n-qubits 5
quantum-bench draw qft --backend pennylane --n-qubits 5 --save-path artifacts/qft_pennylane.png
quantum-bench draw ghz --backend tket --n-qubits 5 --save-path artifacts/ghz_tket.txt
```

Save JSON and plots:

```bash
quantum-bench compare ghz --backends cirq pennylane braket_local --n-qubits 5 --save-json artifacts/ghz.json --save-plot artifacts/ghz.png
```

Save distribution, heatmap, noise-quality, and suite plots:

```bash
quantum-bench run grover --backend cirq --n-qubits 3 --marked-state 101 --save-distribution artifacts/grover_distribution.png
quantum-bench compare ghz --backends cirq pennylane --n-qubits 4 --save-heatmap artifacts/ghz_heatmap.png
quantum-bench noise-sweep ghz --backend cirq --n-qubits 4 --save-quality-plot artifacts/noise_quality.png
quantum-bench suite smoke --backends cirq --save-suite-plot artifacts/smoke_runtime.png
```

Save CSV:

```bash
quantum-bench compare ghz --backends cirq pennylane --n-qubits 5 --save-csv artifacts/ghz.csv
```

Compare saved results and fail on regressions:

```bash
quantum-bench diff artifacts/baseline.json artifacts/current.json --relative-threshold 0.05 --fail-on-regression
quantum-bench diff artifacts/baseline.csv artifacts/current.csv --metric runtime_seconds
```

Run a named suite:

```bash
quantum-bench suite smoke --backends cirq --summary
quantum-bench suite standard --backends cirq pennylane braket_local --save-csv artifacts/standard.csv
quantum-bench suite standard --list-cases --save-json artifacts/standard_manifest.json
```

Run a reproducible experiment manifest:

```bash
quantum-bench experiment run examples/manifests/runtime_scaling.json
```

For more complete workflows, result interpretation, and Python examples, see [USAGE.md](./USAGE.md).

## Benchmark Suite

### GHZ

Generates GHZ states for configurable qubit counts. Ideal output is concentrated on `00...0` and `11...1`.

### QFT

Implements the Quantum Fourier Transform for structural and runtime comparisons.

### Bernstein-Vazirani

Recovers a hidden bitstring with one oracle query. The final qubit is used as the oracle work qubit, so `--secret-string` must have length `--n-qubits - 1`.

### Deutsch-Jozsa

Runs constant or linear balanced oracle cases. Balanced cases use `--bitmask`; constant cases use `--oracle-type constant --constant-value 0|1`.

### Random Circuit

Builds reproducible random circuits using a fixed gate set and explicit seed control.

### Quantum Volume Style

Builds reproducible shuffled-pair random layers inspired by quantum volume workloads. This is a portable workload, not a formal quantum volume certification routine.

### Grover

Implements a small search benchmark for 2 to 4 qubits and reports marked-state success probability.

### Hamiltonian Simulation

Implements first-order Trotterized evolution for a simple Ising-style Hamiltonian:

```text
H = sum_i Z_i Z_{i+1} + 0.5 * sum_i X_i
```

### Noise Sensitivity

Wraps a base benchmark and sweeps depolarizing noise levels. Noise behavior differs by backend and is reported in result metadata. Braket remains local-only and does not inject noise in this adapter.

## Python API

```python
from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench import build_suite, run_benchmark, summarize_results

benchmark = build_benchmark(n_qubits=5)
results = run_benchmark(benchmark, ["cirq", "pennylane", "braket_local"], shots=1024)
suite_results = [
    result
    for benchmark in build_suite("smoke")
    for result in run_benchmark(benchmark, ["cirq"], shots=128)
]
summary = summarize_results(suite_results)
```

## Project Layout

```text
quantum_backend_bench/
├── backends/
├── benchmarks/
├── core/
├── utils/
└── cli.py
```

Example scripts live in [`examples/`](./examples), with a run order and expected outputs documented in [`examples/README.md`](./examples/README.md). They include backend comparison, GHZ execution, oracle benchmarks, quantum-volume-style execution, suite export, plot generation, circuit diagram export, research manifest generation, repeated-runtime analysis, schema inspection, Markdown report generation, backend capability inspection, and a Cirq noise sweep demo. The plot gallery example uses larger circuits, more shots, and multiple backends so the generated images show non-trivial distributions.

## Development

Run formatting and linting:

```bash
black quantum_backend_bench tests examples
ruff check quantum_backend_bench tests examples
```

Run tests:

```bash
pytest
```

Build and inspect release artifacts:

```bash
python -m build
python -m twine check dist/*
```

Continuous integration is handled by [`.github/workflows/ci.yml`](./.github/workflows/ci.yml), which runs formatting, linting, tests, build, and distribution checks. Publishing is handled by [`.github/workflows/publish.yml`](./.github/workflows/publish.yml) when a version tag such as `v0.1.3` is pushed. The workflow expects PyPI trusted publishing to be configured for this repository.

## Notes

- The project targets standard `pip` environments with Python 3.11 or newer.
- No AWS account, cloud credentials, GPUs, or paid services are required.
- The internal circuit model is intentionally simple to keep backend translation maintainable.
