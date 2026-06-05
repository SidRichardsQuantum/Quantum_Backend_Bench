from qiskit.quantum_info import SparsePauliOp

weight = get_weight()  # noqa: F821
hamiltonian = SparsePauliOp.from_list([("Z", weight)])
