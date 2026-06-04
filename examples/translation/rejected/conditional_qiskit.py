from qiskit import QuantumCircuit

use_h = True
circuit = QuantumCircuit(1)
if use_h:
    circuit.h(0)
