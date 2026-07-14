from qiskit import QuantumCircuit


def get_target():
    return 0


target = get_target()
circuit = QuantumCircuit(1)
circuit.reset(target)
