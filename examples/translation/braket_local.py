from braket.circuits import Circuit

theta = 0.5
circuit = Circuit()
circuit.h(0)
circuit.ry(1, angle=theta)
circuit.cnot(0, 1)
circuit.probability(target=[0, 1])
