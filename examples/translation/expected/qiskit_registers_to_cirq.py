import cirq

qubits = cirq.LineQubit.range(2)
circuit = cirq.Circuit()
circuit.append(cirq.H(qubits[0]))
circuit.append(cirq.rx(1.5707963267948966)(qubits[1]))
circuit.append(cirq.CNOT(qubits[0], qubits[1]))
circuit.append(cirq.measure(qubits[0], qubits[1], key="m"))
