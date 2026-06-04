import pennylane as qml

dev = qml.device("default.qubit", wires=2)


@qml.qnode(dev)
def circuit():
    qml.Hadamard(0)
    qml.RY(0.5, 1)
    qml.CNOT([0, 1])
    return qml.sample(wires=[0, 1])
