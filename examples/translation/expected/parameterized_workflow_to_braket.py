import json

from braket.circuits import Circuit, FreeParameter, Observable
from braket.devices import LocalSimulator

theta = FreeParameter("theta")
circuit = Circuit()
circuit.h(0)
circuit.rx(1, theta)
circuit.cnot(0, 1)
circuit.probability(target=[0, 1])
expectation_observable_0 = Observable.Z() @ Observable.Z()
circuit.expectation(observable=expectation_observable_0, target=[0, 1])
inputs = {"theta": 1.5707963267948966}
shots = 512
device = LocalSimulator()
task = device.run(circuit, shots=shots, inputs=inputs)
result = task.result()
counts = dict(result.measurement_counts)
probabilities = {state: count / shots for state, count in counts.items()}
neutral_result = {
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": {},
    "metadata": {"source_format": "braket_local"},
}
print(json.dumps(neutral_result, indent=2, sort_keys=True))

workflow_spec = {
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
                "n_qubits": 2,
                "terms": [{"coefficient": 1.0, "paulis": {"0": "Z", "1": "Z"}}],
            },
        },
    ],
    "shots": 512,
    "seed": 1234,
}
