import cirq


def build_circuit():
    q = cirq.LineQubit.range(1)
    circuit = cirq.Circuit(cirq.H(q[0]))
    return circuit
