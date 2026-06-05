import pennylane as qml

hamiltonian = qml.Hamiltonian([0.5, -1.25], [qml.PauliZ(0) @ qml.PauliZ(1), qml.PauliX(0)])
