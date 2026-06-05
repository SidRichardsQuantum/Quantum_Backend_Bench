from qiskit.quantum_info import SparsePauliOp

hamiltonian = SparsePauliOp.from_list(
    [
        ("ZZ", 0.5),
        ("XI", -1.25),
    ]
)
