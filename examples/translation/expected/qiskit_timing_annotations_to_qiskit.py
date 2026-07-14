from qiskit import QuantumCircuit

circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.barrier(0, 1)
circuit.delay(8.0, 1, unit="dt")
circuit.reset(1)
circuit.measure(0, 1)
circuit.measure(1, 0)
