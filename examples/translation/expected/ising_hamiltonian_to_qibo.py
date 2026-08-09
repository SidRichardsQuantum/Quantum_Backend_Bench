from qibo.hamiltonians import SymbolicHamiltonian
from qibo.symbols import X, Z

hamiltonian = SymbolicHamiltonian(
    0.5 * Z(0) * Z(1) + -1.25 * X(0),
    nqubits=2,
)
