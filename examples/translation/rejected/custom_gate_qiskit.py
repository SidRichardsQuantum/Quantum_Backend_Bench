from qiskit import QuantumCircuit

sub = QuantumCircuit(1)
sub.h(0)
custom = sub.to_gate()
circuit = QuantumCircuit(1)
circuit.append(custom, [0])
