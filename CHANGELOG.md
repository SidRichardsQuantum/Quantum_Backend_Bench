# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.2.13] - 2026-07-21

### Added

- Added `translate-workflow --verify semantic` with exact neutral measurement-distribution TVD, Pauli expectation-value maximum absolute error, configurable distribution/expectation tolerances, result-schema validity, and report fields.
- Added `roundtrip-audit --workflow-verify` plus optional-SDK execution fixtures that run generated Qiskit Aer, Cirq, PennyLane, and Braket LocalSimulator workflows and inspect their neutral results.
- Added public neutral workflow evaluation and result-contract validation helpers.
- Added CI validation for every committed neutral JSON Schema and matching example, including local cross-schema `$ref` resolution.

### Changed

- Generated Qiskit Aer, Cirq, PennyLane, and Braket LocalSimulator workflow scripts now emit schema-versioned runtime counts, normalized probabilities, and populated Pauli expectations instead of placeholder result fields.
- Updated workflow golden outputs, round-trip audit artifacts, semantic contracts, roadmap guidance, and translation/schema documentation for executable result fidelity.
- Repaired all neutral JSON Schemas with Draft 2020-12 `$schema` and stable `$id` declarations; `workflow-json` now references the shared `pauli-json` schema.

### Fixed

- Pinned the CI notebook PNG render stack and removed version-dependent Matplotlib metadata so committed documentation plots regenerate byte-for-byte.
- Golden translation generation now applies the repository's Black configuration so regeneration and `black .` produce identical Python fixtures.
- Result normalization now rejects invalid field types, count/shot mismatches, non-normalized probabilities, count/probability inconsistencies, non-finite expectations, and unsupported schema versions with structured diagnostics.
- Workflow emission now rejects multiple distinct distribution target sets, missing result requests, and explicit measurements without a portable distribution result request.

## [0.2.12]

### Added

- Added neutral `RESET`, `BARRIER`, and `DELAY` circuit annotations across internal JSON, OpenQASM import/export, static SDK importers, and target-aware SDK emitters where local syntax can preserve them.
- Added `canonical` and `statevector` circuit verification modes for neutral structure checks and small noiseless statevector comparison up to global phase.
- Added accepted and rejected translation fixtures for annotation preservation, OpenQASM annotation import/export, nonliteral delay diagnostics, and nonliteral reset-target diagnostics.

### Changed

- Updated the internal-circuit JSON Schema, schema example, translation semantic contract, migration-audit guidance, and circuit translation docs for reset/barrier/delay annotations.
- Tightened annotation diagnostics so SDK outputs warn when reset, barrier, or delay annotations are represented only as neutral comments.
- Extended `roundtrip-audit` with `--verify` for circuit round trips and reports canonical/statevector verification fields when selected.
- Clarified the optional-SDK compatibility review cadence around the checked-in CI constraint bands.

## [0.2.11] - 2026-07-14

### Added

- Promoted the Braket `circuit.expectation(...)` Pauli result-type fixture into the accepted workflow translation corpus with canonical reimport verification.
- Extended the neutral `internal-circuit` model with named quantum/classical register metadata, measurement keys, bit-order labels, global phase metadata, and optional neutral local noise-channel annotations.
- Added richer neutral circuit gate coverage for `SX`, phase/`P`, `U`, `CCX`, and controlled rotations (`CRX`, `CRY`, `CRZ`) across supported static import, emit, and exact-verification paths.
- Added neutral local noise-channel emission for SDK targets where local channel syntax is available, while keeping provider-calibrated noise semantics outside the model.

### Changed

- Updated translation semantic contracts, `translation-audit` capability rows, JSON schemas, schema examples, and migration/round-trip expected artifacts to describe the expanded neutral circuit contract.
- Updated circuit translation and roadmap documentation to distinguish implemented neutral local noise annotations from provider-specific calibrated noise behavior.
- Clarified project scope across README, usage, compatibility, limitations, roadmap, and release policy docs, including core/peripheral workflows, discovery-only SDKs, hardware-preparation exports, benchmark expansion guardrails, and CLI command groups.

## [0.2.10] - 2026-07-10

### Added

- Added circuit translation SDK adapter modules for Qiskit Aer, Cirq, PennyLane, and Braket LocalSimulator with explicit import, emit, capability, and diagnostic hooks.
- Added `scripts/check_translation_artifacts.py` to regenerate migration-audit and roundtrip-audit expected artifacts in a temporary copy and fail when committed examples drift.
- CI now runs the translation audit artifact drift checker alongside the existing translation corpus and golden-output checks.
- Promoted the PennyLane QNode Pauli-expectation workflow fixture into the accepted executable translation corpus.
- Added workflow support for arithmetic parameter expressions over declared parameters, such as `theta / 2`.
- Added tested optional-SDK version-band metadata to the compatibility report.

### Changed

- Circuit translation import dispatch and SDK source emitters now route through the SDK adapter registry while preserving the existing neutral translation behavior.
- `translation-audit` capability rows now expose circuit adapter import, emit, and diagnostic hook metadata for each free local SDK target.

## [0.2.9] - 2026-07-10

### Added

