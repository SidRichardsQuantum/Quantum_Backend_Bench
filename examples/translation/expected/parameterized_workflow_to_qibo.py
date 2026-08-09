import json

import qibo
from qibo import Circuit, gates
from qibo.hamiltonians import SymbolicHamiltonian
from qibo.symbols import Z

parameter_bindings = {"theta": 1.5707963267948966}
theta = parameter_bindings["theta"]
circuit = Circuit(2)
circuit.add(gates.H(0))
circuit.add(gates.RX(1, theta))
circuit.add(gates.CNOT(0, 1))
shots = 512
backend = qibo.construct_backend("numpy")
backend.set_seed(1234)
expectations = {}
observable_2 = SymbolicHamiltonian(
    1.0 * Z(0) * Z(1),
    nqubits=2,
    backend=backend,
)
expectations["expectation_2"] = float(observable_2.expectation(circuit).real)
sampling_circuit = circuit.copy(deep=True)
distribution_targets = [0, 1]
sampling_circuit.add(gates.M(*distribution_targets, register_name="result"))
result = backend.execute_circuit(sampling_circuit, nshots=shots)
counts = {str(state): int(count) for state, count in result.frequencies(binary=True).items()}
probabilities = {state: count / shots for state, count in counts.items()}
neutral_result = {
    "schema_version": "0.1",
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": expectations,
    "metadata": {"source_format": "qibo_numpy"},
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
