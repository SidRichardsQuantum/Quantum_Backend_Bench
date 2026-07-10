from qiskit import QuantumCircuit

circuit = QuantumCircuit(1)
# Portable rewrite of rejected/runtime_call_qiskit.py: keep circuit construction local.
circuit.h(0)
circuit.measure_all()
