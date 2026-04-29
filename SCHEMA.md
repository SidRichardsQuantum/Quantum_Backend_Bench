# Result Schema

`quantum-backend-bench` writes JSON result bundles and flat CSV tables for research workflows.

For definitions of shots, counts, measurement distributions, success probability, and total variation distance, see [THEORY.md](./THEORY.md).

## Table of Contents

- [Experiment Bundle](#experiment-bundle)
- [Result Row](#result-row)
- [Metrics](#metrics)
- [Metadata](#metadata)
- [Manifest](#manifest)
- [CSV](#csv)

## Experiment Bundle

`quantum-bench experiment run examples/manifests/runtime_scaling.json` returns and optionally writes a JSON object:

```json
{
  "schema_version": "0.1",
  "manifest_path": "examples/manifests/runtime_scaling.json",
  "manifest": {},
  "environment": {},
  "results": []
}
```

## Result Row

Each item in `results` has this structure:

- `benchmark`: stable benchmark result name, such as `ghz` or `quantum_volume`
- `backend`: execution backend name, such as `cirq`
- `n_qubits`: logical qubit count for the benchmark
- `shots`: shots per repeat
- `repeats`: number of repeated executions
- `total_shots`: `shots * repeats`
- `parameters`: benchmark parameters used to build the circuit
- `metrics`: structural, runtime, and quality metrics
- `counts`: aggregate measurement counts across repeats
- `metadata`: analysis, environment, case labels, backend notes, and run context

## Metrics

Common metric keys:

- `depth`: structural circuit depth from pytket or the fallback estimator
- `gate_count`: number of internal circuit operations
- `two_qubit_gate_count`: number of two-qubit internal operations
- `runtime_seconds`: mean runtime across repeats
- `runtime_seconds_mean`: same value as `runtime_seconds`
- `runtime_seconds_stddev`: sample standard deviation, or `0.0` for one repeat
- `runtime_seconds_min`: fastest repeat
- `runtime_seconds_max`: slowest repeat
- `measurement_distribution`: normalized aggregate distribution over `total_shots`
- `success_probability`: target-state probability when the benchmark defines a target
- `total_variation_distance`: distance from the benchmark ideal distribution when defined

## Metadata

Common metadata keys:

- `benchmark_family`: broad category such as `oracle`, `search`, or `synthetic`
- `case_label`: stable human-readable label used in tables and plots
- `noise_level`: noise level when applicable
- `noise_requested`: whether the benchmark requested a nonzero noise level
- `noise_supported`: whether the adapter reported support for the requested noise mode
- `noise_applied`: whether the adapter reported applying noise
- `oracle_type`: oracle mode when applicable
- `seed`: random seed when applicable
- `seed_supported`: whether the adapter exposes seed control for this execution path
- `seed_applied`: whether a requested seed was applied
- `depth`: benchmark depth parameter when applicable
- `runtime_includes_transpilation`: whether adapter runtime includes compilation/transpilation work
- `external_process`: whether the backend depends on an external local process
- `local_only`: whether the integration is local-only
- `shot_sampling`: whether the backend reports shot-sampling behavior
- `exact_statevector`: whether the backend is reported as exact-statevector oriented
- `backend_noise_support`: capability-level noise support label
- `backend_package_versions`: package versions for backend-specific distributions
- `repeats`: repeated execution count
- `shots_per_repeat`: shots per repeat
- `total_shots`: total aggregate shots
- `runtime_seconds_samples`: raw runtime samples
- `environment`: Python, platform, package, and git metadata captured at run time

## Manifest

Experiment manifests are JSON by default. YAML is supported when `PyYAML` is installed.

```json
{
  "name": "runtime-scaling-local-simulators",
  "backends": ["cirq"],
  "shots": 256,
  "repeats": 3,
  "benchmarks": [
    {"benchmark": "ghz", "n_qubits": 3},
    {"benchmark": "random-circuit", "n_qubits": 4, "depth": 8, "seed": 42}
  ],
  "outputs": {
    "json": "artifacts/research/runtime_scaling.json",
    "csv": "artifacts/research/runtime_scaling.csv",
    "suite_plot": "artifacts/research/runtime_scaling.png"
  }
}
```

Case-level `backends`, `shots`, and `repeats` override manifest-level values. A case may include `noise_levels` to expand one benchmark into a depolarizing noise sweep.

## CSV

CSV output flattens the main fields for spreadsheet workflows. Nested `parameters` and `counts` are JSON-encoded strings.
