"""Build docs/SDK_AUDITS.md from committed audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "examples" / "reference_results" / "sdk_audits_2026-06-05"
AUDITS_DOC = ROOT / "docs" / "SDK_AUDITS.md"

AUDIT_FILES = {
    "parity": "sdk_parity.json",
    "noise": "noise_matrix.json",
    "roundtrip": "roundtrip_audit.json",
}


def main() -> int:
    missing = [name for name in AUDIT_FILES.values() if not (REFERENCE_DIR / name).exists()]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing SDK audit reference artifacts under {REFERENCE_DIR}: {joined}")

    audits = {
        key: json.loads((REFERENCE_DIR / file_name).read_text(encoding="utf-8"))
        for key, file_name in AUDIT_FILES.items()
    }
    AUDITS_DOC.write_text(_render_doc(audits), encoding="utf-8")
    print(f"Wrote {AUDITS_DOC.relative_to(ROOT)}")
    return 0


def _render_doc(audits: dict[str, list[dict[str, Any]]]) -> str:
    return (
        "\n".join(
            [
                "# SDK Audits",
                "",
                "This page is generated from committed reference artifacts under `../examples/reference_results/sdk_audits_2026-06-05/`. The artifacts demonstrate the free local SDK audit commands without depending on optional SDK availability during documentation builds.",
                "",
                "## Reproduction Commands",
                "",
                "```bash",
                "quantum-bench sdk-parity --save-json artifacts/sdk_parity.json --save-csv artifacts/sdk_parity.csv --save-report artifacts/sdk_parity.md",
                "quantum-bench noise-audit --save-json artifacts/noise_matrix.json --save-csv artifacts/noise_matrix.csv --save-report artifacts/noise_matrix.md",
                "quantum-bench roundtrip-audit --targets cirq qiskit_aer pennylane braket_local qibo_numpy --include-hamiltonian --include-workflow --save-json artifacts/roundtrip_audit.json --save-csv artifacts/roundtrip_audit.csv --save-report artifacts/roundtrip_audit.md",
                "```",
                "",
                "## SDK Parity Scorecard",
                "",
                "*Raw assets:* [`sdk_parity.json`](../examples/reference_results/sdk_audits_2026-06-05/sdk_parity.json), [`sdk_parity.csv`](../examples/reference_results/sdk_audits_2026-06-05/sdk_parity.csv), [`sdk_parity.md`](../examples/reference_results/sdk_audits_2026-06-05/sdk_parity.md).",
                "",
                *_parity_table(audits["parity"]),
                "",
                "## Noise Model Matrix",
                "",
                "*Raw assets:* [`noise_matrix.json`](../examples/reference_results/sdk_audits_2026-06-05/noise_matrix.json), [`noise_matrix.csv`](../examples/reference_results/sdk_audits_2026-06-05/noise_matrix.csv), [`noise_matrix.md`](../examples/reference_results/sdk_audits_2026-06-05/noise_matrix.md).*",
                "",
                *_noise_table(audits["noise"]),
                "",
                "## Round-Trip Translation Audit",
                "",
                "*Raw assets:* [`roundtrip_audit.json`](../examples/reference_results/sdk_audits_2026-06-05/roundtrip_audit.json), [`roundtrip_audit.csv`](../examples/reference_results/sdk_audits_2026-06-05/roundtrip_audit.csv), [`roundtrip_audit.md`](../examples/reference_results/sdk_audits_2026-06-05/roundtrip_audit.md).*",
                "",
                *_roundtrip_table(audits["roundtrip"]),
                "",
                "## Interpretation",
                "",
                "- `sdk-parity` is a capability scorecard, not an execution benchmark.",
                "- `noise-audit` reports which local adapters receive project-injected noise models. Noise models are adapter-specific and should not be treated as physically identical.",
                "- `roundtrip-audit` verifies neutral circuit, Pauli Hamiltonian, and parameterized workflow semantics through SDK source generation and reimport.",
            ]
        ).rstrip()
        + "\n"
    )


def _parity_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| SDK | circuits | workflows | Pauli terms | result objects | grouping | noise models |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        noise = ", ".join(sorted(row.get("noise_models", {}))) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["sdk"]),
                    _yes(row.get("circuit_translation")),
                    _yes(row.get("workflow_translation")),
                    _yes(row.get("pauli_hamiltonians")),
                    _yes(row.get("result_normalization")),
                    _yes(row.get("measurement_grouping")),
                    noise,
                ]
            )
            + " |"
        )
    return lines


def _noise_table(rows: list[dict[str, Any]]) -> list[str]:
    models = ["depolarizing", "bit_flip", "phase_flip", "amplitude_damping", "readout_error"]
    lines = [
        "| backend | " + " | ".join(models) + " | scope |",
        "| --- | " + " | ".join("---" for _ in models) + " | --- |",
    ]
    for row in rows:
        values = [str(row["models"].get(model, "")) for model in models]
        lines.append(
            "| " + " | ".join([str(row["backend"]), *values, str(row["comparison_scope"])]) + " |"
        )
    return lines


def _roundtrip_table(rows: list[dict[str, Any]]) -> list[str]:
    summary: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        key = (str(row["audit"]), str(row["target"]))
        summary.setdefault(key, []).append(str(row["status"]))
    lines = [
        "| audit | target | rows | passed |",
        "| --- | --- | ---: | --- |",
    ]
    for (audit, target), statuses in sorted(summary.items()):
        passed = all(status == "passed" for status in statuses)
        lines.append(f"| {audit} | {target} | {len(statuses)} | {_yes(passed)} |")
    return lines


def _yes(value: object) -> str:
    return "yes" if value else "no"


if __name__ == "__main__":
    raise SystemExit(main())
