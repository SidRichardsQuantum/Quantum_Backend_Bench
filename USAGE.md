# Usage Guide

`quantum-backend-bench` supports two primary workflows:

- CLI-driven benchmarking with `quantum-bench`
- Python-driven benchmarking with `build_benchmark(...)` and `run_benchmark(...)`

The package is designed for local simulator execution only. Cirq, PennyLane, Amazon Braket `LocalSimulator`, Qiskit Aer, CUDA-Q, pyQuil QVM, and QuTiP are supported as execution backends, while `pytket` is used for structural analysis.

## Installation

Install from PyPI:

```bash
python -m pip install quantum-backend-bench
```

Install only the backend integrations you need:

```bash
python -m pip install "quantum-backend-bench[cirq]"
python -m pip install "quantum-backend-bench[pennylane]"
python -m pip install "quantum-backend-bench[braket]"
python -m pip install "quantum-backend-bench[tket]"
python -m pip install "quantum-backend-bench[plot]"
python -m pip install "quantum-backend-bench[qiskit]"
python -m pip install "quantum-backend-bench[cudaq]"
python -m pip install "quantum-backend-bench[pyquil]"
python -m pip install "quantum-backend-bench[qutip]"
python -m pip install "quantum-backend-bench[qbraid]"
python -m pip install "quantum-backend-bench[qsharp]"
python -m pip install "quantum-backend-bench[all]"
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

Install everything needed for the full local test matrix:

```bash
python -m pip install -e ".[all,dev]"
```

## CLI Usage

The CLI entrypoint is:

```bash
quantum-bench
```

Available subcommands:

- `list`
- `info`
- `recommend`
- `validate`
- `run`
- `compare`
- `noise-sweep`
- `suite`
- `draw`
- `experiment`

### Discover Benchmarks and Integrations

List available benchmarks and suites:

```bash
quantum-bench list
quantum-bench list --kind benchmarks
quantum-bench list --kind suites
```

Show installed and missing backend, analysis, and plotting integrations:

```bash
quantum-bench info
```

Recommend installed backends for a use case:

```bash
quantum-bench recommend --use-case research
quantum-bench recommend --use-case teaching
quantum-bench recommend --use-case noise
```

Validate installed or selected backends with known-correct small circuits:

```bash
quantum-bench validate
quantum-bench validate --backends cirq pennylane --shots 128 --save-json artifacts/validation.json
```

Execution backend names are:

- `cirq`
- `pennylane`
- `braket_local`
- `qiskit_aer`
- `cudaq`
- `pyquil_qvm`
- `qutip`

`qbraid` and `qsharp` are reported by `quantum-bench info` as optional ecosystem integrations, but they are not execution backends in this local circuit adapter.

### Run One Benchmark on One Backend

GHZ on Cirq:

```bash
quantum-bench run ghz --backend cirq --n-qubits 5
quantum-bench run ghz --backend cirq --n-qubits 5 --repeats 5
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

Bernstein-Vazirani on Cirq:

```bash
quantum-bench run bernstein-vazirani --backend cirq --n-qubits 4 --secret-string 101
```

Deutsch-Jozsa on Cirq:

```bash
quantum-bench run deutsch-jozsa --backend cirq --n-qubits 4 --oracle-type balanced --bitmask 101
quantum-bench run deutsch-jozsa --backend cirq --n-qubits 4 --oracle-type constant --constant-value 1
```

Quantum-volume-style circuit on Cirq:

```bash
quantum-bench run quantum-volume --backend cirq --n-qubits 4 --depth 4 --seed 42
```

### Compare Backends

Compare QFT across all execution backends:

```bash
quantum-bench compare qft --backends cirq pennylane braket_local qiskit_aer qutip --n-qubits 5
```

Compare GHZ and save artifacts:

```bash
quantum-bench compare ghz \
  --backends cirq pennylane braket_local \
  --n-qubits 5 \
  --save-json artifacts/ghz_compare.json \
  --save-csv artifacts/ghz_compare.csv \
  --save-plot artifacts/ghz_compare.png
```

Print fastest/lowest-depth/best-quality summary rankings:

