import json

from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit.quantum_info import SparsePauliOp, Statevector

theta = Parameter("theta")
circuit = QuantumCircuit(2)
circuit.h(0)
circuit.rx(theta, 1)
circuit.cx(0, 1)
parameter_bindings = {theta: 1.5707963267948966}
bound_circuit = circuit.assign_parameters(parameter_bindings)
shots = 512
expectations = {}
observable_2 = SparsePauliOp.from_list([("ZZ", 1.0)])
expectations["expectation_2"] = float(
    Statevector.from_instruction(bound_circuit).expectation_value(observable_2).real
)
sampling_circuit = bound_circuit.copy()
sampling_circuit.measure_all()
simulator = AerSimulator()
compiled_circuit = transpile(sampling_circuit, simulator, seed_transpiler=1234)
result = simulator.run(compiled_circuit, shots=shots, seed_simulator=1234).result()
raw_counts = result.get_counts()
full_counts = {state.replace(" ", "")[::-1]: int(count) for state, count in raw_counts.items()}
counts = {}
distribution_targets = [0, 1]
for state, count in full_counts.items():
    key = "".join(state[index] for index in distribution_targets)
    counts[key] = counts.get(key, 0) + count
probabilities = {state: count / shots for state, count in counts.items()}
neutral_result = {
    "schema_version": "0.1",
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": expectations,
    "metadata": {"source_format": "qiskit_aer"},
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
