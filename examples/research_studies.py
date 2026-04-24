"""Run bundled research-style benchmark manifests."""

from __future__ import annotations

from pathlib import Path

from quantum_backend_bench.core.manifest import run_experiment_manifest

MANIFESTS = [
    "runtime_scaling.json",
    "noise_sensitivity.json",
    "structure_vs_runtime.json",
]


def main() -> int:
    manifest_dir = Path(__file__).parent / "manifests"
    for manifest_name in MANIFESTS:
        bundle = run_experiment_manifest(manifest_dir / manifest_name)
        print(f"{manifest_name}: {len(bundle['results'])} result rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
