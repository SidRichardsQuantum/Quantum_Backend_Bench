# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

## [0.2.3] - 2026-06-03

### Added

- Shared notebook utility helpers for artifact paths, result summaries, top-state tables, measurement-series extraction, and tutorial verification checks.
- Generated notebook-results documentation pipeline that rebuilds `docs/RESULTS.md`, JSON/CSV assets, and PNG plots from executed notebook artifacts.
- CI stale-result checks for notebook-generated results and documentation assets.
- Packaging tests that keep moved docs and generated notebook result assets included in source distributions.

### Changed

- Moved long-form project documentation from the repository root into `docs/` and updated README, usage, Pages, packaging, and link validation paths.
- Renumbered SDK workflow notebooks to keep tutorial notebook ordering unique and contiguous.
- Refactored tutorial notebooks to use the shared notebook helpers and keep committed notebooks output-free with standard Python kernel metadata.
- Updated the generated site build so `results.html` is rendered from notebook-derived tables, plots, and raw artifacts.
- Scrubbed reference-result bundles to remove volatile runtime, package, environment, and git metadata while preserving deterministic structural and quality metrics.
- Expanded CI and Pages workflows to lint docs scripts, install documentation plotting dependencies, watch moved docs paths, and validate generated notebook result freshness.

### Fixed

- Adjusted the smoke-suite Grover case to use a valid single marked-state amplification iteration for the configured qubit count.
- Fixed documentation site imports so the Pages builder works both as a direct script and as an imported test module.

## [0.2.2] - 2026-06-03

### Added

- SDK utility CLI commands for circuit export, OpenQASM import, exact probability/amplitude inspection, result-parity diagnosis, and hardware-preparation artifact generation.
- Applied workload builders for `vqe-ansatz`, `phase-estimation`, `amplitude-estimation`, and `quantum-kernel`.
- Parameter-sweep support for `quantum-bench run`, `quantum-bench compare`, and experiment manifests.
- Noise model selection for `quantum-bench noise-sweep`, including bit-flip, phase-flip, amplitude-damping, and readout-error modes where supported by backend adapters.
- SDK workflow notebooks for Cirq, Qiskit Aer, PennyLane, Braket LocalSimulator, and QuTiP/statevector usage.
- Notebook result cells with readable benchmark tables, key metric summaries, top-state probability plots, saved artifacts, and verification checks.

### Changed

- Result tables, CSV records, and Markdown reports now include compile/transpile metadata when backends provide it.
- `quantum-bench recommend` now supports constraint filters for noise support, exact statevectors, external runtimes, maximum qubits, and Python version notes.
- Cirq, PennyLane, and Qiskit adapters now report richer compile metadata for supported executions.
- README and usage documentation now include the SDK utility workflows and new applied workloads.
- Tutorial notebooks now open with problem context, quantum-advantage notes, SDK/backend rationale, and variable/parameter definitions.

## [0.2.1] - 2026-06-03

### Added

- CI docs-link validation for Markdown sources and generated GitHub Pages output.
- CI Cirq smoke regression gate that compares deterministic quality and structure metrics against the checked-in reference bundle.
- `docs` optional dependency extra for local documentation build and validation tooling.
- pyQuil package-level circuit-construction smoke coverage that does not require local `qvm` or `quilc` executables.

### Changed

- Optional-backend CI smoke jobs now fail when selected tests silently skip instead of reporting a false green run.
- Default local `pytest` runs now focus on the core suite; optional SDK and generated-site docs checks are selected explicitly in CI or with pytest markers.
- Generated Pages output now includes linked repository assets such as examples, notebooks, workflow files, devcontainer metadata, and the license.

## [0.2.0] - 2026-06-03

### Added

- `quantum-bench compatibility` for reporting Python support, installed SDK integrations, account/runtime requirements, and CI coverage status.
- `quantum-bench bundle` for creating reproducible result bundles with normalized JSON/CSV outputs, flattened records, Markdown reports, optional plots, environment metadata, and bundle READMEs.
- Public `results_to_records(...)` and `results_to_dataframe(...)` helpers for notebook and pandas workflows.
- `COMPATIBILITY.md` documenting supported Python versions, optional SDK extras, local runtime requirements, CI coverage, and the free/local simulator scope.
- Tutorial notebooks for a Cirq quickstart, local simulator comparison, and Hamiltonian simulation case study.
- A Cirq smoke reference result bundle under `examples/reference_results/` for the two-minute first-run workflow.
- GitHub Pages workflow and portfolio-style documentation landing page for the project website.
- `RESULTS.md` with curated benchmark tables, reproduction commands, and generated plot assets for the website.
- Live README badges for CI, Pages, PyPI, supported Python versions, license, and local simulator backends.

