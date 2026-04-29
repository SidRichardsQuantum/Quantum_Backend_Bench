"""Environment diagnostics for local benchmark readiness."""

from __future__ import annotations

from typing import Any

from quantum_backend_bench.core.discovery import backend_capabilities


def doctor_checks() -> list[dict[str, Any]]:
    """Return install and capability checks for known integrations."""

    checks = []
    for capability in backend_capabilities():
        install_hint = f"quantum-backend-bench[{capability.install_extra}]"
        checks.append(
            {
                "name": capability.name,
                "role": capability.role,
                "status": "ok" if capability.installed else "missing",
                "install_hint": "" if capability.installed else install_hint,
                "local_only": capability.local_only,
                "external_process": capability.external_process,
                "noise_support": capability.noise_support,
                "notes": capability.notes,
            }
        )
    return checks


def doctor_passed(checks: list[dict[str, Any]]) -> bool:
    """Return whether the environment has at least one local execution backend."""

    return any(check["role"] == "execution" and check["status"] == "ok" for check in checks)


def format_doctor_table(checks: list[dict[str, Any]]) -> str:
    """Render diagnostics as a compact text table."""

    headers = ["name", "role", "status", "install", "notes"]
    rows = [
        [
            check["name"],
            check["role"],
            check["status"],
            check["install_hint"] or "-",
            check["notes"],
        ]
        for check in checks
    ]
    widths = [
        max(len(str(value)) for value in [header, *column])
        for header, column in zip(headers, zip(*rows, strict=False))
    ]
    lines = [
        " | ".join(header.ljust(width) for header, width in zip(headers, widths)),
        "-+-".join("-" * width for width in widths),
    ]
    for row in rows:
        lines.append(" | ".join(str(value).ljust(width) for value, width in zip(row, widths)))
    return "\n".join(lines)
