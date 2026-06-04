from __future__ import annotations

import argparse
from pathlib import Path

from quantum_backend_bench.core.circuit_translate import translate_circuit_source

ROOT = Path(__file__).resolve().parent
CASES = [
    ("qiskit_registers.py", "qiskit", "cirq", "expected/qiskit_registers_to_cirq.py"),
    ("cirq_nested.py", "cirq", "qiskit_aer", "expected/cirq_nested_to_qiskit.py"),
    ("ghz.qasm", "openqasm", "pennylane", "expected/ghz_qasm_to_pennylane.py"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate translation expected outputs.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero if generated outputs differ instead of updating files.",
    )
    args = parser.parse_args(argv)

    changed: list[Path] = []
    for source_name, from_format, to_format, expected_name in CASES:
        source = (ROOT / source_name).read_text(encoding="utf-8")
        result = translate_circuit_source(
            source, from_format=from_format, to_format=to_format, verify="exact"
        )
        expected_path = ROOT / expected_name
        if args.check:
            existing = expected_path.read_text(encoding="utf-8")
            if existing != result.source:
                changed.append(expected_path)
        else:
            expected_path.write_text(result.source, encoding="utf-8")
            print(f"updated {expected_path.relative_to(ROOT)}")

    if changed:
        for path in changed:
            print(f"out of date: {path.relative_to(ROOT)}")
        return 1
    if args.check:
        print("translation expected outputs are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
