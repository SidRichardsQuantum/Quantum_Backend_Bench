import pennylane as qml

wires = list(range(2))
dev = qml.device("default.qubit", wires=2)


@qml.qnode(dev)
def circuit():
    qml.CNOT(wires=wires)
    return qml.sample(wires=wires)
