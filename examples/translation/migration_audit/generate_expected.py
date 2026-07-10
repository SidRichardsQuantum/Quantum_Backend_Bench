from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum_backend_bench.core.circuit_translate import (  # noqa: E402
    import_circuit_source,
    translation_check_report,
)


def _markdown(report: dict[str, object]) -> str:
    audit = report["migration_audit"]
    assert isinstance(audit, dict)
    contract = report["semantic_contract"]
    assert isinstance(contract, dict)
    lines = [
        "# Qiskit Static Bell to Cirq Audit",
        "",
        f"- input format: `{report['input_format']}`",
        f"- target: `{audit['target']}`",
        f"- status: `{audit['status']}`",
        f"- guarantee: {contract['guarantee']}",
        f"- operations: {audit['operation_count']}",
        f"- gates: `{json.dumps(audit['gate_counts'], sort_keys=True)}`",
        "",
        "## Preserved",
        *[f"- {item}" for item in audit["preserved"]],
        "",
        "## Rewritten",
        *[f"- {item}" for item in audit["rewritten"]],
        "",
        "## Rejected If Present",
        *[f"- {item}" for item in audit["rejected_if_present"]],
        "",
        "## Not Modeled",
        *[f"- {item}" for item in audit["not_modeled"]],
        "",
        f"Verification: {audit['verification_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    source_path = ROOT / "qiskit_static_bell.py"
    benchmark, detected = import_circuit_source(
        source_path.read_text(encoding="utf-8"), from_format="qiskit"
    )
    report = translation_check_report(
        benchmark, detected, source_path=str(source_path), to_format="cirq"
    )
    expected = ROOT / "expected"
    expected.mkdir(exist_ok=True)
    (expected / "qiskit_static_bell_to_cirq_check.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (expected / "qiskit_static_bell_to_cirq_check.md").write_text(
        _markdown(report), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
