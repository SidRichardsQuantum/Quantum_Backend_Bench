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
counts = {}
probabilities = {}
neutral_result = {
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": {},
    "metadata": {"source_format": "pennylane"},
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
