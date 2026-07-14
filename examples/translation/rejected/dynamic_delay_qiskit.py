from qiskit import QuantumCircuit


def get_duration():
    return 8


duration = get_duration()
circuit = QuantumCircuit(1)
circuit.delay(duration, 0, unit="dt")
