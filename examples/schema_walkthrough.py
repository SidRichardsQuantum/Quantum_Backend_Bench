"""Inspect the stable fields in a saved experiment result bundle."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    source = Path("artifacts/research/runtime_scaling.json")
    if not source.exists():
        print(f"{source} does not exist. Run:")
        print("  quantum-bench experiment run examples/manifests/runtime_scaling.json")
        return

    bundle = json.loads(source.read_text(encoding="utf-8"))
    result = bundle["results"][0]
    print("Bundle keys:", ", ".join(sorted(bundle)))
    print("Result keys:", ", ".join(sorted(result)))
    print("Metric keys:", ", ".join(sorted(result["metrics"])))
    print("Metadata keys:", ", ".join(sorted(result["metadata"])))
    print("Package versions captured:", len(bundle["environment"]["packages"]))


if __name__ == "__main__":
    main()
