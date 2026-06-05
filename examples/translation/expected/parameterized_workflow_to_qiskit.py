import json

from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit.quantum_info import SparsePauliOp

theta = Parameter("theta")
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.rx(theta, 1)
circuit.cx(0, 1)
circuit.measure(range(circuit.num_qubits), range(circuit.num_qubits))
parameter_bindings = {"theta": 1.5707963267948966}
bound_circuit = circuit.assign_parameters(parameter_bindings)
shots = 512
simulator = AerSimulator()
compiled_circuit = transpile(bound_circuit, simulator)
result = simulator.run(compiled_circuit, shots=shots).result()
counts = result.get_counts()
probabilities = {state: count / shots for state, count in counts.items()}
probability_targets_1 = [0, 1]
observable_2 = SparsePauliOp.from_list([("ZZ", 1.0)])
# Evaluate observable_2 with qiskit.quantum_info estimator tooling when available.
neutral_result = {
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": {},
    "metadata": {"source_format": "qiskit_aer"},
}
print(json.dumps(neutral_result, indent=2, sort_keys=True))

workflow_spec = json.loads("""
{
  "measurements": [
    {
      "targets": [
        0,
        1
      ],
      "type": "counts"
    },
    {
      "targets": [
        0,
        1
      ],
      "type": "probabilities"
    },
    {
      "observable": {
        "n_qubits": 2,
        "terms": [
          {
            "coefficient": 1.0,
            "paulis": {
              "0": "Z",
              "1": "Z"
            }
          }
        ]
      },
      "targets": [
        0,
        1
      ],
      "type": "expectation"
    }
  ],
  "n_qubits": 2,
  "name": "parameterized_bell_workflow",
  "operations": [
    {
      "controls": [],
      "gate": "H",
      "parameter": null,
      "targets": [
        0
      ]
    },
    {
      "controls": [],
      "gate": "RX",
      "parameter": "theta",
      "targets": [
        1
      ]
    },
    {
      "controls": [
        0
      ],
      "gate": "CNOT",
      "parameter": null,
      "targets": [
        1
      ]
    }
  ],
  "parameter_bindings": {
    "theta": 1.5707963267948966
  },
  "parameters": [
    "theta"
  ],
  "seed": 1234,
  "shots": 512
}
""")
