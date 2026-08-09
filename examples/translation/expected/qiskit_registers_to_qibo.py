from qibo import Circuit, gates

circuit = Circuit(2, density_matrix=False)
circuit.add(gates.H(0))
circuit.add(gates.RX(1, theta=1.5707963267948966))
circuit.add(gates.CNOT(0, 1))
circuit.add(gates.M(0, 1, register_name="m"))
