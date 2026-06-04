from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
import math

q = QuantumRegister(2, "q")
c = ClassicalRegister(2, "c")
theta = math.pi / 2

circuit = QuantumCircuit(q, c)
circuit.h(q[0])
circuit.rx(theta, q[1])
circuit.cx(q[0], q[1])
circuit.measure(q[0], c[0])
circuit.measure(q[1], c[1])
