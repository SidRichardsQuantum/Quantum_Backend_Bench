from qiskit import QuantumCircuit

circuit = QuantumCircuit(1)
# Portable rewrite of rejected/custom_gate_qiskit.py: inline the supported operation.
circuit.h(0)
circuit.measure_all()
