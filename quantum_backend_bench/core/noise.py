"""Neutral noise validation and placement helpers."""

from __future__ import annotations

from quantum_backend_bench.core.benchmark_spec import CircuitOperation, NoiseInstruction

NOISE_CHANNELS = {
    "depolarizing",
    "bit_flip",
    "phase_flip",
    "amplitude_damping",
    "readout_error",
}
NOISE_PLACEMENTS = {"after_circuit", "after_operation", "after_each_operation", "readout"}


def validate_noise(noise: list[NoiseInstruction], n_qubits: int, operation_count: int) -> None:
    """Validate neutral noise channels, targets, probabilities, and placement."""

    for item in noise:
        if item.channel not in NOISE_CHANNELS:
            raise ValueError(f"Unsupported neutral noise channel: {item.channel}")
        if item.placement not in NOISE_PLACEMENTS:
            raise ValueError(f"Unsupported neutral noise placement: {item.placement}")
        if not 0.0 <= item.probability <= 1.0:
            raise ValueError("Noise probability must be between 0 and 1.")
        if not item.targets or any(target < 0 or target >= n_qubits for target in item.targets):
            raise ValueError("Noise targets must be nonempty valid circuit qubits.")
        if item.placement == "after_operation":
            if item.operation_index is None or not 0 <= item.operation_index < operation_count:
                raise ValueError(
                    "after_operation noise requires a valid zero-based operation_index."
                )
        elif item.operation_index is not None:
            raise ValueError(f"Noise placement '{item.placement}' cannot define operation_index.")
        if item.channel == "readout_error" and item.placement != "readout":
            raise ValueError("readout_error noise must use placement='readout'.")
        if item.placement == "readout" and item.channel != "readout_error":
            raise ValueError("Only readout_error may use placement='readout'.")


def noise_after_operation(
    noise: list[NoiseInstruction], operation_index: int, operation: CircuitOperation
) -> list[NoiseInstruction]:
    """Return channels scheduled immediately after one circuit operation."""

    scheduled = [
        item
        for item in noise
        if item.placement == "after_operation" and item.operation_index == operation_index
    ]
    if operation.gate not in {"BARRIER", "DELAY"}:
        scheduled.extend(item for item in noise if item.placement == "after_each_operation")
    return scheduled


def noise_after_circuit(noise: list[NoiseInstruction]) -> list[NoiseInstruction]:
    return [item for item in noise if item.placement == "after_circuit"]


def readout_noise(noise: list[NoiseInstruction]) -> list[NoiseInstruction]:
    return [item for item in noise if item.placement == "readout"]
