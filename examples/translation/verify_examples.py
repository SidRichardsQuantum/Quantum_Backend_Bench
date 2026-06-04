from __future__ import annotations

from pathlib import Path

from quantum_backend_bench.core.circuit_translate import translate_circuit_source

ROOT = Path(__file__).resolve().parent
CASES = [
    ("qiskit_registers.py", "qiskit", "cirq"),
    ("cirq_nested.py", "cirq", "qiskit_aer"),
    ("pennylane_positional.py", "pennylane", "braket_local"),
    ("braket_local.py", "braket", "pennylane"),
    ("ghz.qasm", "openqasm", "cirq"),
    ("internal_ghz.json", "internal-json", "qiskit_aer"),
]


def main() -> int:
    for filename, from_format, to_format in CASES:
        result = translate_circuit_source(
            (ROOT / filename).read_text(encoding="utf-8"),
            from_format=from_format,
            to_format=to_format,
            verify="exact",
        )
        if result.verification is None or not result.verification.passed:
            print(f"FAILED {filename} -> {to_format}")
            return 1
        print(f"PASS {filename} -> {to_format}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
