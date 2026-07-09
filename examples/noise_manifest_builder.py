"""Generate a focused depolarizing-noise experiment manifest."""

from __future__ import annotations

import json
from pathlib import Path

from _common import installed_noise_backends


def main() -> None:
    backends = installed_noise_backends(limit=2)
    manifest = {
        "name": "generated-ghz-noise-sweep",
        "description": "Generated GHZ depolarizing-noise sweep for noise-capable adapters.",
        "backends": backends,
        "shots": 128,
        "repeats": 2,
        "benchmarks": [
            {
                "benchmark": "ghz",
                "n_qubits": 3,
                "noise_levels": [0.0, 0.005, 0.02],
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
    print(f"Backends: {', '.join(backends)}")


if __name__ == "__main__":
    main()
