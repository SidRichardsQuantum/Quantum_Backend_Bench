import pennylane as qml

parameter_bindings = {"theta": 0.25}
dev = qml.device("default.qubit", wires=2, shots=256)


@qml.qnode(dev)
def circuit(theta):
    qml.RX(theta, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.probs(wires=[0, 1])
