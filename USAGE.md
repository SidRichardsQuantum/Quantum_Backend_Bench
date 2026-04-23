# Usage Guide

`quantum-backend-bench` supports two primary workflows:

- CLI-driven benchmarking with `quantum-bench`
- Python-driven benchmarking with `build_benchmark(...)` and `run_benchmark(...)`

The package is designed for local simulator execution only. Cirq, PennyLane, and Amazon Braket `LocalSimulator` are supported as execution backends, while `pytket` is used for structural analysis.

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

Install development tools:

```bash
python -m pip install -e .[dev]
```

## CLI Usage

The CLI entrypoint is:

```bash
quantum-bench
```

Available subcommands:

- `run`
- `compare`
- `noise-sweep`
- `draw`

### Run One Benchmark on One Backend

GHZ on Cirq:

```bash
quantum-bench run ghz --backend cirq --n-qubits 5
```

Grover on PennyLane:

```bash
quantum-bench run grover --backend pennylane --n-qubits 3 --marked-state 101
```

Random circuit on Braket local:

```bash
quantum-bench run random-circuit --backend braket_local --n-qubits 4 --depth 10 --seed 42
```

Hamiltonian simulation on Cirq:

```bash
quantum-bench run hamiltonian-sim --backend cirq --n-qubits 4 --time 1.0 --trotter-steps 2
```

### Compare Backends

Compare QFT across all execution backends:

```bash
quantum-bench compare qft --backends cirq pennylane braket_local --n-qubits 5
```

Compare GHZ and save artifacts:

```bash
quantum-bench compare ghz \
  --backends cirq pennylane braket_local \
  --n-qubits 5 \
  --save-json artifacts/ghz_compare.json \
  --save-plot artifacts/ghz_compare.png
```

### Run a Noise Sweep

Run a depolarizing noise sweep over GHZ with Cirq:

```bash
quantum-bench noise-sweep ghz --backend cirq --n-qubits 5
```

Use custom noise levels:

```bash
quantum-bench noise-sweep ghz \
  --backend cirq \
  --n-qubits 5 \
  --noise-levels 0.0 0.001 0.005 0.01 0.02
```

### Draw Circuits

Render a textual circuit diagram with Cirq:

```bash
quantum-bench draw ghz --backend cirq --n-qubits 5
```

Render with Braket local's native circuit object:

```bash
quantum-bench draw random-circuit --backend braket_local --n-qubits 4 --depth 10 --seed 42
```

Render with pytket and save the textual diagram:

```bash
quantum-bench draw qft --backend tket --n-qubits 5 --save-path artifacts/qft_tket.txt
```

Render with PennyLane and save a plotted figure:

```bash
quantum-bench draw ghz --backend pennylane --n-qubits 5 --save-path artifacts/ghz_pennylane.png
```

Behavior by backend:

- `cirq`: prints Cirq's text diagram and can save it as text
- `pennylane`: prints PennyLane's text drawer and saves a matplotlib figure when `--save-path` is provided
- `braket_local`: prints Braket's native circuit representation and can save it as text
- `tket`: prints pytket's textual representation and can save it as text

## CLI Output

Commands print a plain-text comparison table with metrics such as:

- `runtime_seconds`
- `depth`
- `gate_count`
- `two_qubit_gate_count`
- `success_prob`

When supported by the benchmark, result payloads also include:

- measurement counts
- normalized measurement distributions
- total variation distance from an ideal distribution

Use `--save-json` to persist the full result objects and `--save-plot` to write a runtime/depth bar chart.

## Python API Usage

### Minimal Example

```python
from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark

benchmark = build_benchmark(n_qubits=5)
results = run_benchmark(
    benchmark,
    backends=["cirq", "pennylane", "braket_local"],
    shots=1024,
)

for result in results:
    print(result["backend"], result["metrics"]["runtime_seconds"])
```

### Selecting Specific Metrics

```python
from quantum_backend_bench.benchmarks.qft import build_benchmark
from quantum_backend_bench.core.runner import run_benchmark

benchmark = build_benchmark(n_qubits=5)
results = run_benchmark(
    benchmark,
    backends=["cirq", "pennylane"],
    metrics=["depth", "gate_count", "runtime_seconds"],
    shots=512,
)
```

### Noise Sweep from Python

```python
from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench.benchmarks.noise_sensitivity import build_benchmark as build_noise_suite
from quantum_backend_bench.core.runner import run_benchmark

base = build_benchmark(n_qubits=5)
all_results = []

for noisy_spec in build_noise_suite(base, noise_levels=[0.0, 0.005, 0.01]):
    all_results.extend(run_benchmark(noisy_spec, backends=["cirq"], shots=128))
```

## Benchmarks

### GHZ

Use when you want an entanglement-oriented sanity check. Ideal output mass is split between `00...0` and `11...1`.

### QFT

Use when you care about circuit structure, controlled-phase usage, and cross-backend runtime on a more interaction-heavy circuit.

### Random Circuit

Use when you want reproducible synthetic workloads. Control reproducibility with `seed`, and scale difficulty with `n_qubits` and `depth`.

### Grover

Use when you want a benchmark with a target success state. This is the main built-in benchmark for `success_probability`.

### Hamiltonian Simulation

Use when you want a small, documented time-evolution workload based on a simple Ising-style Hamiltonian.

### Noise Sensitivity

Use when you want to compare how output quality changes under injected depolarizing noise. Cirq and PennyLane support noisy execution in this project; Braket local remains local-only but does not inject noise in this adapter.

## Result Schema

`run_benchmark(...)` returns a list of dictionaries. Each result includes:

```python
{
    "benchmark": "ghz",
    "backend": "cirq",
    "n_qubits": 5,
    "shots": 1024,
    "parameters": {...},
    "metrics": {...},
    "counts": {...},
    "metadata": {...},
}
```

Important metric keys:

- `depth`
- `gate_count`
- `two_qubit_gate_count`
- `runtime_seconds`
- `measurement_distribution`
- `success_probability`
- `total_variation_distance`

If a metric cannot be provided consistently for a given benchmark or backend, the value may be `None`.

## Practical Notes

- Amazon Braket support is limited to `LocalSimulator`; no AWS credentials are required.
- `pytket` is not used as an execution backend.
- No GPUs or paid cloud services are required.
- Noisy simulation is materially slower than noiseless simulation, especially for larger Cirq runs.
- This package intentionally uses a simple internal circuit description to keep per-backend translation maintainable.

## Examples

The repository includes example scripts:

- [`examples/basic_benchmark.py`](./examples/basic_benchmark.py)
- [`examples/compare_backends.py`](./examples/compare_backends.py)
- [`examples/noise_sweep_demo.py`](./examples/noise_sweep_demo.py)

## Development Workflow

Run formatting and linting:

```bash
black .
ruff check .
```

Run tests:

```bash
pytest
```

Build release artifacts:

```bash
python -m build
python -m twine check dist/*
```