### Changed

- `quantum-bench recommend` now explains installed backend recommendations and reports unavailable execution backends with install/runtime caveats.
- README and usage documentation now emphasize the free, local, credential-free default execution path.
- Reference result artifacts are grouped under `examples/reference_results/` and copied into the generated Pages site.
- The source distribution now includes compatibility docs, tutorial notebooks, and reference result artifacts.
- Notebook and plot examples consistently use ordered ket notation for displayed computational-basis states.

## [0.1.7] - 2026-04-29

### Added

- QAOA MaxCut benchmark for single-layer line and ring graph optimization workloads.
- Packaged comparison presets for runtime, noise, algorithmic, and SDK smoke studies.
- `quantum-bench preset` commands for listing, exporting, and running packaged presets.
- `quantum-bench report` for Markdown reports from saved JSON, result bundles, or CSV exports.
- Experiment manifest `outputs.report` support for Markdown report generation.
- Qiskit Aer depolarizing-noise injection for noisy benchmark wrappers.

### Changed

- Backend discovery and result metadata now report Qiskit Aer depolarizing noise support.
- The standard suite now includes a small QAOA MaxCut optimization workload.
- The `all` extra now targets the practical Python-only comparison stack; `full` includes heavyweight and external-runtime-backed SDK extras.
- Optional backend tests are marked by Python SDK, heavyweight SDK, and external runtime requirements.

## [0.1.6] - 2026-04-29

### Added

- `quantum-bench doctor` for local integration diagnostics and install hints.
- CLI validation for positive `--shots` and `--repeats`, probability-bounded success thresholds, and noise levels.
- Backend runtime metadata in result rows, including transpilation/runtime caveats, external-process usage, local-only status, noise support, and backend package versions.
- Best-effort deterministic simulator seeding for backends that expose seed controls.
- Packaging regression coverage for required source-distribution documentation.
- Python 3.11 and 3.12 CI coverage.
- Backend-selection guidance, result-interpretation notes, and a reproducibility checklist in the documentation.

### Changed

- CI now runs the main test/build job across the supported Python version matrix.

## [0.1.5] - 2026-04-29

### Added

- `THEORY.md` with conceptual background for qubits, circuits, shots, distributions, metrics, noise models, benchmark families, and backend comparability.
- Tables of contents for long-form and reference Markdown documentation.
- Public benchmark factory helpers for CLI-style benchmark configuration.

### Changed

- Experiment manifest execution now builds benchmarks through shared core factory helpers instead of importing CLI internals.
- The `all` optional dependency extra now includes `qbraid`.
- Optional-backend CI coverage now includes CUDA-Q and pyQuil smoke jobs, with CUDA-Q marked experimental.

### Fixed

- `run_benchmark` now rejects invalid `shots` values before dispatching to backend adapters.

## [0.1.4] - 2026-04-29

### Added

- `quantum-bench diff` for comparing saved JSON or CSV result files with metric thresholds.
- Public result-diff helpers for loading saved outputs, comparing metric deltas, and formatting diff tables.

### Fixed

- pyQuil QVM discovery now requires local `qvm` and `quilc` executables in addition to the Python package.

## [0.1.3] - 2026-04-24

### Added

