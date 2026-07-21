import json

import pennylane as qml

shots = 512
parameter_bindings = {"theta": 1.5707963267948966}
dev = qml.device("default.qubit", wires=2, shots=shots)


@qml.qnode(dev)
def circuit(theta=parameter_bindings["theta"]):
    qml.Hadamard(wires=0)
    qml.RX(theta, wires=1)
    qml.CNOT(wires=[0, 1])
    return (
        qml.sample(wires=[0, 1]),
        qml.probs(wires=[0, 1]),
        qml.expval(qml.Hamiltonian([1.0], [qml.PauliZ(0) @ qml.PauliZ(1)])),
    )


raw_result = circuit()
raw_results = raw_result if isinstance(raw_result, tuple) else (raw_result,)
counts = {}
probabilities = {}
expectations = {}
samples_0 = raw_results[0].tolist()
sample_rows_0 = samples_0 if samples_0 and isinstance(samples_0[0], list) else [samples_0]
counts = {}
for sample in sample_rows_0:
    state = "".join(str(int(bit)) for bit in sample)
    counts[state] = counts.get(state, 0) + 1
probability_values_1 = raw_results[1].tolist()
probabilities = {
    format(state, "02b"): float(value) for state, value in enumerate(probability_values_1)
}
expectations["expectation_2"] = float(raw_results[2])
if counts:
    probabilities = {state: count / shots for state, count in counts.items()}
neutral_result = {
    "schema_version": "0.1",
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": expectations,
    "metadata": {"source_format": "pennylane"},
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
