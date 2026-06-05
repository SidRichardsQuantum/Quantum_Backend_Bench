import cirq

qubits = cirq.LineQubit.range(2)
hamiltonian = 0.5 * cirq.Z(qubits[0]) * cirq.Z(qubits[1]) + -1.25 * cirq.X(qubits[0])
