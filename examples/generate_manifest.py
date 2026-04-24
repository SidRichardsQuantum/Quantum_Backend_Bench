"""Generate a small experiment manifest from installed execution backends."""

from __future__ import annotations

import json
from pathlib import Path

from quantum_backend_bench import backend_capabilities


def main() -> None:
    installed_backends = [
        capability.name
        for capability in backend_capabilities()
        if capability.role == "execution" and capability.installed and capability.local_only
    ]
    if not installed_backends:
        installed_backends = ["cirq"]

    manifest = {
        "name": "generated-local-smoke-study",
        "description": "Generated manifest using installed local execution backends.",
        "backends": installed_backends,
        "shots": 128,
        "repeats": 3,
        "benchmarks": [
            {"benchmark": "ghz", "n_qubits": 3},
            {"benchmark": "bernstein-vazirani", "n_qubits": 4, "secret_string": "101"},
            {"benchmark": "random-circuit", "n_qubits": 4, "depth": 8, "seed": 42},
        ],
        "outputs": {
            "json": "artifacts/research/generated_smoke.json",
            "csv": "artifacts/research/generated_smoke.csv",
            "suite_plot": "artifacts/research/generated_smoke.png",
        },
    }

    destination = Path("artifacts/manifests/generated_smoke.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {destination}")
    print(f"Backends: {', '.join(installed_backends)}")


if __name__ == "__main__":
    main()