- Translation reports now include an explicit semantic contract that states the lossless neutral-subset guarantee, preserved semantics, rewrites, rejected constructs, unmodeled behavior, verification modes, and free local SDK target scope.
- `quantum-bench translate-check` now supports `--to-format`, `--explain`, and `--save-markdown` for target-aware migration-audit guidance covering preserved semantics, syntax rewrites, rejection categories, unmodeled behavior, and recommended verification.
- `quantum-bench translate-all` now emits selected SDK target source files, neutral `internal-json`, per-target JSON reports, a combined JSON report, and a compact Markdown summary in one artifact directory.
- Translation examples now include migration-audit reports, realistic accepted SDK snippets, purpose-level workflow JSON, round-trip audit artifacts, portable rewrites for rejected patterns, roadmap-only intent examples, and result-normalization edge cases.
- Added a translation migration-audit notebook and refreshed the circuit/workflow translation notebooks to show semantic contracts, target-aware audit guidance, and purpose-level workflow examples.

### Changed

- Translation documentation and SDK workflow guidance now describe the semantic-contract and migration-audit report fields so SDK portability checks are easier to use in CI and migration reviews.

## [0.2.8] - 2026-07-09

### Added

- Versioned neutral translation schemas for `internal-circuit`, `pauli-json`, `workflow-json`, and `result-json`, with JSON Schema files and example payloads.
- Translation reports now include neutral schema metadata for supported input and output formats.
- `translation-audit` now reports a fuller SDK translation coverage matrix with supported gates, parameter forms, measurement/result shapes, diagnostics, caveats, and verification modes.

### Changed

- Neutral JSON emitters now include `schema_version: "0.1"` while remaining tolerant of existing unversioned local examples.

## [0.2.7] - 2026-07-09

### Added

- Project roadmap documenting the next SDK interop and translation stabilization track, including neutral schema versioning, translation coverage matrices, a planned `translate-all` workflow, conservative diagnostics, SDK adapter refactoring, and optional SDK compatibility hardening.
- Generated documentation site entry and navigation link for the roadmap page.

### Changed

- README and usage documentation now link to the roadmap alongside release notes and translation docs.
- Source distributions now include `ROADMAP.md`.
- The `dev` extra now includes the clean-venv dependencies needed by the default test suite.
- Test coverage now avoids redundant generated-site builds and expensive SDK rendering in CLI dispatch tests while preserving draw and plot artifact coverage.
- Example scripts now use compact adaptive workloads and installed-backend selection for faster, more portable default runs.

## [0.2.6] - 2026-06-05

### Added

- Free local SDK audit commands for parity scorecards, semantic checks, broader noise model matrices and smoke execution, compilation/structure comparisons, and neutral-to-SDK-to-neutral round-trip translation verification, with JSON, CSV, and Markdown artifact outputs.
- Circuit audit coverage for rotation, CZ, SWAP, and controlled-phase gates, plus Hamiltonian and parameterized workflow round-trip audits.
- Public audit helpers for SDK parity, semantic audits, noise model audits, compilation audits, round-trip translation audits, and audit artifact writers.
- Generated SDK audit documentation page and committed reference audit artifacts.

### Changed

- Documentation now reflects the broader local noise model support across Cirq, PennyLane, and Qiskit Aer.

## [0.2.5] - 2026-06-05

### Added

- Weighted Pauli observable and Hamiltonian translation across Qiskit Aer, Cirq, PennyLane, Braket LocalSimulator, and neutral `pauli-json` formats.
- `quantum-bench translate-hamiltonian`, `quantum-bench translate-observable`, and `quantum-bench translation-audit` commands for SDK migration beyond circuit construction.
- Canonical Pauli-term and small dense-matrix verification, JSON reports, public Python API helpers, SDK-format Hamiltonian fixtures, golden outputs, rejected diagnostics, audit filters, and a tutorial notebook for observable/Hamiltonian translation workflows.
- Workflow-level translation for parameterized circuits, parameter bindings, measurement/expectation requests, local execution wrappers, neutral result-object normalization, and qubit-wise Pauli measurement grouping through `translate-workflow`, `translate-result`, and `group-pauli-terms`.
- Canonical workflow verification, golden expected outputs for parameterized workflow translations, first-pass static parameterized workflow importers for Qiskit/Cirq/PennyLane/Braket snippets, result-normalization fixtures, generated scripts that emit neutral result JSON, and a parameterized workflow translation notebook.
- Tutorial notebook polish for v0.2.5, including consistent Variables and Parameters blocks, clean standard Python 3 kernel metadata, a Hamiltonian coefficient plot with subscripted Pauli labels, result probability plots, and expanded translation fixture documentation.

## [0.2.4] - 2026-06-04

### Added

- `quantum-bench translate` for converting supported OpenQASM, internal JSON, and static SDK circuit snippets through the neutral circuit model into Cirq, Qiskit, PennyLane, Braket LocalSimulator, OpenQASM, or internal JSON outputs.
- `quantum-bench translate-check` for preflight inspection of translatable circuit sources, including `--json` stdout reports and `--save-report` artifacts for CI workflows.
- Exact and sample-based translation verification with total-variation-distance reporting, backend caveat diagnostics, runnable translated script output, and structured translation report helpers in the public Python API.
- Translation example corpus with expected outputs, rejected unsupported-construct fixtures, semantic verification, and golden-output maintenance scripts.
- Circuit translation documentation, generated-site page, and tutorial notebook covering supported SDK patterns, all-target local SDK translation, SDK-native visual circuit comparison, report artifacts, verification modes, caveats, and maintenance workflows.

### Changed

- CI now verifies translation examples and checks generated expected outputs for drift.
- Source distributions now include circuit translation docs and translation example fixtures, including OpenQASM examples.

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
- Fixed clean-checkout documentation builds by falling back to committed notebook result assets when ignored local notebook artifacts are absent.

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