- Distribution, heatmap, noise-quality, and suite runtime plot outputs.
- Plot gallery and circuit diagram export examples.
- Bra-ket notation for computational basis states in plots.
- Backend legend for suite runtime plots.
- GHZ plot-gallery noise sweep now spans 0% to 5%.
- Bernstein-Vazirani benchmark with configurable hidden bitstring.
- Deutsch-Jozsa benchmark with constant and linear balanced oracle modes.
- Quantum-volume-style random layered benchmark.
- CLI and suite coverage for the new benchmark families.
- `quantum-bench list` and `quantum-bench info` discovery commands.
- Suite dry-run/listing support with JSON suite manifest export.
- Standardized result metadata fields for benchmark family, case labels, depth, seed, oracle type, and noise level.
- Optional Qiskit Aer, CUDA-Q, pyQuil QVM, and QuTiP local execution adapters.
- Optional qBraid and Q# integration discovery extras.
- Experiment manifest runner with JSON/YAML loading, output export, and bundled research-style manifests.
- Runtime repeat statistics and environment capture in result metadata.
- Result schema and benchmark methodology documentation.
- Research helper examples for capability matrices, manifest generation, repeated-runtime analysis, schema inspection, noise manifests, and Markdown reports.
- `examples/README.md` with a recommended research example workflow and expected artifacts.
- `quantum-bench validate` for installed-backend correctness and regression checks.
- `quantum-bench recommend` for backend selection by use case.
- Problem statement, limitations, and citation metadata.
- Example scripts for oracle benchmarks, quantum-volume-style execution, and suite artifact export.
- Tests for new benchmark builders, CLI execution, and Cirq Bernstein-Vazirani correctness.

### Changed

- CSV exports now include case labels and benchmark families.
- Plot labels now use standardized result case labels.
- Backend CLI choices are now driven by the backend registry.
- CLI result tables and CSV exports include repeat-aware runtime fields.

### Fixed

- Benchmark validation errors now report clearer expected lengths and invalid parameter constraints.

## [0.1.2] - 2026-04-24

### Added

- CI workflow for formatting, linting, tests, build, and distribution checks.
- Optional backend extras for Cirq, PennyLane, Braket, pytket, plotting, and all integrations.
- `--summary` result ranking output for CLI benchmark result commands.
- `--save-csv` export support for benchmark results.
- `quantum-bench suite` command with `smoke`, `standard`, and `scaling` presets.
- Public exports for suite and summary helpers.
- Additional tests for backend bitstring consistency, Grover success metrics, QFT structure, noise metadata, suites, CSV export, summary output, and result ranking.

### Changed

- Split backend SDKs and plotting dependencies into optional extras.
- Removed tracked local Codex metadata from the repository.

### Fixed

- Missing backend and plotting dependencies now report the matching optional extra install command.

## [0.1.1] - 2026-04-23

### Added

- Native circuit drawing through Cirq, PennyLane, Amazon Braket, and pytket.
- `quantum-bench draw` CLI command for rendering benchmark circuits and optionally saving diagrams.
- `USAGE.md` with task-oriented CLI, Python API, result schema, and development workflow guidance.
- `MANIFEST.in`, `.gitignore`, and `.gitattributes` for cleaner source distributions and repository hygiene.

### Changed

- Updated README badges, installation guidance, release build instructions, and circuit drawing examples.
- Configured writable local runtime cache directories for matplotlib and Numba in Codespaces-style environments.
- Updated PennyLane execution to use `qml.set_shots(...)`.

### Fixed

- Replaced deprecated or removed pytket `Circuit.optypes()` usage with command-based gate histogram analysis.
- Avoided Braket `LocalSimulator` Numba cache failures in restricted local environments.
- Removed generated artifacts, egg-info metadata, and Python bytecode caches from git tracking.

## [0.1.0] - 2026-04-23

Initial public release of `quantum-backend-bench`.

### Added

- Backend-agnostic benchmarking package structure with a shared `BenchmarkSpec` abstraction and a unified `run_benchmark(...)` API.
- Local execution backends for Cirq, PennyLane, and Amazon Braket `LocalSimulator`, with no cloud credentials required.
- `pytket`-based structural analysis for circuit depth, gate counts, and two-qubit gate metrics.
- Built-in benchmark builders for GHZ, QFT, random circuits, Grover search, Hamiltonian simulation, and noise sensitivity sweeps.
- Standardized metric calculation for runtime, measurement distributions, success probability, and total variation distance.
- `quantum-bench` CLI with `run`, `compare`, and `noise-sweep` commands.
- JSON export helpers, matplotlib plotting utilities, and example scripts for backend comparison and noise benchmarking.
- Automated tests covering benchmark builders, backend interfaces, metric helpers, and CLI execution.
- GitHub Codespaces development container configuration for Python 3.11+.
- PyPI publish workflow triggered from version tags.
