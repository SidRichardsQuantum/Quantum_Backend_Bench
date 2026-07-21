import json

import cirq
import sympy

qubits = cirq.LineQubit.range(2)
circuit = cirq.Circuit()
theta = sympy.Symbol("theta")
circuit.append(cirq.H(qubits[0]))
circuit.append(cirq.rx(theta)(qubits[1]))
circuit.append(cirq.CNOT(qubits[0], qubits[1]))
parameter_resolver = {"theta": 1.5707963267948966}
shots = 512
simulator = cirq.Simulator(seed=1234)
expectations = {}
observable_2 = 1.0 * cirq.Z(qubits[0]) * cirq.Z(qubits[1])
expectations["expectation_2"] = float(
    simulator.simulate_expectation_values(
        circuit, observables=[observable_2], param_resolver=parameter_resolver
    )[0].real
)
distribution_targets = [0, 1]
measurement_qubits = [qubits[index] for index in distribution_targets]
measurement_circuit = circuit + cirq.measure(*measurement_qubits, key="m")
result = simulator.run(measurement_circuit, repetitions=shots, param_resolver=parameter_resolver)
histogram = result.histogram(key="m")
counts = {format(key, "02b"): int(value) for key, value in histogram.items()}
probabilities = {state: count / shots for state, count in counts.items()}
neutral_result = {
    "schema_version": "0.1",
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": expectations,
    "metadata": {"source_format": "cirq"},
}
print(json.dumps(neutral_result, indent=2, sort_keys=True))

workflow_spec = {
    "schema_version": "0.1",
    "name": "parameterized_bell_workflow",
    "n_qubits": 2,
    "parameters": ["theta"],
    "parameter_bindings": {"theta": 1.5707963267948966},
    "operations": [
        {"gate": "H", "targets": [0], "controls": [], "parameter": None},
        {"gate": "RX", "targets": [1], "controls": [], "parameter": "theta"},
        {"gate": "CNOT", "targets": [1], "controls": [0], "parameter": None},
    ],
    "measurements": [
        {"type": "counts", "targets": [0, 1]},
        {"type": "probabilities", "targets": [0, 1]},
        {
            "type": "expectation",
            "targets": [0, 1],
            "observable": {
                "schema_version": "0.1",
                "n_qubits": 2,
                "terms": [{"coefficient": 1.0, "paulis": {"0": "Z", "1": "Z"}}],
            },
        },
    ],
    "shots": 512,
    "seed": 1234,
}
