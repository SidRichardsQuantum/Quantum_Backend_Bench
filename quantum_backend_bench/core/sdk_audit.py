"""Audit helpers for local SDK parity, semantics, noise, compilation, and translation."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantum_backend_bench.backends import BACKEND_REGISTRY
from quantum_backend_bench.benchmarks import noise_sensitivity
from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)
from quantum_backend_bench.core.circuit_translate import (
    FREE_LOCAL_TRANSLATION_SDKS,
    TRANSLATION_OUTPUT_FORMATS,
    emit_circuit_source,
    import_circuit_source,
    verify_translation,
)
from quantum_backend_bench.core.discovery import backend_capabilities, result_case_label
from quantum_backend_bench.core.exact import exact_probabilities
from quantum_backend_bench.core.factory import build_benchmark_from_config
from quantum_backend_bench.core.metrics import total_variation_distance
from quantum_backend_bench.core.observable_translate import (
    HAMILTONIAN_OUTPUT_FORMATS,
    canonical_hamiltonian,
    emit_hamiltonian_source,
    import_hamiltonian_source,
    translation_capability_rows,
    verify_hamiltonian_translation,
)
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.workflow_translate import (
    WORKFLOW_OUTPUT_FORMATS,
    canonical_workflow,
    emit_workflow_source,
    import_workflow_source,
    verify_workflow_translation,
)

FREE_LOCAL_EXECUTION_BACKENDS = (
    "cirq",
    "pennylane",
    "braket_local",
    "qiskit_aer",
    "qutip",
)

NOISE_MODELS = (
    "depolarizing",
    "bit_flip",
    "phase_flip",
    "amplitude_damping",
    "readout_error",
)

_NOISE_SUPPORT: dict[str, dict[str, str]] = {
    "cirq": {
        "depolarizing": "implemented",
        "bit_flip": "implemented",
        "phase_flip": "implemented",
        "amplitude_damping": "implemented",
        "readout_error": "implemented",
    },
    "pennylane": {
        "depolarizing": "implemented",
        "bit_flip": "implemented",
        "phase_flip": "implemented",
        "amplitude_damping": "implemented",
        "readout_error": "implemented",
    },
    "qiskit_aer": {
        "depolarizing": "implemented",
        "bit_flip": "implemented",
        "phase_flip": "implemented",
        "amplitude_damping": "implemented",
        "readout_error": "implemented",
    },
    "braket_local": {model: "not injected" for model in NOISE_MODELS},
    "qutip": {model: "not injected" for model in NOISE_MODELS},
    "cudaq": {model: "not injected" for model in NOISE_MODELS},
    "pyquil_qvm": {model: "not injected" for model in NOISE_MODELS},
}


@dataclass(frozen=True, slots=True)
class AuditCase:
    """A compact benchmark case used by SDK audits."""

    name: str
    config: dict[str, object] | None = None
    benchmark: BenchmarkSpec | None = None

    def build(self) -> BenchmarkSpec:
        if self.benchmark is not None:
            return self.benchmark
        if self.config is None:
            raise ValueError(f"Audit case {self.name} has no benchmark source.")
        return build_benchmark_from_config(self.config)


def _gate_coverage_case() -> BenchmarkSpec:
    circuit = InternalCircuit(
        3,
        (
            CircuitOperation("H", (0,)),
            CircuitOperation("RX", (0,), {"theta": 0.25}),
            CircuitOperation("RY", (1,), {"theta": 0.5}),
            CircuitOperation("RZ", (2,), {"theta": 0.75}),
            CircuitOperation("CZ", (0, 1)),
            CircuitOperation("SWAP", (1, 2)),
            CircuitOperation("CPHASE", (0, 2), {"theta": 0.125}),
        ),
        (0, 1, 2),
    )
    return BenchmarkSpec(
        name="sdk_gate_coverage",
        n_qubits=3,
        parameters={"case": "rotations_cz_swap_cphase"},
        circuit_data=circuit,
        metadata={"family": "sdk_audit"},
    )


DEFAULT_AUDIT_CASES = (
    AuditCase("ghz", {"benchmark": "ghz", "n_qubits": 3}),
    AuditCase("qft", {"benchmark": "qft", "n_qubits": 3}),
    AuditCase(
        "bernstein-vazirani",
        {"benchmark": "bernstein-vazirani", "n_qubits": 3, "secret_string": "10"},
    ),
    AuditCase("gate-coverage", benchmark=_gate_coverage_case()),
)

DEFAULT_HAMILTONIAN_SOURCE = json.dumps(
    {
        "n_qubits": 3,
        "terms": [
            {"coefficient": 0.5, "paulis": {"0": "Z"}},
            {"coefficient": -1.25, "paulis": {"1": "X", "2": "Z"}},
            {"coefficient": 0.75, "paulis": {"0": "Y", "2": "Y"}},
        ],
    },
    indent=2,
    sort_keys=True,
)

DEFAULT_WORKFLOW_SOURCE = json.dumps(
    {
        "name": "audit_parameterized_workflow",
        "n_qubits": 2,
        "parameters": ["theta"],
        "parameter_bindings": {"theta": 1.5707963267948966},
        "operations": [
            {"gate": "H", "targets": [0]},
            {"gate": "RX", "targets": [1], "parameter": "theta"},
            {"gate": "CNOT", "controls": [0], "targets": [1]},
        ],
        "measurements": [
            {"type": "counts", "targets": [0, 1]},
            {"type": "probabilities", "targets": [0, 1]},
            {
                "type": "expectation",
                "observable": {
                    "n_qubits": 2,
                    "terms": [{"coefficient": 1.0, "paulis": {"0": "Z", "1": "Z"}}],
                },
            },
        ],
        "shots": 512,
        "seed": 1234,
    },
    indent=2,
    sort_keys=True,
)


def sdk_parity_scorecard() -> list[dict[str, Any]]:
    """Return feature scorecard rows for free local SDK integrations."""

    capabilities = {item.name: item for item in backend_capabilities()}
    translation_rows = {str(row["sdk"]): row for row in translation_capability_rows()}
    rows: list[dict[str, Any]] = []
    for backend in sorted(FREE_LOCAL_EXECUTION_BACKENDS):
        capability = capabilities.get(backend)
        translation = translation_rows.get(backend, {})
        noise = _NOISE_SUPPORT.get(backend, {})
        rows.append(
            {
                "sdk": backend,
                "installed": bool(capability and capability.installed),
                "execution_backend": backend in BACKEND_REGISTRY,
                "local_only": bool(capability and capability.local_only),
                "python_package_only": bool(capability and not capability.external_process),
                "shot_sampling": bool(capability and capability.shot_sampling),
                "exact_statevector": bool(capability and capability.exact_statevector),
                "runtime_includes_transpilation": bool(
                    capability and capability.includes_transpilation_time
                ),
                "circuit_translation": bool(translation.get("circuits")),
                "workflow_translation": bool(translation.get("execution_wrappers")),
                "pauli_hamiltonians": bool(translation.get("pauli_hamiltonians")),
                "result_normalization": bool(translation.get("result_objects")),
                "measurement_grouping": bool(translation.get("measurement_grouping")),
                "noise_models": {
                    model: status for model, status in noise.items() if status == "implemented"
                },
                "unsupported_noise_models": {
                    model: status for model, status in noise.items() if status != "implemented"
                },
                "notes": capability.notes if capability else "No capability metadata found.",
            }
        )
    return rows


def noise_model_matrix() -> list[dict[str, Any]]:
    """Return local noise model support rows."""

    capabilities = {item.name: item for item in backend_capabilities()}
    rows = []
    for backend in sorted(_NOISE_SUPPORT):
        capability = capabilities.get(backend)
        rows.append(
            {
                "backend": backend,
                "installed": bool(capability and capability.installed),
                "models": dict(_NOISE_SUPPORT[backend]),
                "comparison_scope": (
                    "project-injected local model"
                    if any(status == "implemented" for status in _NOISE_SUPPORT[backend].values())
                    else "reported only; noise is not injected by this project"
                ),
            }
        )
    return rows


def semantic_audit(
    *,
    backends: list[str] | None = None,
    shots: int = 512,
    tolerance: float = 0.15,
    include_missing: bool = True,
) -> list[dict[str, Any]]:
    """Run compact semantic checks against ideal neutral probabilities."""

    selected = backends or list(FREE_LOCAL_EXECUTION_BACKENDS)
    installed = _installed_execution_backends()
    rows: list[dict[str, Any]] = []
    for backend in selected:
        if backend not in installed:
            if include_missing:
                rows.append(_missing_backend_row("semantic", backend))
            continue
        for case in DEFAULT_AUDIT_CASES:
            benchmark = case.build()
            try:
                result = run_benchmark(
                    benchmark,
                    [backend],
                    shots=shots,
                    repeats=1,
                    include_environment=False,
                )[0]
                ideal = exact_probabilities(benchmark)
                tvd = total_variation_distance(result["counts"], ideal, shots=result["total_shots"])
                rows.append(
                    {
                        "audit": "semantic",
                        "backend": backend,
                        "case": result_case_label(result),
                        "status": "passed" if tvd is not None and tvd <= tolerance else "failed",
                        "total_variation_distance": tvd,
                        "tolerance": tolerance,
                        "shots": shots,
                    }
                )
            except Exception as exc:  # pragma: no cover - exercised by optional SDK environments
                rows.append(_error_row("semantic", backend, case.name, exc))
    return rows


def compile_audit(
    *,
    backends: list[str] | None = None,
    shots: int = 128,
    include_missing: bool = True,
) -> list[dict[str, Any]]:
    """Run compact structure/compilation checks and report compiled deltas."""

    selected = backends or list(FREE_LOCAL_EXECUTION_BACKENDS)
    installed = _installed_execution_backends()
    rows: list[dict[str, Any]] = []
    for backend in selected:
        if backend not in installed:
            if include_missing:
                rows.append(_missing_backend_row("compile", backend))
            continue
        for case in DEFAULT_AUDIT_CASES:
            benchmark = case.build()
            try:
                result = run_benchmark(
                    benchmark,
                    [backend],
                    shots=shots,
                    repeats=1,
                    include_environment=False,
                )[0]
                metrics = result["metrics"]
                rows.append(
                    {
                        "audit": "compile",
                        "backend": backend,
                        "case": result_case_label(result),
                        "status": "reported",
                        "depth": metrics.get("depth"),
                        "compiled_depth": metrics.get("compiled_depth"),
                        "depth_delta": _delta(metrics.get("compiled_depth"), metrics.get("depth")),
                        "gate_count": metrics.get("gate_count"),
                        "compiled_gate_count": metrics.get("compiled_gate_count"),
                        "gate_count_delta": _delta(
                            metrics.get("compiled_gate_count"), metrics.get("gate_count")
                        ),
                        "compile_seconds": metrics.get("compile_seconds"),
                        "compile_toolchain": result["metadata"].get("compile_toolchain"),
                        "runtime_includes_transpilation": result["metadata"].get(
                            "runtime_includes_transpilation"
                        ),
                    }
                )
            except Exception as exc:  # pragma: no cover - exercised by optional SDK environments
                rows.append(_error_row("compile", backend, case.name, exc))
    return rows


def roundtrip_audit(
    *,
    targets: list[str] | None = None,
    tolerance: float = 1e-9,
    include_hamiltonian: bool = False,
    include_workflow: bool = False,
) -> list[dict[str, Any]]:
    """Translate neutral objects to SDK snippets and back, then verify semantics."""

    selected = targets or list(FREE_LOCAL_TRANSLATION_SDKS)
    rows: list[dict[str, Any]] = []
    rows.extend(_circuit_roundtrip_rows(selected, tolerance=tolerance))
    if include_hamiltonian:
        rows.extend(_hamiltonian_roundtrip_rows(selected))
    if include_workflow:
        rows.extend(_workflow_roundtrip_rows(selected))
    return rows


def runnable_noise_audit(
    *,
    backends: list[str] | None = None,
    noise_models: list[str] | None = None,
    noise_level: float = 0.01,
    shots: int = 256,
    include_missing: bool = True,
) -> list[dict[str, Any]]:
    """Run tiny noisy workloads where the project claims local injection support."""

    selected_backends = backends or list(FREE_LOCAL_EXECUTION_BACKENDS)
    selected_models = noise_models or list(NOISE_MODELS)
    installed = _installed_execution_backends()
    rows: list[dict[str, Any]] = []
    base = build_benchmark_from_config({"benchmark": "ghz", "n_qubits": 3})
    for backend in selected_backends:
        if backend not in installed:
            if include_missing:
                rows.append(_missing_backend_row("noise", backend))
            continue
        for model in selected_models:
            support = _NOISE_SUPPORT.get(backend, {}).get(model, "unknown")
            if support != "implemented":
                rows.append(
                    {
                        "audit": "noise",
                        "backend": backend,
                        "noise_type": model,
                        "status": "not_supported",
                        "support": support,
                    }
                )
                continue
            benchmark = noise_sensitivity.build_benchmark(
                base, noise_type=model, noise_levels=[noise_level]
            )[0]
            try:
                result = run_benchmark(
                    benchmark,
                    [backend],
                    shots=shots,
                    repeats=1,
                    include_environment=False,
                )[0]
                rows.append(
                    {
                        "audit": "noise",
                        "backend": backend,
                        "noise_type": model,
                        "status": (
                            "applied" if result["metadata"].get("noise_applied") else "not_applied"
                        ),
                        "noise_level": noise_level,
                        "success_probability": result["metrics"].get("success_probability"),
                        "total_variation_distance": result["metrics"].get(
                            "total_variation_distance"
                        ),
                    }
                )
            except Exception as exc:  # pragma: no cover - exercised by optional SDK environments
                rows.append(_error_row("noise", backend, model, exc))
    return rows


def save_audit_json(rows: list[dict[str, Any]], path: str | Path) -> Path:
    """Save audit rows as indented JSON."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def save_audit_csv(rows: list[dict[str, Any]], path: str | Path) -> Path:
    """Save audit rows as a flattened CSV table."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    keys = _display_keys(rows)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in keys})
    return destination


def save_audit_report(rows: list[dict[str, Any]], path: str | Path, *, title: str) -> Path:
    """Save audit rows as a Markdown report."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(format_audit_markdown(title, rows), encoding="utf-8")
    return destination


