"""Backend validation checks for known-correct small benchmarks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from quantum_backend_bench.benchmarks.bernstein_vazirani import (
    build_benchmark as build_bernstein_vazirani,
)
from quantum_backend_bench.benchmarks.ghz import build_benchmark as build_ghz
from quantum_backend_bench.core.discovery import backend_capabilities
from quantum_backend_bench.core.runner import run_benchmark


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    """One backend validation check result."""

    backend: str
    benchmark: str
    status: str
    message: str
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""

        return asdict(self)


def validate_backends(
    backends: list[str] | None = None,
    shots: int = 64,
    success_threshold: float = 0.95,
) -> list[dict[str, Any]]:
    """Validate installed execution backends with small known-correct circuits."""

    selected = backends or [
        capability.name
        for capability in backend_capabilities()
        if capability.role == "execution" and capability.installed
    ]
    checks: list[ValidationCheck] = []
    for backend in selected:
        checks.extend(_validate_backend(backend, shots=shots, success_threshold=success_threshold))
    return [check.to_dict() for check in checks]


def validation_passed(checks: list[dict[str, Any]]) -> bool:
    """Return whether all validation checks passed."""

    return all(check["status"] == "pass" for check in checks)


def _validate_backend(
    backend: str,
    shots: int,
    success_threshold: float,
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    try:
        ghz_result = run_benchmark(
            build_ghz(n_qubits=3),
            [backend],
            shots=shots,
            include_environment=False,
        )[0]
        ghz_counts = ghz_result.get("counts", {})
        expected_states = {"000", "111"}
        unexpected_states = sorted(set(ghz_counts) - expected_states)
        status = "pass" if not unexpected_states and sum(ghz_counts.values()) == shots else "fail"
        message = (
            "GHZ counts are limited to expected states."
            if status == "pass"
            else f"Unexpected GHZ states: {unexpected_states}"
        )
        checks.append(
            ValidationCheck(
                backend=backend,
                benchmark="ghz",
                status=status,
                message=message,
                metrics=ghz_result.get("metrics", {}),
            )
        )
    except Exception as exc:  # noqa: BLE001 - validation should report backend errors.
        checks.append(
            ValidationCheck(
                backend=backend,
                benchmark="ghz",
                status="error",
                message=str(exc),
                metrics={},
            )
        )

    try:
        bv_result = run_benchmark(
            build_bernstein_vazirani(n_qubits=4, secret_string="101"),
            [backend],
            shots=shots,
            include_environment=False,
        )[0]
        success = bv_result.get("metrics", {}).get("success_probability")
        status = "pass" if success is not None and success >= success_threshold else "fail"
        message = (
            f"Bernstein-Vazirani success >= {success_threshold}."
            if status == "pass"
            else f"Bernstein-Vazirani success {success} below {success_threshold}."
        )
        checks.append(
            ValidationCheck(
                backend=backend,
                benchmark="bernstein_vazirani",
                status=status,
                message=message,
                metrics=bv_result.get("metrics", {}),
            )
        )
    except Exception as exc:  # noqa: BLE001 - validation should report backend errors.
        checks.append(
            ValidationCheck(
                backend=backend,
                benchmark="bernstein_vazirani",
                status="error",
                message=str(exc),
                metrics={},
            )
        )
    return checks
