# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

No changes yet.

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