def format_audit_markdown(title: str, rows: list[dict[str, Any]]) -> str:
    """Format audit rows as a Markdown report."""

    keys = _display_keys(rows)
    lines = [f"# {title}", "", f"- rows: `{len(rows)}`", f"- passed: `{audit_passed(rows)}`", ""]
    if not rows:
        lines.append("No audit rows.")
        return "\n".join(lines).rstrip() + "\n"
    lines.append("| " + " | ".join(keys) + " |")
    lines.append("| " + " | ".join("---" for _ in keys) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_markdown_value(row.get(key)) for key in keys) + " |")
    return "\n".join(lines).rstrip() + "\n"


def audit_passed(rows: list[dict[str, Any]]) -> bool:
    """Return True when no audit row failed with an error or threshold miss."""

    return all(row.get("status") not in {"failed", "error"} for row in rows)


def format_scorecard(rows: list[dict[str, Any]]) -> str:
    """Format SDK parity scorecard rows."""

    lines = [
        "SDK Parity Scorecard",
        "sdk           installed  circuits  workflows  pauli  results  grouping  noise models",
    ]
    for row in rows:
        noise = ", ".join(sorted(row["noise_models"])) or "none"
        lines.append(
            f"{row['sdk']:<13} {_yes_no(row['installed']):<10} "
            f"{_yes_no(row['circuit_translation']):<8} "
            f"{_yes_no(row['workflow_translation']):<10} "
            f"{_yes_no(row['pauli_hamiltonians']):<6} "
            f"{_yes_no(row['result_normalization']):<8} "
            f"{_yes_no(row['measurement_grouping']):<9} {noise}"
        )
    return "\n".join(lines)


