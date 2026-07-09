# Quantum Backend Bench

[![CI](https://github.com/SidRichardsQuantum/Quantum_Backend_Bench/actions/workflows/ci.yml/badge.svg)](https://github.com/SidRichardsQuantum/Quantum_Backend_Bench/actions/workflows/ci.yml)
[![Pages](https://github.com/SidRichardsQuantum/Quantum_Backend_Bench/actions/workflows/pages.yml/badge.svg)](https://github.com/SidRichardsQuantum/Quantum_Backend_Bench/actions/workflows/pages.yml)
[![PyPI](https://img.shields.io/pypi/v/quantum-backend-bench.svg)](https://pypi.org/project/quantum-backend-bench/)
[![Python](https://img.shields.io/pypi/pyversions/quantum-backend-bench.svg)](https://pypi.org/project/quantum-backend-bench/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![Backends](https://img.shields.io/badge/backends-local%20simulators-purple.svg)](./docs/COMPATIBILITY.md)

PyPI: [https://pypi.org/project/quantum-backend-bench/](https://pypi.org/project/quantum-backend-bench/)

Website: [https://sidrichardsquantum.github.io/Quantum_Backend_Bench/](https://sidrichardsquantum.github.io/Quantum_Backend_Bench/)

Backend-agnostic benchmarking toolkit for local quantum circuit simulators. The package runs the same benchmark definitions across local simulator adapters such as Cirq, PennyLane, Amazon Braket `LocalSimulator`, Qiskit Aer, CUDA-Q, pyQuil QVM, and QuTiP, then reports standardized runtime, structural, and distribution metrics. `pytket` is used for circuit analysis and compilation-style metrics, not as an execution backend.

See [USAGE.md](./USAGE.md) for a task-oriented guide to the CLI and Python API, [ROADMAP.md](./ROADMAP.md) for planned interop and translation work, and [CHANGELOG.md](./CHANGELOG.md) for release notes.
For research workflows and interpretation, see [PROBLEM.md](./docs/PROBLEM.md), [THEORY.md](./docs/THEORY.md), [METHODOLOGY.md](./docs/METHODOLOGY.md), [RESULTS.md](./docs/RESULTS.md), [SCHEMA.md](./docs/SCHEMA.md), [COMPATIBILITY.md](./docs/COMPATIBILITY.md), and [LIMITATIONS.md](./docs/LIMITATIONS.md).

## Table of Contents

- [Features](#features)
- [Backend Support](#backend-support)
- [Compatibility](#compatibility)
- [Installation](#installation)
- [Two-Minute First Run](#two-minute-first-run)
- [GitHub Codespaces](#github-codespaces)
- [Quickstart](#quickstart)
- [Benchmark Suite](#benchmark-suite)
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
- [Python API](#python-api)
- [Result Bundles and DataFrames](#result-bundles-and-dataframes)
- [Tutorial Notebooks](#tutorial-notebooks)
- [Project Layout](#project-layout)
- [Development](#development)
- [SDK Utility Workflows](#sdk-utility-workflows)
- [Circuit Translation](./docs/CIRCUIT_TRANSLATION.md)
- [Roadmap](./ROADMAP.md)
- [Notes](#notes)
- [Author](#author)
- [License](#license)

## Features

- Unified `BenchmarkSpec` abstraction for reusable benchmark definitions
- Local-first execution backends with no cloud credentials required
- Built-in benchmarks for GHZ, Bernstein-Vazirani, Deutsch-Jozsa, QFT, random circuits, quantum-volume-style circuits, Grover search, Hamiltonian simulation, QAOA MaxCut, and noise sweeps
- Standardized metrics including depth, gate counts, runtime, success probability, and total variation distance
- CLI commands for discovery, backend capability reporting, single runs, backend comparison, presets, reports, SDK parity scorecards, semantic audits, round-trip translation audits, compilation audits, and noise sweeps
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
| Qiskit Aer | `AerSimulator` | Local Aer simulation with depolarizing noise injection support |
| NVIDIA CUDA-Q | local simulator target | Optional local CUDA-Q execution adapter |
| pyQuil QVM | local QVM/quilc runtime | Requires local Forest runtime support |
| QuTiP | local statevector simulation | Useful for physics-oriented local simulation coverage |
| pytket | Analysis only | Used for depth and gate metrics, not execution |
| qBraid | Discovery only | Optional interop/runtime SDK; not used as a local execution backend |
| Q# / QDK | Discovery only | Optional language/runtime SDK; not used as a circuit backend |

The core execution path is intentionally free, local, and credential-free. Backends
that require cloud accounts, provider billing, remote queues, or private services
should stay outside the default workflow unless they are added as clearly optional
provider adapters. The default recommendation is to keep new-user benchmarking
instantly accessible through local simulators.

## Compatibility

See [COMPATIBILITY.md](./docs/COMPATIBILITY.md) for the supported Python versions,
optional SDK extras, local runtime requirements, and CI coverage status for each
integration.

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
python -m pip install "quantum-backend-bench[full]"
```

The default package and `.[dev]` workflow are self-contained Python installs. The `all`
extra is the practical Python-only comparison stack and intentionally excludes CUDA-Q
and pyQuil. Use `full` only when you explicitly want every Python SDK extra, including
heavy or external-runtime-backed adapters.

Install from a local checkout:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For development tools:

```bash
python -m pip install -e .[dev]
```

For the practical local test matrix:

```bash
python -m pip install -e ".[all,dev]"
```

For the exhaustive optional SDK matrix:

```bash
python -m pip install -e ".[full,dev]"
```

The pyQuil execution test also requires local `qvm` and `quilc` executables on `PATH`.
Those are external Rigetti runtime tools and are not installed by pip extras.

## Two-Minute First Run

For the shortest public path, install the Cirq extra and run the smoke workflow:

```bash
python -m pip install "quantum-backend-bench[cirq]"
quantum-bench run ghz --backend cirq --n-qubits 3 --shots 128 --summary
quantum-bench suite smoke --backends cirq --shots 128 --summary
```

Expected output is a compact table with runtime, depth, gate counts, and benchmark
quality metrics, followed by summary rankings. A saved reference bundle for this
workflow is available under
[`examples/reference_results/cirq_smoke_2026-06-03/`](./examples/reference_results/cirq_smoke_2026-06-03/).

## GitHub Codespaces

The repository includes a Codespaces-ready [`.devcontainer/devcontainer.json`](./.devcontainer/devcontainer.json) using a Python 3.11 base image. On container creation it installs the package in editable mode with development dependencies.

## Quickstart

List available benchmarks, suites, and local integrations:

```bash
quantum-bench list
quantum-bench info
quantum-bench doctor
quantum-bench recommend --use-case research
quantum-bench compatibility
quantum-bench sdk-parity
quantum-bench semantic-audit --backends cirq qiskit_aer
quantum-bench roundtrip-audit --include-hamiltonian --include-workflow
quantum-bench compile-audit --backends cirq qiskit_aer
quantum-bench noise-audit
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

Run QAOA MaxCut:

```bash
quantum-bench run qaoa-maxcut --backend cirq --n-qubits 4 --graph ring --gamma 0.8 --beta 0.4
```

Run a noise sweep:

```bash
quantum-bench noise-sweep ghz --backend cirq --n-qubits 5
```

Run free local SDK audits:

```bash
quantum-bench sdk-parity --save-json artifacts/sdk_parity.json
quantum-bench semantic-audit --backends cirq qiskit_aer pennylane
quantum-bench roundtrip-audit --targets cirq qiskit_aer pennylane braket_local --include-hamiltonian --include-workflow
quantum-bench compile-audit --backends cirq qiskit_aer
quantum-bench noise-audit
quantum-bench noise-audit --run --backends cirq qiskit_aer --noise-types depolarizing amplitude_damping readout_error
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
quantum-bench bundle artifacts/current.json --output artifacts/current_bundle
quantum-bench diff artifacts/baseline.csv artifacts/current.csv --metric runtime_seconds
```

Generate a Markdown report:

```bash
quantum-bench report artifacts/current.json --output artifacts/current_report.md
```

Use packaged comparison presets:

```bash
quantum-bench preset list
quantum-bench preset show algorithmic --save-json artifacts/algorithmic_manifest.json
quantum-bench preset run runtime --backends cirq pennylane qiskit_aer --save-report artifacts/runtime_report.md
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

### QAOA MaxCut

Builds a single-layer QAOA circuit for line or ring MaxCut instances and reports success probability as probability mass on optimal cut bitstrings.

### Noise Sensitivity

Wraps a base benchmark and sweeps depolarizing noise levels. Noise behavior differs by backend and is reported in result metadata. Cirq, PennyLane, and Qiskit Aer inject depolarizing noise in this project; other adapters may report the request without applying noise.

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

## Result Bundles and DataFrames

Create a shareable result bundle from any saved JSON or CSV result file:

```bash
quantum-bench bundle artifacts/results.json --output artifacts/results_bundle
```

The bundle contains normalized JSON/CSV outputs, flattened records, a Markdown
report, plots when matplotlib is available, environment metadata when present, and
a README for interpretation. Python users can also flatten results directly:

```python
from quantum_backend_bench import results_to_dataframe

frame = results_to_dataframe("artifacts/results.json")
```

## Tutorial Notebooks

The [`notebooks/`](./notebooks/) directory contains succinct package-client tutorials. Each notebook starts with problem context, quantum-advantage scope, and parameter definitions, then uses readable tables, plots where useful, saved artifacts, and verification checks.

- [`01_quickstart_cirq.ipynb`](./notebooks/01_quickstart_cirq.ipynb): GHZ and smoke-suite workflow on the free local Cirq simulator.
- [`02_compare_local_simulators.ipynb`](./notebooks/02_compare_local_simulators.ipynb): installed local simulator comparison for GHZ and QFT.
- [`03_hamiltonian_simulation_case_study.ipynb`](./notebooks/03_hamiltonian_simulation_case_study.ipynb): small Ising-style Hamiltonian simulation scaling study.
- [`04_sdk_cirq_workflow.ipynb`](./notebooks/04_sdk_cirq_workflow.ipynb) through [`08_sdk_qutip_workflow.ipynb`](./notebooks/08_sdk_qutip_workflow.ipynb): compact SDK export, execution, plotting, artifact, and verification workflows for Cirq, Qiskit Aer, PennyLane, Braket LocalSimulator, and QuTiP.
- [`09_circuit_translation_workflow.ipynb`](./notebooks/09_circuit_translation_workflow.ipynb): all-target local SDK circuit translation with native diagram comparison, reports, runner output, and diagnostics.
- [`10_observable_hamiltonian_translation_workflow.ipynb`](./notebooks/10_observable_hamiltonian_translation_workflow.ipynb): Pauli observable and Hamiltonian translation across local SDK formats with canonical verification.
- [`11_parameterized_workflow_translation.ipynb`](./notebooks/11_parameterized_workflow_translation.ipynb): parameterized workflow translation, canonical workflow verification, result normalization, and Pauli grouping.

Install notebook helpers with:

```bash
python -m pip install -e ".[cirq,plot,notebooks]"
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

Example scripts live in [`examples/`](./examples), with a run order and expected outputs documented in [`examples/README.md`](./examples/README.md). They include backend comparison, GHZ execution, oracle benchmarks, quantum-volume-style execution, suite export, plot generation, circuit diagram export, research manifest generation, repeated-runtime analysis, schema inspection, Markdown report generation, backend capability inspection, and a Cirq noise sweep demo. The plot gallery example uses compact workloads by default, but remains the heaviest basic example because it renders multiple plots and includes noisy simulation.

## Development

Run formatting and linting:

```bash
black quantum_backend_bench tests examples
ruff check quantum_backend_bench tests examples
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

Build and inspect release artifacts:

```bash
python -m build
python -m twine check dist/*
```

Continuous integration is handled by [`.github/workflows/ci.yml`](./.github/workflows/ci.yml), which runs formatting, linting, tests, documentation link validation, Cirq smoke regression checks, package builds, and distribution checks. Publishing is handled by [`.github/workflows/publish.yml`](./.github/workflows/publish.yml) when a version tag such as `v0.2.8` is pushed. The workflow expects PyPI trusted publishing to be configured for this repository.

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

## Notes

- The project targets standard `pip` environments with Python 3.11 or newer.
- No AWS account, cloud credentials, GPUs, or paid services are required.
- The internal circuit model is intentionally simple to keep backend translation maintainable.

---

## Author

Sid Richards

- LinkedIn: [sid-richards-21374b30b](https://www.linkedin.com/in/sid-richards-21374b30b/)
- GitHub: [SidRichardsQuantum](https://github.com/SidRichardsQuantum)

## License

MIT. See [LICENSE](LICENSE).
