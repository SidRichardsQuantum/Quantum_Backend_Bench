import pennylane as qml

theta = 0.25
parameter_bindings = {"theta": theta}
dev = qml.device("default.qubit", wires=2, shots=256)


@qml.qnode(dev)
def circuit(theta):
    qml.RX(theta, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))