def format_audit_rows(title: str, rows: list[dict[str, Any]]) -> str:
    """Format generic audit rows for CLI output."""

    if not rows:
        return f"{title}\nNo rows."
    keys = _display_keys(rows)
    lines = [title, "  ".join(key for key in keys)]
    for row in rows:
        lines.append("  ".join(_format_value(row.get(key)) for key in keys))
    return "\n".join(lines)


def _circuit_roundtrip_rows(targets: list[str], *, tolerance: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        if target not in TRANSLATION_OUTPUT_FORMATS:
            rows.append(_unsupported_target_row("circuit_roundtrip", target))
            continue
        for case in DEFAULT_AUDIT_CASES:
            benchmark = case.build()
            try:
                source = emit_circuit_source(benchmark, target)
                imported, detected = import_circuit_source(
                    source, from_format=_target_import_format(target), name=f"{case.name}_roundtrip"
                )
                verification = verify_translation(
                    benchmark,
                    source,
                    to_format=target,
                    mode="exact",
                    tolerance=tolerance,
                )
                rows.append(
                    {
                        "audit": "circuit_roundtrip",
                        "target": target,
                        "case": case.name,
                        "status": "passed" if verification.passed else "failed",
                        "detected_format": detected,
                        "operations": (
                            len(imported.circuit_data.operations) if imported.circuit_data else None
                        ),
                        "total_variation_distance": verification.total_variation_distance,
                        "tolerance": tolerance,
                    }
                )
            except Exception as exc:
                rows.append(_error_row("circuit_roundtrip", target, case.name, exc, key="target"))
    return rows


def _hamiltonian_roundtrip_rows(targets: list[str]) -> list[dict[str, Any]]:
    expected, _ = import_hamiltonian_source(DEFAULT_HAMILTONIAN_SOURCE, from_format="pauli-json")
    rows: list[dict[str, Any]] = []
    for target in targets:
        if target not in HAMILTONIAN_OUTPUT_FORMATS:
            rows.append(_unsupported_target_row("hamiltonian_roundtrip", target))
            continue
        try:
            source = emit_hamiltonian_source(expected, target)
            imported, detected = import_hamiltonian_source(
                source, from_format=_hamiltonian_import_format(target)
            )
            verification = verify_hamiltonian_translation(
                expected, source, to_format=target, mode="canonical"
            )
            rows.append(
                {
                    "audit": "hamiltonian_roundtrip",
                    "target": target,
                    "case": "pauli_hamiltonian",
                    "status": "passed" if verification.passed else "failed",
                    "detected_format": detected,
                    "terms": len(canonical_hamiltonian(imported)[1]),
                    "details": verification.details,
                }
            )
        except Exception as exc:
            rows.append(
                _error_row("hamiltonian_roundtrip", target, "pauli_hamiltonian", exc, key="target")
            )
    return rows


def _workflow_roundtrip_rows(targets: list[str]) -> list[dict[str, Any]]:
    expected, _ = import_workflow_source(DEFAULT_WORKFLOW_SOURCE, from_format="workflow-json")
    rows: list[dict[str, Any]] = []
    for target in targets:
        if target not in WORKFLOW_OUTPUT_FORMATS:
            rows.append(_unsupported_target_row("workflow_roundtrip", target))
            continue
        try:
            source = emit_workflow_source(expected, target)
            imported, detected = import_workflow_source(
                source, from_format=_workflow_import_format(target)
            )
            verification = verify_workflow_translation(expected, source, to_format=target)
            rows.append(
                {
                    "audit": "workflow_roundtrip",
                    "target": target,
                    "case": "parameterized_expectation_workflow",
                    "status": "passed" if verification.passed else "failed",
                    "detected_format": detected,
                    "operations": len(canonical_workflow(imported)["operations"]),
                    "measurements": len(canonical_workflow(imported)["measurements"]),
                    "details": verification.details,
                }
            )
        except Exception as exc:
            rows.append(
                _error_row(
                    "workflow_roundtrip",
                    target,
                    "parameterized_expectation_workflow",
                    exc,
                    key="target",
                )
            )
    return rows


def _installed_execution_backends() -> set[str]:
    return {
        capability.name
        for capability in backend_capabilities()
        if capability.role == "execution" and capability.installed
    }


def _target_import_format(target: str) -> str:
    return {
        "braket_local": "braket",
        "cirq": "cirq",
        "pennylane": "pennylane",
        "qiskit_aer": "qiskit",
        "internal-json": "internal-json",
        "openqasm": "openqasm",
    }[target]


def _hamiltonian_import_format(target: str) -> str:
    return {
        "braket_local": "braket",
        "cirq": "cirq",
        "pennylane": "pennylane",
        "qiskit_aer": "qiskit",
        "pauli-json": "pauli-json",
    }[target]


def _workflow_import_format(target: str) -> str:
    return {
        "braket_local": "braket",
        "cirq": "cirq",
        "pennylane": "pennylane",
        "qiskit_aer": "qiskit",
        "workflow-json": "workflow-json",
    }[target]


def _unsupported_target_row(audit: str, target: str) -> dict[str, Any]:
    return {
        "audit": audit,
        "target": target,
        "case": None,
        "status": "failed",
        "message": f"Unsupported translation target '{target}' for {audit}.",
    }


def _missing_backend_row(audit: str, backend: str) -> dict[str, Any]:
    return {
        "audit": audit,
        "backend": backend,
        "case": None,
        "status": "missing",
        "message": "Backend is not installed or not locally runnable.",
    }


def _error_row(
    audit: str, backend: str, case: str, exc: Exception, *, key: str = "backend"
) -> dict[str, Any]:
    return {
        "audit": audit,
        key: backend,
        "case": case,
        "status": "error",
        "message": str(exc),
    }


def _delta(candidate: Any, baseline: Any) -> Any:
    if candidate is None or baseline is None:
        return None
    return candidate - baseline


def _display_keys(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "audit",
        "backend",
        "target",
        "case",
        "noise_type",
        "status",
        "support",
        "total_variation_distance",
        "success_probability",
        "depth",
        "compiled_depth",
        "depth_delta",
        "compile_seconds",
        "message",
        "details",
    ]
    keys = [key for key in preferred if any(key in row for row in rows)]
    extras = sorted({key for row in rows for key in row} - set(keys))
    return keys + extras


def _format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, dict):
        return ",".join(f"{key}={item}" for key, item in sorted(value.items()))
    return str(value)


def _csv_value(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _markdown_value(value: Any) -> str:
    text = _format_value(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _yes_no(value: object) -> str:
    return "yes" if value else "no"
