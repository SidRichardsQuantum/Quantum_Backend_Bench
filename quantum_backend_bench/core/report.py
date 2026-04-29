"""Markdown report generation for benchmark result files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantum_backend_bench.core.diff import load_result_file
from quantum_backend_bench.core.discovery import result_case_label


def load_report_input(path: str | Path) -> dict[str, Any]:
    """Load a JSON result bundle, JSON result list, or CSV result export."""

    source = Path(path)
    if source.suffix.lower() == ".csv":
        return {"source": str(source), "results": load_result_file(source)}
    data = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return {"source": str(source), **data}
    if isinstance(data, list):
        return {"source": str(source), "results": data}
    raise ValueError("Report input must be a result list, result bundle, or CSV export.")


def save_markdown_report(
    bundle: dict[str, Any],
    path: str | Path,
    *,
    title: str = "Quantum Backend Benchmark Report",
) -> Path:
    """Render and save a Markdown report for benchmark results."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(format_markdown_report(bundle, title=title), encoding="utf-8")
    return destination


def format_markdown_report(
    bundle: dict[str, Any],
    *,
    title: str = "Quantum Backend Benchmark Report",
) -> str:
    """Render a Markdown report for benchmark results."""

    results = list(bundle.get("results", []))
    lines = [
        f"# {title}",
        "",
        "## Overview",
        "",
        f"- result rows: `{len(results)}`",
        f"- source: `{bundle.get('source') or bundle.get('manifest_path') or 'in-memory'}`",
    ]
    manifest = bundle.get("manifest") or {}
    if manifest.get("description"):
        lines.append(f"- description: {manifest['description']}")
    if manifest.get("backends"):
        lines.append(
            f"- manifest backends: `{', '.join(str(item) for item in manifest['backends'])}`"
        )
    lines.extend(["", "## Results", ""])
    lines.extend(_results_table(results))
    lines.extend(["", "## Backend Caveats", ""])
    lines.extend(_backend_caveats(results))
    environment = bundle.get("environment") or _first_environment(results)
    if environment:
        lines.extend(["", "## Environment", ""])
        lines.extend(_environment_lines(environment))
    return "\n".join(lines).rstrip() + "\n"


def _results_table(results: list[dict[str, Any]]) -> list[str]:
    if not results:
        return ["No results found."]
    lines = [
        "| case | backend | repeats | shots | runtime mean | runtime stddev | depth | success | TVD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        metrics = result.get("metrics", {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(result_case_label(result)),
                    _escape(str(result.get("backend"))),
                    str(result.get("repeats", "")),
                    str(result.get("shots", "")),
                    _fmt(metrics.get("runtime_seconds")),
                    _fmt(metrics.get("runtime_seconds_stddev")),
                    _fmt(metrics.get("depth")),
                    _fmt(metrics.get("success_probability")),
                    _fmt(metrics.get("total_variation_distance")),
                ]
            )
            + " |"
        )
    return lines


def _backend_caveats(results: list[dict[str, Any]]) -> list[str]:
    caveats: dict[str, dict[str, Any]] = {}
    for result in results:
        backend = str(result.get("backend"))
        metadata = result.get("metadata", {})
        caveats.setdefault(
            backend,
            {
                "noise": metadata.get("backend_noise_support"),
                "transpilation": metadata.get("runtime_includes_transpilation"),
                "external": metadata.get("external_process"),
                "local": metadata.get("local_only"),
                "packages": metadata.get("backend_package_versions") or {},
            },
        )
    if not caveats:
        return ["No backend metadata found."]
    lines = [
        "| backend | noise support | includes transpilation | external process | local only | packages |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for backend, values in sorted(caveats.items()):
        packages = ", ".join(
            f"{name}={version}" for name, version in sorted(values["packages"].items())
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(backend),
                    _escape(str(values["noise"])),
                    _escape(str(values["transpilation"])),
                    _escape(str(values["external"])),
                    _escape(str(values["local"])),
                    _escape(packages or "n/a"),
                ]
            )
            + " |"
        )
    return lines


def _environment_lines(environment: dict[str, Any]) -> list[str]:
    python = environment.get("python", {})
    platform = environment.get("platform", {})
    git = environment.get("git", {})
    lines = []
    if python.get("version"):
        lines.append(f"- python: `{python['version']}`")
    platform_label = platform.get("platform") or " ".join(
        str(part)
        for part in (platform.get("system"), platform.get("release"), platform.get("machine"))
        if part
    )
    if platform_label:
        lines.append(f"- platform: `{platform_label}`")
    if git.get("commit"):
        lines.append(f"- git commit: `{git['commit']}`")
    if git.get("dirty") is not None:
        lines.append(f"- git dirty: `{git['dirty']}`")
    return lines or ["No environment metadata found."]


def _first_environment(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    for result in results:
        environment = result.get("metadata", {}).get("environment")
        if isinstance(environment, dict):
            return environment
    return None


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _escape(value: str) -> str:
    return value.replace("|", "\\|")
