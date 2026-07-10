from qiskit import QuantumCircuit

theta = 0.25
phi = 0.5
n_qubits = 3

circuit = QuantumCircuit(n_qubits)
for wire in range(n_qubits):
    circuit.ry(theta, wire)
circuit.rz(phi, 1)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure_all()
