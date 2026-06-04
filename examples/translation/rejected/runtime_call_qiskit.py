from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService

circuit = QuantumCircuit(1)
circuit.h(0)
service = QiskitRuntimeService()
backend = service.backend("ibm_test")
backend.run(circuit)
