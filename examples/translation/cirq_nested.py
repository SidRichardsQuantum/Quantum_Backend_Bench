import cirq
import numpy as np

qubits = cirq.LineQubit.range(2)
circuit = cirq.Circuit(
    [
        cirq.H(qubits[0]),
        [cirq.rz(np.pi / 2)(qubits[1]), cirq.CNOT(qubits[0], qubits[1])],
        cirq.measure(qubits[0], qubits[1], key="m"),
    ]
)
