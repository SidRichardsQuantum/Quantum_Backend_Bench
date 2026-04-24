"""Generate a focused depolarizing-noise experiment manifest."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    manifest = {
        "name": "generated-ghz-noise-sweep",
        "description": "Generated GHZ depolarizing-noise sweep for noise-capable adapters.",
        "backends": ["cirq", "pennylane"],
        "shots": 512,
        "repeats": 3,
        "benchmarks": [
            {
                "benchmark": "ghz",
                "n_qubits": 5,
                "noise_levels": [0.0, 0.001, 0.005, 0.01, 0.02, 0.05],
            }
        ],
        "outputs": {
            "json": "artifacts/research/generated_noise.json",
            "csv": "artifacts/research/generated_noise.csv",
            "suite_plot": "artifacts/research/generated_noise.png",
        },
    }
    destination = Path("artifacts/manifests/generated_noise.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
