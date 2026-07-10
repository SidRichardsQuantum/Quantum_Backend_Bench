from braket.circuits import Circuit, Observable

circuit = Circuit()
circuit.h(0)
circuit.cnot(0, 1)
circuit.expectation(observable=Observable.Z() @ Observable.Z(), target=[0, 1])
