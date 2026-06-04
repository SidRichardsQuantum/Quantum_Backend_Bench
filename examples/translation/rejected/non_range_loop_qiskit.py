from qiskit import QuantumCircuit

wires = [0, 1]
circuit = QuantumCircuit(2)
for wire in wires:
    circuit.h(wire)
