from __future__ import annotations

import json

import pytest

from quantum_backend_bench.core.benchmark_spec import CircuitOperation, NoiseInstruction
from quantum_backend_bench.core.circuit_translate import (
    TranslationError,
    import_circuit_source,
    translate_circuit_source,
    verify_translation,
)
from quantum_backend_bench.core.neutral_simulator import (
    density_matrix_trace_distance,
    simulate_density_matrix,
    simulate_density_probabilities,
)


def _noisy_source(
    channel: str = "amplitude_damping",
    probability: float = 0.25,
    placement: str = "after_operation",
) -> str:
    noise: dict[str, object] = {
        "channel": channel,
        "targets": [0],
        "probability": probability,
        "placement": placement,
    }
    if placement == "after_operation":
        noise["operation_index"] = 0
    return json.dumps(
        {
            "schema_version": "0.1",
            "n_qubits": 1,
            "operations": [{"gate": "X", "qubits": [0]}],
            "measurements": [0],
            "noise": [noise],
        }
    )


def test_density_matrix_models_amplitude_damping_and_readout_error() -> None:
    operations = [CircuitOperation("X", (0,))]
    damping = [NoiseInstruction("amplitude_damping", (0,), 1.0, "after_operation", 0)]
    readout = [NoiseInstruction("readout_error", (0,), 1.0, "readout")]

    assert simulate_density_probabilities(1, operations, [0], damping) == pytest.approx(
        {"0": 1.0, "1": 0.0}
    )
    assert simulate_density_probabilities(1, [], [0], readout) == pytest.approx(
        {"0": 0.0, "1": 1.0}
    )


def test_noise_placement_changes_density_matrix_semantics() -> None:
    operations = [CircuitOperation("X", (0,)), CircuitOperation("X", (0,))]
    after_first = [NoiseInstruction("amplitude_damping", (0,), 1.0, "after_operation", 0)]
    after_circuit = [NoiseInstruction("amplitude_damping", (0,), 1.0)]

    left = simulate_density_matrix(1, operations, after_first)
    right = simulate_density_matrix(1, operations, after_circuit)

    assert density_matrix_trace_distance(left, right) == pytest.approx(1.0)


@pytest.mark.parametrize("target", ["cirq", "pennylane", "braket_local", "qibo_numpy"])
def test_noisy_sdk_roundtrip_passes_density_matrix_verification(target: str) -> None:
    result = translate_circuit_source(
        _noisy_source(),
        from_format="internal-json",
        to_format=target,
        verify="density-matrix",
    )

    assert result.verification is not None
    assert result.verification.passed
    assert result.verification.density_matrix_trace_distance == pytest.approx(0.0)
    assert result.verification.total_variation_distance == pytest.approx(0.0)


def test_density_matrix_verification_detects_changed_native_noise() -> None:
    source = _noisy_source(probability=0.25)
    original, _ = import_circuit_source(source, from_format="internal-json")
    emitted = translate_circuit_source(source, from_format="internal-json", to_format="cirq").source

    verification = verify_translation(
        original,
        emitted.replace("amplitude_damp(0.25)", "amplitude_damp(0.5)"),
        to_format="cirq",
        mode="density-matrix",
    )

    assert not verification.passed
    assert verification.density_matrix_trace_distance == pytest.approx(0.25)


def test_density_matrix_verification_rejects_comment_only_noise_target() -> None:
    with pytest.raises(TranslationError, match="target_unrepresentable"):
        translate_circuit_source(
            _noisy_source(),
            from_format="internal-json",
            to_format="qiskit_aer",
            verify="density-matrix",
        )


def test_qibo_roundtrips_readout_error_placement() -> None:
    result = translate_circuit_source(
        _noisy_source("readout_error", placement="readout"),
        from_format="internal-json",
        to_format="qibo_numpy",
        verify="density-matrix",
    )

    assert result.verification is not None
    assert result.verification.passed
    assert "ReadoutErrorChannel" in result.source


def test_non_qibo_readout_roundtrip_is_explicitly_unsupported() -> None:
    with pytest.raises(TranslationError, match="readout_unrepresentable"):
        translate_circuit_source(
            _noisy_source("readout_error", placement="readout"),
            from_format="internal-json",
            to_format="cirq",
            verify="density-matrix",
        )


def test_noise_placement_json_is_backward_compatible() -> None:
    old, _ = import_circuit_source(
        _noisy_source().replace(', "placement": "after_operation", "operation_index": 0', ""),
        from_format="internal-json",
    )
    current = json.loads(
        translate_circuit_source(
            _noisy_source(), from_format="internal-json", to_format="internal-json"
        ).source
    )

    assert old.circuit_data.noise[0].placement == "after_circuit"
    assert current["noise"][0]["placement"] == "after_operation"
    assert current["noise"][0]["operation_index"] == 0