```bash
quantum-bench compare ghz \
  --backends cirq pennylane braket_local \
  --n-qubits 5 \
  --summary
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

### Run Benchmark Suites

Suites run multiple benchmark presets with one command:

```bash
quantum-bench suite smoke --backends cirq --summary
quantum-bench suite standard --backends cirq pennylane braket_local --save-csv artifacts/standard.csv
quantum-bench suite scaling --backends cirq --shots 256 --save-json artifacts/scaling.json
```

Preview suite cases without running them:

```bash
quantum-bench suite standard --list-cases
quantum-bench suite standard --dry-run --save-json artifacts/standard_manifest.json
```

Available suites:

- `smoke`: small GHZ, oracle, and Grover checks for quick validation
- `standard`: representative GHZ, oracle, QFT, random circuit, Grover, Hamiltonian simulation, and quantum-volume-style cases
- `scaling`: repeated GHZ, QFT, quantum-volume-style, and random-circuit cases at larger sizes or depths

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

### Run Experiment Manifests

Experiment manifests make benchmark runs reproducible and research-friendly:

```bash
quantum-bench experiment run examples/manifests/runtime_scaling.json
quantum-bench experiment run examples/manifests/noise_sensitivity.json
quantum-bench experiment run examples/manifests/structure_vs_runtime.json
```

Manifests can set `backends`, `shots`, `repeats`, benchmark cases, and output paths. JSON works with the standard library. YAML files require `PyYAML`, available with:

```bash
python -m pip install "quantum-backend-bench[yaml]"
```

Research-oriented example helpers:

```bash
python examples/backend_capability_matrix.py
python examples/generate_manifest.py
python examples/noise_manifest_builder.py
python examples/repeated_runtime_analysis.py
python examples/schema_walkthrough.py
python examples/experiment_report.py
```

`schema_walkthrough.py` and `experiment_report.py` expect an experiment bundle such as `artifacts/research/runtime_scaling.json`.

See [`examples/README.md`](./examples/README.md) for the recommended run order and expected artifacts.

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

Use `--summary` to print per-case rankings, `--save-json` to persist the full result objects, `--save-csv` for spreadsheet-friendly output, and `--save-plot` to write a runtime/depth bar chart.

Result JSON includes standardized metadata fields such as `benchmark_family`, `case_label`, `depth`, `seed`, `oracle_type`, and `noise_level` when applicable. CSV exports include `case_label` and `benchmark_family` columns for easier spreadsheet grouping.

When `--repeats` is greater than 1, `runtime_seconds` is the mean runtime. Raw samples and environment metadata are stored in result metadata. See [SCHEMA.md](./SCHEMA.md) and [METHODOLOGY.md](./METHODOLOGY.md).

Additional image outputs:

- `--save-distribution`: measured bitstring probability bar charts
- `--save-heatmap`: top bitstring probability heatmap
- `--save-quality-plot`: noise level vs TVD/success probability
- `--save-suite-plot`: runtime chart for suite or multi-benchmark results

Plots display measured computational basis states in bra-ket notation, such as `|101>`.

## Python API Usage

### Minimal Example

```python
from quantum_backend_bench.benchmarks.ghz import build_benchmark
from quantum_backend_bench import run_benchmark

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

### Running a Suite from Python

```python
from quantum_backend_bench import build_suite, run_benchmark, summarize_results

results = []
for benchmark in build_suite("smoke"):
    results.extend(run_benchmark(benchmark, backends=["cirq"], shots=128))

summary = summarize_results(results)
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

### Bernstein-Vazirani

Use when you want a deterministic oracle benchmark with a known success state. The final qubit is an oracle work qubit, so a 4-qubit run uses a 3-bit secret string.

### Deutsch-Jozsa

Use when you want a deterministic constant-vs-balanced oracle workload. Linear balanced cases report the bitmask as the expected measurement state; constant cases report the all-zero input register.

### Random Circuit

Use when you want reproducible synthetic workloads. Control reproducibility with `seed`, and scale difficulty with `n_qubits` and `depth`.

### Quantum Volume Style

Use when you want shuffled-pair random layers with more structure than the generic random circuit benchmark. This workload is inspired by quantum volume circuits but is not a certification routine.

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
- [`examples/circuit_diagrams.py`](./examples/circuit_diagrams.py)
- [`examples/compare_backends.py`](./examples/compare_backends.py)
- [`examples/noise_sweep_demo.py`](./examples/noise_sweep_demo.py)
- [`examples/oracle_benchmarks.py`](./examples/oracle_benchmarks.py)
- [`examples/plot_gallery.py`](./examples/plot_gallery.py)
- [`examples/quantum_volume_demo.py`](./examples/quantum_volume_demo.py)
- [`examples/suite_export.py`](./examples/suite_export.py)

Run them from a local checkout:

```bash
python examples/basic_benchmark.py
python examples/circuit_diagrams.py
python examples/oracle_benchmarks.py
python examples/plot_gallery.py
python examples/quantum_volume_demo.py
python examples/suite_export.py
```

`plot_gallery.py` intentionally uses larger shot counts, multiple backends, a 0% to 5% GHZ noise sweep, and larger circuits so the generated images contain non-trivial distributions and comparisons.

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
