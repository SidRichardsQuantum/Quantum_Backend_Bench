from qiskit import QuantumCircuit

circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.rz(1.5707963267948966, 1)
circuit.cx(0, 1)
circuit.measure(0, 1)
circuit.measure(1, 0)
