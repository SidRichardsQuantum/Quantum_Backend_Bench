"""Create a compact Markdown report from an experiment result bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def main() -> None:
    source = Path("artifacts/research/runtime_scaling.json")
    if not source.exists():
        print(f"{source} does not exist. Run:")
        print("  quantum-bench experiment run examples/manifests/runtime_scaling.json")
        return

    bundle = json.loads(source.read_text(encoding="utf-8"))
    destination = Path("artifacts/research/runtime_scaling_report.md")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_render_report(bundle), encoding="utf-8")
    print(f"Wrote {destination}")


def _render_report(bundle: dict[str, Any]) -> str:
    environment = bundle.get("environment", {})
    git = environment.get("git", {})
    lines = [
        f"# {bundle.get('manifest', {}).get('name', 'Experiment Report')}",
        "",
        f"- schema: `{bundle.get('schema_version')}`",
        f"- python: `{environment.get('python', {}).get('version')}`",
        f"- platform: `{environment.get('platform', {}).get('system')}`",
        f"- git commit: `{git.get('commit')}`",
        f"- git dirty: `{git.get('dirty')}`",
        "",
        "| case | backend | repeats | shots | runtime mean | runtime stddev | depth | TVD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in bundle.get("results", []):
        metrics = result.get("metrics", {})
        metadata = result.get("metadata", {})
        lines.append(
            "| "
            + " | ".join(
                [
                    str(metadata.get("case_label", result.get("benchmark"))),
                    str(result.get("backend")),
                    str(result.get("repeats")),
                    str(result.get("shots")),
                    _fmt(metrics.get("runtime_seconds_mean")),
                    _fmt(metrics.get("runtime_seconds_stddev")),
                    _fmt(metrics.get("depth")),
                    _fmt(metrics.get("total_variation_distance")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


if __name__ == "__main__":
    main()
