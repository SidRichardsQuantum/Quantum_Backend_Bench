"""Packaged comparison preset manifests."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

_PRESET_PACKAGE = "quantum_backend_bench.presets"


def list_presets() -> list[str]:
    """Return available packaged preset names."""

    root = resources.files(_PRESET_PACKAGE)
    return sorted(path.stem for path in root.iterdir() if path.name.endswith(".json"))


def load_preset(name: str) -> dict[str, Any]:
    """Load a packaged preset manifest by name."""

    normalized = name.removesuffix(".json")
    if normalized not in list_presets():
        available = ", ".join(list_presets())
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")
    source = resources.files(_PRESET_PACKAGE).joinpath(f"{normalized}.json")
    return json.loads(source.read_text(encoding="utf-8"))


def write_preset(name: str, path: str | Path) -> Path:
    """Write a packaged preset manifest to a local path."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(load_preset(name), indent=2, sort_keys=True), encoding="utf-8"
    )
    return destination
