# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

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
