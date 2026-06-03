"""Hardware-preparation artifact helpers."""

from __future__ import annotations

from pathlib import Path

from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec
from quantum_backend_bench.core.circuit_export import export_benchmark_circuit

PROVIDERS = ("generic", "ibm", "braket", "rigetti")

_PROVIDER_NOTES = {
    "generic": [
        "Map this circuit through the target provider compiler before submission.",
        "Check basis gates, coupling constraints, and calibration data near run time.",
    ],
    "ibm": [
        "Use Qiskit to load the OpenQASM file and transpile against an IBM backend target.",
        "Review optimization level, coupling map, dynamic-circuit limits, and measurement ordering.",
    ],
    "braket": [
        "Convert the circuit with the Amazon Braket SDK or rebuild it using braket.circuits.Circuit.",
        "Select a managed device ARN and confirm shot limits and supported gates before submission.",
    ],
    "rigetti": [
        "Convert the exported circuit to Quil/pyQuil before submitting to Rigetti hardware.",
        "Confirm quilc/qcs compilation settings, topology, and readout ordering.",
    ],
}

_PROVIDER_SNIPPETS = {
    "generic": "# Load the QASM with your provider SDK, compile for a target device, then submit with credentials configured outside this bundle.",
    "ibm": "from qiskit import QuantumCircuit, transpile\nqc = QuantumCircuit.from_qasm_file('circuit.qasm')\n# compiled = transpile(qc, backend=backend, optimization_level=1)",
    "braket": "# Rebuild or convert this QASM circuit with amazon-braket-sdk, then run with AwsDevice(device_arn).run(circuit, shots=shots).",
    "rigetti": "# Convert the circuit to Quil/pyQuil, compile with quilc/QCS tooling, then submit through the Rigetti service API.",
}


def write_hardware_artifacts(
    benchmark: BenchmarkSpec,
    destination: str | Path,
    *,
    backend_hint: str | None = None,
    shots: int = 1024,
    provider: str = "generic",
    qasm_version: str = "openqasm",
) -> dict[str, Path]:
    """Write local artifacts useful when moving a benchmark circuit to hardware."""

    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Available: {', '.join(PROVIDERS)}")
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    suffix = "qasm3" if qasm_version == "openqasm3" else "qasm"
    qasm_path = root / f"{benchmark.name}.{suffix}"
    readme_path = root / "README.md"
    export_benchmark_circuit(benchmark, qasm_version, save_path=qasm_path)
    provider_notes = _PROVIDER_NOTES[provider]
    readme_path.write_text(
        "\n".join(
            [
                f"# Hardware Preparation: {benchmark.name}",
                "",
                f"- benchmark: `{benchmark.name}`",
                f"- n_qubits: `{benchmark.n_qubits}`",
                f"- suggested_shots: `{shots}`",
                f"- provider: `{provider}`",
                f"- backend_hint: `{backend_hint or 'provider-specific'}`",
                f"- qasm_version: `{qasm_version}`",
                "",
                "## Files",
                "",
                f"- `{qasm_path.name}`: circuit export for provider-side compilation.",
                "",
                "## Provider Notes",
                "",
                *[f"- {note}" for note in provider_notes],
                "",
                "## Submission Sketch",
                "",
                "```python",
                _PROVIDER_SNIPPETS[provider],
                "```",
                "",
                "## Caveats",
                "",
                "- This project does not submit jobs to cloud hardware.",
                "- Provider credentials, device selection, queue time, coupling maps, and calibration data are handled outside this artifact.",
                "- Re-run local validation before comparing hardware results with simulator outputs.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"qasm": qasm_path, "readme": readme_path}
