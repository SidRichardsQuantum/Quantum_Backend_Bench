from braket.circuits import Observable

hamiltonian_terms = [
    (0.5, Observable.Z() @ Observable.Z(), [0, 1]),
    (-1.25, Observable.X(), [0]),
]
