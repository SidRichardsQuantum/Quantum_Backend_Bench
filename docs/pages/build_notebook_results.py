"""Build docs/RESULTS.md and assets from executed notebook artifacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_ARTIFACTS = ROOT / "artifacts" / "notebooks"
DOC_ASSETS = ROOT / "docs" / "pages" / "assets" / "notebooks"
RESULTS_DOC = ROOT / "docs" / "RESULTS.md"

NOTEBOOK_RESULT_FILES = {
    "quickstart": "quickstart_cirq_smoke.json",
    "comparison": "local_simulator_comparison.json",
    "hamiltonian": "hamiltonian_case_study.json",
    "sdk_cirq": "sdk_cirq_workflow.json",
    "sdk_qiskit": "sdk_qiskit_workflow.json",
    "sdk_pennylane": "sdk_pennylane_workflow.json",
    "sdk_braket": "sdk_braket_workflow.json",
    "sdk_qutip": "sdk_qutip_workflow.json",
}


def main() -> int:
    missing = [
        name for name in NOTEBOOK_RESULT_FILES.values() if not (NOTEBOOK_ARTIFACTS / name).exists()
    ]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            f"Missing notebook artifacts: {joined}. Run the notebooks first, then rerun this script."
        )

    DOC_ASSETS.mkdir(parents=True, exist_ok=True)
    results = {
        key: _load_json(NOTEBOOK_ARTIFACTS / file_name)
        for key, file_name in NOTEBOOK_RESULT_FILES.items()
    }
    _copy_raw_artifacts()
    _build_plots(results)
    RESULTS_DOC.write_text(_render_results_doc(results), encoding="utf-8")
    print(f"Wrote {RESULTS_DOC.relative_to(ROOT)}")
    print(f"Wrote notebook result assets under {DOC_ASSETS.relative_to(ROOT)}")
    return 0


def _load_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of results in {path}")
    return payload


def _copy_raw_artifacts() -> None:
    for source in sorted(NOTEBOOK_ARTIFACTS.glob("*.json")):
        shutil.copyfile(source, DOC_ASSETS / source.name)
    for source in sorted(NOTEBOOK_ARTIFACTS.glob("*.csv")):
        shutil.copyfile(source, DOC_ASSETS / source.name)


def _build_plots(results: dict[str, list[dict[str, Any]]]) -> None:
    import matplotlib.pyplot as plt

    _plot_quickstart_smoke(results["quickstart"], plt)
    _plot_local_comparison(results["comparison"], plt)
    _plot_local_quality(results["comparison"], plt)
    _plot_hamiltonian_runtime(results["hamiltonian"], plt)
    _plot_hamiltonian_structure(results["hamiltonian"], plt)
    _plot_sdk_tvd(_sdk_results(results), plt)


def _plot_quickstart_smoke(results: list[dict[str, Any]], plt: Any) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.bar(
        [_case_label(result) for result in results],
        [_runtime(result) for result in results],
        color="#457b9d",
    )
    axis.set_title("Quickstart smoke suite runtime")
    axis.set_ylabel("seconds")
    axis.tick_params(axis="x", rotation=25)
    figure.tight_layout()
    _save_plot(figure, plt, "quickstart_smoke_runtime.png")


def _plot_local_comparison(results: list[dict[str, Any]], plt: Any) -> None:
    backends = sorted({result["backend"] for result in results})
    benchmarks = sorted({result["benchmark"] for result in results})
    width = 0.8 / len(benchmarks)
    positions = list(range(len(backends)))

    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    for offset, benchmark in enumerate(benchmarks):
        subset = [result for result in results if result["benchmark"] == benchmark]
        by_backend = {result["backend"]: result for result in subset}
        x = [position + (offset - (len(benchmarks) - 1) / 2) * width for position in positions]
        axes[0].bar(
            x, [_runtime(by_backend[backend]) for backend in backends], width=width, label=benchmark
        )
        axes[1].bar(
            x,
            [by_backend[backend]["metrics"].get("depth") or 0 for backend in backends],
            width=width,
            label=benchmark,
        )
    axes[0].set_title("Runtime by backend")
    axes[0].set_ylabel("seconds")
    axes[1].set_title("Circuit depth by backend")
    axes[1].set_ylabel("depth")
    for axis in axes:
        axis.set_xticks(positions)
        axis.set_xticklabels(backends, rotation=25)
        axis.legend(title="benchmark")
    figure.tight_layout()
    _save_plot(figure, plt, "local_simulator_runtime_depth.png")


def _plot_local_quality(results: list[dict[str, Any]], plt: Any) -> None:
    rows = [
        result
        for result in results
        if result["metrics"].get("total_variation_distance") is not None
    ]
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.bar(
        [f"{result['backend']} / {result['benchmark']}" for result in rows],
        [result["metrics"]["total_variation_distance"] for result in rows],
        color="#2a9d8f",
    )
    axis.set_title("Total variation distance by backend")
    axis.set_ylabel("TVD")
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    _save_plot(figure, plt, "local_simulator_tvd.png")


def _plot_hamiltonian_runtime(results: list[dict[str, Any]], plt: Any) -> None:
    figure, axis = plt.subplots(figsize=(9, 4))
    for backend in sorted({result["backend"] for result in results}):
        subset = [result for result in results if result["backend"] == backend]
        labels = [_hamiltonian_case(result) for result in subset]
        axis.plot(labels, [_runtime(result) for result in subset], marker="o", label=backend)
    axis.set_title("Hamiltonian simulation runtime by case")
    axis.set_ylabel("seconds")
    axis.tick_params(axis="x", rotation=25)
    axis.legend(title="backend")
    figure.tight_layout()
    _save_plot(figure, plt, "hamiltonian_runtime.png")


def _plot_hamiltonian_structure(results: list[dict[str, Any]], plt: Any) -> None:
    unique: dict[tuple[int, float, int], dict[str, Any]] = {}
    for result in results:
        parameters = result.get("parameters", {})
        key = (
            int(result["n_qubits"]),
            float(parameters.get("time", 0.0)),
            int(parameters.get("trotter_steps", 0)),
        )
        unique.setdefault(key, result)
    ordered = [unique[key] for key in sorted(unique)]
    labels = [_hamiltonian_case(result) for result in ordered]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar(
        labels, [result["metrics"].get("depth") or 0 for result in ordered], color="#e76f51"
    )
    axes[0].set_title("Circuit depth")
    axes[0].set_ylabel("depth")
    axes[1].bar(
        labels, [result["metrics"].get("gate_count") or 0 for result in ordered], color="#457b9d"
    )
    axes[1].set_title("Gate count")
    axes[1].set_ylabel("gates")
    for axis in axes:
        axis.tick_params(axis="x", rotation=30)
    figure.tight_layout()
    _save_plot(figure, plt, "hamiltonian_structure.png")


def _plot_sdk_tvd(results: list[dict[str, Any]], plt: Any) -> None:
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.bar(
        [result["backend"] for result in results],
        [_tvd(result) for result in results],
        color="#6f4bb2",
    )
    axis.set_title("SDK GHZ total variation distance")
    axis.set_ylabel("TVD")
    axis.tick_params(axis="x", rotation=25)
    figure.tight_layout()
    _save_plot(figure, plt, "sdk_ghz_tvd.png")


def _save_plot(figure: Any, plt: Any, file_name: str) -> None:
    figure.savefig(DOC_ASSETS / file_name, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _render_results_doc(results: dict[str, list[dict[str, Any]]]) -> str:
    sdk_results = _sdk_results(results)
    return "\n".join(
        [
            "# Results",
            "",
            "This page is generated from executed tutorial notebook artifacts. The source notebooks live in `../notebooks/`, and their saved JSON/CSV outputs are copied from `../artifacts/notebooks/` into `pages/assets/notebooks/` for the documentation site.",
            "",
            "The numbers demonstrate result shape, plotting, and qualitative benchmark behavior. Runtime values are local-machine dependent and should not be read as universal backend rankings.",
            "",
            "## Reproduce These Outputs",
            "",
            "Run the notebooks in order, or execute their code cells with a notebook runner, then rebuild this page:",
            "",
            "```bash",
            "python docs/pages/build_notebook_results.py",
            "python docs/pages/build_site.py",
            "```",
            "",
            "The builder expects these notebook-generated files under `../artifacts/notebooks/`: `quickstart_cirq_smoke.json`, `local_simulator_comparison.json`, `hamiltonian_case_study.json`, and the five `sdk_*_workflow.json` files.",
            "",
            "## Quickstart Cirq Smoke Suite",
            "",
            "Generated by `01_quickstart_cirq.ipynb`. This compact run exercises GHZ, Bernstein-Vazirani, and Grover through the local Cirq backend.",
            "",
            _results_table(results["quickstart"]),
            "",
            "![Quickstart smoke suite runtime](pages/assets/notebooks/quickstart_smoke_runtime.png)",
            "",
            "Raw notebook artifacts: [JSON](pages/assets/notebooks/quickstart_cirq_smoke.json) and [CSV](pages/assets/notebooks/quickstart_cirq_smoke.csv).",
            "",
            "## Local Simulator Comparison",
            "",
            "Generated by `02_compare_local_simulators.ipynb`. The notebook compares installed local simulator SDKs on GHZ and QFT using the same package runner.",
            "",
            _results_table(results["comparison"]),
            "",
            "![Local simulator runtime and depth](pages/assets/notebooks/local_simulator_runtime_depth.png)",
            "",
            "![Local simulator total variation distance](pages/assets/notebooks/local_simulator_tvd.png)",
            "",
            "Raw notebook artifacts: [JSON](pages/assets/notebooks/local_simulator_comparison.json) and [CSV](pages/assets/notebooks/local_simulator_comparison.csv).",
            "",
            "## Hamiltonian Simulation Case Study",
            "",
            "Generated by `03_hamiltonian_simulation_case_study.ipynb`. The notebook varies qubits, evolution time, and Trotter steps for a small Ising-style Hamiltonian simulation study.",
            "",
            _results_table(results["hamiltonian"]),
            "",
            "![Hamiltonian runtime](pages/assets/notebooks/hamiltonian_runtime.png)",
            "",
            "![Hamiltonian structure](pages/assets/notebooks/hamiltonian_structure.png)",
            "",
            "Raw notebook artifacts: [JSON](pages/assets/notebooks/hamiltonian_case_study.json) and [CSV](pages/assets/notebooks/hamiltonian_case_study.csv).",
            "",
            "## SDK Workflow Notebooks",
            "",
            "Generated by `04_sdk_cirq_workflow.ipynb` through `08_sdk_qutip_workflow.ipynb`. These notebooks share the same GHZ export, local execution, artifact, and verification workflow across SDK adapters.",
            "",
            _results_table(sdk_results),
            "",
            "![SDK GHZ total variation distance](pages/assets/notebooks/sdk_ghz_tvd.png)",
            "",
            _sdk_links(),
            "",
            "## Interpretation Notes",
            "",
            "- Runtime comparisons are only meaningful for the local environment where the notebooks were executed.",
            "- Circuit depth and gate-count metrics are structural checks and should be more stable than wall-clock timing.",
            "- Total variation distance is computed against the expected distribution where the benchmark defines one.",
            "- Success probability is reported only for benchmarks with a meaningful target state or oracle success condition.",
            "- Noise-heavy examples remain in the examples workflow rather than this notebook-derived page because noisy simulation can be much slower.",
            "",
        ]
    )


def _results_table(results: list[dict[str, Any]]) -> str:
    lines = [
        "| Case | Backend | Runtime (s) | Depth | Gates | TVD | Success |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        metrics = result["metrics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_pipe(_case_label(result)),
                    result["backend"],
                    _fmt(metrics.get("runtime_seconds")),
                    _fmt(metrics.get("depth")),
                    _fmt(metrics.get("gate_count")),
                    _fmt(metrics.get("total_variation_distance")),
                    _fmt(metrics.get("success_probability")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _sdk_results(results: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        results["sdk_cirq"][0],
        results["sdk_qiskit"][0],
        results["sdk_pennylane"][0],
        results["sdk_braket"][0],
        results["sdk_qutip"][0],
    ]


def _sdk_links() -> str:
    stems = [
        "sdk_cirq_workflow",
        "sdk_qiskit_workflow",
        "sdk_pennylane_workflow",
        "sdk_braket_workflow",
        "sdk_qutip_workflow",
    ]
    links = [f"[{stem}.json](pages/assets/notebooks/{stem}.json)" for stem in stems]
    return "Raw notebook artifacts: " + ", ".join(links) + "."


def _case_label(result: dict[str, Any]) -> str:
    return result.get("metadata", {}).get("case_label") or result.get("benchmark", "")


def _hamiltonian_case(result: dict[str, Any]) -> str:
    parameters = result.get("parameters", {})
    return (
        f"n={result['n_qubits']} t={parameters.get('time')} "
        f"steps={parameters.get('trotter_steps')}"
    )


def _runtime(result: dict[str, Any]) -> float:
    return float(result["metrics"].get("runtime_seconds") or 0.0)


def _tvd(result: dict[str, Any]) -> float:
    return float(result["metrics"].get("total_variation_distance") or 0.0)


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _escape_pipe(value: str) -> str:
    return value.replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
