import pennylane as qml

coeff = get_coeff()  # noqa: F821
hamiltonian = qml.Hamiltonian([coeff], [qml.PauliZ(0)])
