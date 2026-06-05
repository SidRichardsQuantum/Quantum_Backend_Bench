import json

import cirq
import sympy

qubits = cirq.LineQubit.range(2)
circuit = cirq.Circuit()
theta = sympy.Symbol("theta")
circuit.append(cirq.H(qubits[0]))
circuit.append(cirq.rx(theta)(qubits[1]))
circuit.append(cirq.CNOT(qubits[0], qubits[1]))
circuit.append(cirq.measure(*qubits, key="m"))
parameter_resolver = {"theta": 1.5707963267948966}
shots = 512
simulator = cirq.Simulator()
result = simulator.run(circuit, repetitions=shots, param_resolver=parameter_resolver)
histogram = result.histogram(key="m") if "m" in result.measurements else {}
counts = {format(key, "02b"): value for key, value in histogram.items()}
probabilities = {state: count / shots for state, count in counts.items()}
probability_targets_1 = [0, 1]
observable_2 = 1.0 * cirq.Z(qubits[0]) * cirq.Z(qubits[1])
# simulator.simulate_expectation_values can evaluate observable_2.
neutral_result = {
    "counts": counts,
    "shots": shots,
    "probabilities": probabilities,
    "expectations": {},
    "metadata": {"source_format": "cirq"},
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
