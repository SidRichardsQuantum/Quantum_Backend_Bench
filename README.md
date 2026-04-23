# Quantum Backend Bench

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.1-green.svg)](./CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![Backends](https://img.shields.io/badge/backends-Cirq%20%7C%20PennyLane%20%7C%20Braket%20Local-purple.svg)](./USAGE.md)
[![Analysis](https://img.shields.io/badge/analysis-pytket-orange.svg)](./README.md#backend-support)

Backend-agnostic benchmarking toolkit for local quantum circuit simulators. The package runs the same benchmark definitions across Cirq, PennyLane, and Amazon Braket `LocalSimulator`, then reports standardized runtime, structural, and distribution metrics. `pytket` is used for circuit analysis and compilation-style metrics, not as an execution backend.

See [USAGE.md](./USAGE.md) for a task-oriented guide to the CLI and Python API, and [CHANGELOG.md](./CHANGELOG.md) for release notes.

## Features

- Unified `BenchmarkSpec` abstraction for reusable benchmark definitions
- Local-only execution backends with no cloud credentials required
- Built-in benchmarks for GHZ, QFT, random circuits, Grover search, Hamiltonian simulation, and noise sweeps
- Standardized metrics including depth, gate counts, runtime, success probability, and total variation distance
- CLI commands for single runs, backend comparison, and noise sweeps
- Native circuit drawing through Cirq, PennyLane, Braket, and pytket renderers
- JSON export and matplotlib plot generation
- Installable in GitHub Codespaces with Python 3.11+

## Backend Support

| Backend | Execution | Notes |
|---|---|---|
| Cirq | `cirq.Simulator` | Supports depolarizing noise injection in this project |
| PennyLane | `default.qubit` / `default.mixed` | Uses local devices only |
| Amazon Braket | `LocalSimulator` only | Offline execution, no AWS credentials required |
| pytket | Analysis only | Used for depth and gate metrics, not execution |

## Installation

Install from PyPI:

```bash
python -m pip install quantum-backend-bench
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

## GitHub Codespaces

The repository includes a Codespaces-ready [`.devcontainer/devcontainer.json`](./.devcontainer/devcontainer.json) using a Python 3.11 base image. On container creation it installs the package in editable mode with development dependencies.

## Quickstart

Run a single benchmark:

```bash
quantum-bench run ghz --backend cirq --n-qubits 5
```

Compare a benchmark across all execution backends:

```bash
quantum-bench compare qft --backends cirq pennylane braket_local --n-qubits 5
```

Run a random circuit:

```bash
quantum-bench run random-circuit --backend braket_local --n-qubits 4 --depth 10 --seed 42
```

Run Grover:

```bash
quantum-bench run grover --backend pennylane --n-qubits 3 --marked-state 101
```

Run Hamiltonian simulation:

```bash
quantum-bench run hamiltonian-sim --backend cirq --n-qubits 4 --time 1.0 --trotter-steps 2
```

Run a noise sweep:

```bash
quantum-bench noise-sweep ghz --backend cirq --n-qubits 5
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

For more complete workflows, result interpretation, and Python examples, see [USAGE.md](./USAGE.md).

## Benchmark Suite

### GHZ

Generates GHZ states for configurable qubit counts. Ideal output is concentrated on `00...0` and `11...1`.

### QFT

Implements the Quantum Fourier Transform for structural and runtime comparisons.

### Random Circuit

Builds reproducible random circuits using a fixed gate set and explicit seed control.

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
from quantum_backend_bench.core.runner import run_benchmark

benchmark = build_benchmark(n_qubits=5)
results = run_benchmark(benchmark, ["cirq", "pennylane", "braket_local"], shots=1024)
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

Example scripts live in [`examples/`](./examples), including backend comparison, GHZ execution, and a Cirq noise sweep demo.

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

Publishing is handled by [`.github/workflows/publish.yml`](./.github/workflows/publish.yml) when a version tag such as `v0.1.1` is pushed. The workflow expects PyPI trusted publishing to be configured for this repository.

## Notes

- The project targets standard `pip` environments with Python 3.11 or newer.
- No AWS account, cloud credentials, GPUs, or paid services are required.
- The internal circuit model is intentionally simple to keep backend translation maintainable.
