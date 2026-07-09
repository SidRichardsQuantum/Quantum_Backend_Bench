# Usage Guide

`quantum-backend-bench` supports two primary workflows:

- CLI-driven benchmarking with `quantum-bench`
- Python-driven benchmarking with `build_benchmark(...)` and `run_benchmark(...)`

The package is designed for local simulator execution only. Cirq, PennyLane, Amazon Braket `LocalSimulator`, Qiskit Aer, CUDA-Q, pyQuil QVM, and QuTiP are supported as execution backends, while `pytket` is used for structural analysis.

For the theoretical background behind shots, distributions, success probability, total variation distance, noise, and the built-in benchmark families, see [THEORY.md](./docs/THEORY.md). For planned SDK interop and translation work, see [ROADMAP.md](./ROADMAP.md).

## Table of Contents

- [Installation](#installation)
- [CLI Usage](#cli-usage)
  - [Discover Benchmarks and Integrations](#discover-benchmarks-and-integrations)
  - [Diagnose Local Readiness](#diagnose-local-readiness)
  - [Choosing Backends](#choosing-backends)
  - [Compatibility Matrix](#compatibility-matrix)
  - [Run Presets, Reports, and Bundles](#run-presets-reports-and-bundles)
  - [Run One Benchmark on One Backend](#run-one-benchmark-on-one-backend)
  - [Compare Backends](#compare-backends)
  - [Run a Noise Sweep](#run-a-noise-sweep)
  - [Run Benchmark Suites](#run-benchmark-suites)
  - [Draw Circuits](#draw-circuits)
  - [Run Experiment Manifests](#run-experiment-manifests)
- [CLI Output](#cli-output)
- [Python API Usage](#python-api-usage)
  - [Minimal Example](#minimal-example)
  - [Selecting Specific Metrics](#selecting-specific-metrics)
  - [Running a Suite from Python](#running-a-suite-from-python)
  - [Noise Sweep from Python](#noise-sweep-from-python)
- [Benchmarks](#benchmarks)
  - [GHZ](#ghz)
  - [QFT](#qft)
  - [Bernstein-Vazirani](#bernstein-vazirani)
  - [Deutsch-Jozsa](#deutsch-jozsa)
  - [Random Circuit](#random-circuit)
  - [Quantum Volume Style](#quantum-volume-style)
  - [Grover](#grover)
  - [Hamiltonian Simulation](#hamiltonian-simulation)
  - [QAOA MaxCut](#qaoa-maxcut)
  - [Noise Sensitivity](#noise-sensitivity)
- [Result Schema](#result-schema)
- [Practical Notes](#practical-notes)
- [Examples](#examples)
- [Development Workflow](#development-workflow)
- [SDK Utility Workflows](#sdk-utility-workflows)
- [Circuit Translation](./docs/CIRCUIT_TRANSLATION.md)
- [Roadmap](./ROADMAP.md)
- [Author](#author)
- [License](#license)

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
python -m pip install "quantum-backend-bench[full]"
```

`all` is the practical Python-only comparison stack. It excludes CUDA-Q and pyQuil so
normal local setup does not pull a large CUDA dependency set or imply that external
Rigetti runtime executables are available. Use `full` when you explicitly want every
Python SDK extra.

Install from a local checkout:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Install development tools:

```bash
python -m pip install -e .[dev]
```

Install the practical local test matrix:

```bash
python -m pip install -e ".[all,dev]"
```

Install every optional Python SDK extra:

```bash
python -m pip install -e ".[full,dev]"
```

Even with `full`, the pyQuil execution test requires non-Python local runtime tools:
`qvm` and `quilc` must be installed separately and available on `PATH`.

## CLI Usage

The CLI entrypoint is:

```bash
quantum-bench
```

Available subcommands:

- `list`
- `info`
- `doctor`
- `recommend`
- `validate`
- `compatibility`
- `sdk-parity`
- `semantic-audit`
- `noise-audit`
- `compile-audit`
- `roundtrip-audit`
- `diff`
- `report`
- `bundle`
- `preset`
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

### Diagnose Local Readiness

Use `doctor` for a compact readiness report with install hints:

```bash
quantum-bench doctor
quantum-bench doctor --strict
```

The default command exits successfully after printing diagnostics. `--strict` exits with status 1 if no execution backend is installed.

Recommend installed backends for a use case:

```bash
quantum-bench recommend --use-case research
quantum-bench recommend --use-case teaching
quantum-bench recommend --use-case noise
```

### Choosing Backends

Use `quantum-bench info`, `quantum-bench doctor`, and `quantum-bench recommend` before comparing results. In general:

- Use Cirq, PennyLane, or Qiskit Aer for noise-sweep studies because this project injects depolarizing noise for those adapters.
- Use Qiskit Aer when you want a common transpilation-inclusive local simulator workflow.
- Use Braket LocalSimulator when you want offline Braket circuit coverage without AWS credentials.
- Use QuTiP when statevector-style local simulation is useful for small physics-oriented cases.
- Use pyQuil only when local `qvm` and `quilc` runtime support is available.
- Treat CUDA-Q availability as platform-sensitive and check it with `doctor` in CI or fresh environments.

### Compatibility Matrix

Show Python, SDK, account/runtime, and CI coverage status for known integrations:

```bash
quantum-bench compatibility
```

Validate installed or selected backends with known-correct small circuits:

```bash
quantum-bench validate
quantum-bench validate --backends cirq pennylane --shots 128 --save-json artifacts/validation.json
```

Audit free local SDK parity and interop behavior:

```bash
quantum-bench sdk-parity
quantum-bench sdk-parity --json
quantum-bench sdk-parity --save-json artifacts/sdk_parity.json --save-csv artifacts/sdk_parity.csv --save-report artifacts/sdk_parity.md
quantum-bench semantic-audit --backends cirq qiskit_aer pennylane --shots 512
quantum-bench compile-audit --backends cirq qiskit_aer
quantum-bench roundtrip-audit --targets cirq qiskit_aer pennylane braket_local --include-hamiltonian --include-workflow
quantum-bench noise-audit
quantum-bench noise-audit --run --backends cirq qiskit_aer --noise-types depolarizing amplitude_damping readout_error
```

`semantic-audit` compares compact shared workloads against neutral exact probabilities. `compile-audit` reports structural deltas and compile/transpile metadata where adapters expose it. `roundtrip-audit` translates neutral circuits to supported local SDK source and back, and `--include-hamiltonian --include-workflow` extends the same check to Pauli Hamiltonians and parameterized local workflows. `noise-audit` prints the noise model matrix by default and executes tiny noisy workloads only with `--run`. Audit commands can write `--save-json`, `--save-csv`, and `--save-report` artifacts.

Compare saved JSON or CSV result files:

```bash
quantum-bench diff artifacts/baseline.json artifacts/current.json
quantum-bench diff artifacts/baseline.csv artifacts/current.csv --metric runtime_seconds
quantum-bench diff artifacts/baseline.json artifacts/current.json --relative-threshold 0.05 --fail-on-regression
```

Execution backend names are:

- `cirq`
- `pennylane`
- `braket_local`
- `qiskit_aer`
- `cudaq`
- `pyquil_qvm`
- `qutip`

### Run Presets, Reports, and Bundles

Packaged presets provide ready-made comparison manifests:

```bash
quantum-bench preset list
quantum-bench preset show runtime --save-json artifacts/runtime_manifest.json
quantum-bench preset run runtime --backends cirq pennylane qiskit_aer --save-json artifacts/runtime.json --save-report artifacts/runtime.md
```

Generate a Markdown report from an existing JSON, JSON bundle, or CSV export:

```bash
quantum-bench report artifacts/runtime.json --output artifacts/runtime_report.md
```

Create a reproducible result bundle with normalized outputs, report, plots, and metadata:

```bash
quantum-bench bundle artifacts/runtime.json --output artifacts/runtime_bundle
quantum-bench bundle artifacts/runtime.csv --output artifacts/runtime_bundle --no-plots
```

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

QAOA MaxCut on Cirq:

```bash
quantum-bench run qaoa-maxcut --backend cirq --n-qubits 4 --graph ring --gamma 0.8 --beta 0.4
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
- `standard`: representative GHZ, oracle, QFT, random circuit, Grover, Hamiltonian simulation, QAOA MaxCut, and quantum-volume-style cases
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

Use `quantum-bench diff` to compare saved result files from two runs. It matches results by benchmark, backend, qubit count, and benchmark parameters, then reports metric deltas. By default it compares `runtime_seconds`, `success_probability`, and `total_variation_distance`. Use repeated `--metric` flags to choose metrics, `--absolute-threshold` or `--relative-threshold` to tolerate expected noise, and `--fail-on-regression` for CI-style gating.

When `--repeats` is greater than 1, `runtime_seconds` is the mean runtime. Raw samples and environment metadata are stored in result metadata. See [SCHEMA.md](./docs/SCHEMA.md) and [METHODOLOGY.md](./docs/METHODOLOGY.md).

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
from quantum_backend_bench import results_to_dataframe

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
from quantum_backend_bench import results_to_dataframe

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

### QAOA MaxCut

Use when you want an optimization-flavored workload. The benchmark builds a single-layer QAOA circuit for line or ring MaxCut graphs and reports success probability as probability mass on optimal cut bitstrings.

### Noise Sensitivity

Use when you want to compare how output quality changes under injected depolarizing noise. Cirq, PennyLane, and Qiskit Aer support noisy execution in this project; other adapters may execute the base circuit without injecting noise and report that in result metadata.

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

Quality metrics should be interpreted with shot count in mind. A lower `total_variation_distance` means the observed distribution is closer to the benchmark's ideal distribution. A higher `success_probability` means the target state appeared more often for benchmarks with a target state, such as Grover. Small shot counts can make both values noisy.

## Practical Notes

- Amazon Braket support is limited to `LocalSimulator`; no AWS credentials are required.
- `pytket` is not used as an execution backend.
- No GPUs or paid cloud services are required.
- Noisy simulation is materially slower than noiseless simulation, especially for larger Cirq runs.
- `--shots`, `--repeats`, and `--noise-levels` are validated by the CLI before backend execution starts.
- Random seeds are applied where backend APIs expose stable seed controls; result metadata reports whether a seed was supported and applied.
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

`plot_gallery.py` uses compact workloads by default, but it is still the heaviest basic example because it renders multiple matplotlib figures and includes noisy simulation.

## Development Workflow

Run formatting and linting:

```bash
black .
ruff check .
```

Run the default core test suite:

```bash
pytest
```

Run optional SDK and generated-site documentation checks explicitly when needed:

```bash
pytest -m optional_sdk
pytest tests/test_docs_links.py -m "docs or not docs"
```

Build release artifacts:

```bash
python -m build
python -m twine check dist/*
```

## SDK Utility Workflows

The CLI includes SDK-facing workflows beyond local benchmark execution:

```bash
quantum-bench export ghz --n-qubits 3 --format openqasm
quantum-bench export ghz --n-qubits 3 --format openqasm3
quantum-bench export ghz --n-qubits 3 --format native --backend cirq
quantum-bench import-qasm artifacts/ghz.qasm3 --name imported_ghz
quantum-bench translate artifacts/ghz.qasm --from-format openqasm --to-format cirq --verify exact --output artifacts/ghz_cirq.py
quantum-bench translate examples/qiskit_circuit.py --from-format qiskit --to-format pennylane --verify exact --output artifacts/circuit_pennylane.py
quantum-bench translate-check examples/translation/qiskit_registers.py --from-format qiskit
quantum-bench translate-check examples/translation/qiskit_registers.py --from-format qiskit --json
quantum-bench translate examples/translation/ghz.qasm --from-format openqasm --to-format cirq --verify exact --save-report artifacts/translation_report.json
quantum-bench translate-hamiltonian examples/translation/ising_hamiltonian.json --from-format pauli-json --to-format pennylane --output artifacts/ising_pennylane.py
quantum-bench translate-observable examples/translation/ising_hamiltonian.json --from-format pauli-json --to-format qiskit_aer
quantum-bench translate-workflow examples/translation/parameterized_workflow.json --to-format qiskit_aer
quantum-bench translate-result examples/translation/qiskit_counts_result.json --from-format qiskit-counts-json
quantum-bench group-pauli-terms examples/translation/ising_hamiltonian.json --from-format pauli-json
quantum-bench translation-audit
quantum-bench translation-audit --from-format qiskit --to-format qiskit_aer --json
quantum-bench exact ghz --n-qubits 3 --top-k 4 --amplitudes --observable ZZI
quantum-bench run random-circuit --backend cirq --sweep n-qubits=2:5 --sweep depth=4,8
quantum-bench noise-sweep ghz --backend cirq --noise-type bit_flip
quantum-bench diagnose artifacts/ghz.json
quantum-bench hardware qaoa-maxcut --n-qubits 4 --output artifacts/hardware_qaoa --provider ibm --qasm-version openqasm3 --backend-hint provider-device
quantum-bench recommend --needs-noise --no-external-runtime
```

`translate` converts supported OpenQASM, internal JSON, or static SDK circuit snippets through the package's neutral circuit model. `translate-hamiltonian` and `translate-observable` convert weighted Pauli terms through the neutral Pauli Hamiltonian model with canonical or small dense-matrix verification. `translate-workflow`, `translate-result`, and `group-pauli-terms` extend that into parameterized workflow JSON, first-pass static SDK workflow imports, parameter bindings, measurement/expectation requests, local execution wrappers, neutral result objects, and qubit-wise Pauli grouping. Generated workflow scripts print neutral result JSON and embed a canonical `workflow_spec` for verification. SDK output is limited to free local Python SDK APIs for now: Cirq, Qiskit, PennyLane, and Braket LocalSimulator. Unsupported dynamic Python constructs are rejected instead of rewritten approximately. Neutral `internal-json`, `pauli-json`, `workflow-json`, and `result-json` payloads are versioned with `schema_version: "0.1"`; saved translation reports include `schema_metadata`, and `translation-audit --json` emits the current SDK coverage matrix. See [Circuit Translation](./docs/CIRCUIT_TRANSLATION.md) and [Schema](./docs/SCHEMA.md) for supported gates, static Python patterns, diagnostics, runnable-script output, report artifacts, JSON Schema files, examples, caveats, and verification modes.

Result tables, CSV records, and Markdown reports include compile/transpile metadata when a backend provides it, such as Qiskit Aer `compile_seconds`, compiled depth, compiled gate counts, and compile toolchain. New applied workloads include `vqe-ansatz`, `phase-estimation`, `amplitude-estimation`, and `quantum-kernel`. The `hardware` command writes OpenQASM and provider-specific caveats for IBM, Braket, Rigetti, or generic submission workflows, but it does not submit cloud jobs or handle credentials. SDK tutorial notebooks live in `notebooks/04_sdk_cirq_workflow.ipynb` through `notebooks/08_sdk_qutip_workflow.ipynb` and include readable result summaries, top-state plots, saved artifacts, and verification checks. `notebooks/09_circuit_translation_workflow.ipynb` covers all-target local SDK circuit translation, SDK-native diagram comparison, reports, runner output, and diagnostics. `notebooks/10_observable_hamiltonian_translation_workflow.ipynb` covers Pauli observable and Hamiltonian translation with canonical verification. `notebooks/11_parameterized_workflow_translation.ipynb` covers parameterized workflow translation, result normalization, and Pauli grouping.

---

## Author

Sid Richards

- LinkedIn: [sid-richards-21374b30b](https://www.linkedin.com/in/sid-richards-21374b30b/)
- GitHub: [SidRichardsQuantum](https://github.com/SidRichardsQuantum)

## License

MIT. See [LICENSE](LICENSE).
