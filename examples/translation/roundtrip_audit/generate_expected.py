from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum_backend_bench.core.circuit_translate import (  # noqa: E402
    translate_circuit_source,
    translation_result_report,
)


def _markdown(report: dict[str, object]) -> str:
    verification = report["verification"]
    assert isinstance(verification, dict)
    contract = report["semantic_contract"]
    assert isinstance(contract, dict)
    diagnostics = report["diagnostics"]
    assert isinstance(diagnostics, list)
    lines = [
        "# Qiskit Static Bell to Cirq Round Trip",
        "",
        f"- from: `{report['from_format']}`",
        f"- to: `{report['to_format']}`",
        f"- guarantee: {contract['guarantee']}",
        f"- verification: `{verification['mode']}`",
        f"- passed: `{verification['passed']}`",
        f"- details: {verification['details']}",
        "",
        "## Diagnostics",
        *[f"- `{item['code']}`: {item['message']}" for item in diagnostics],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    source_path = (
        REPO_ROOT / "examples" / "translation" / "migration_audit" / "qiskit_static_bell.py"
    )
    result = translate_circuit_source(
        source_path.read_text(encoding="utf-8"),
        from_format="qiskit",
        to_format="cirq",
        verify="exact",
    )
    report = translation_result_report(
        result,
        source_path=str(source_path),
        from_format="qiskit",
        to_format="cirq",
    )
    expected = ROOT / "expected"
    expected.mkdir(exist_ok=True)
    (expected / "qiskit_static_bell_to_cirq_roundtrip.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (expected / "qiskit_static_bell_to_cirq_roundtrip.md").write_text(
        _markdown(report), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
