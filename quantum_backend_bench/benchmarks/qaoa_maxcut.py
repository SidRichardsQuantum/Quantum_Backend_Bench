"""QAOA MaxCut benchmark."""

from __future__ import annotations

import itertools

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)


def build_benchmark(
    n_qubits: int = 4,
    gamma: float = 0.8,
    beta: float = 0.4,
    graph: str = "ring",
) -> BenchmarkSpec:
    """Build a single-layer QAOA MaxCut circuit for a line or ring graph."""

    if n_qubits < 2:
        raise ValueError("qaoa-maxcut requires at least 2 qubits.")
    if graph not in {"line", "ring"}:
        raise ValueError("graph must be 'line' or 'ring'.")

    edges = _graph_edges(n_qubits, graph)
    operations = [CircuitOperation("H", (qubit,)) for qubit in range(n_qubits)]

    for control, target in edges:
        operations.append(CircuitOperation("CNOT", (control, target)))
        operations.append(CircuitOperation("RZ", (target,), {"theta": 2.0 * gamma}))
        operations.append(CircuitOperation("CNOT", (control, target)))

    for qubit in range(n_qubits):
        operations.append(CircuitOperation("RX", (qubit,), {"theta": 2.0 * beta}))

    optimal_states, optimal_cut_size = _optimal_cut_states(n_qubits, edges)
    return BenchmarkSpec(
        name="qaoa_maxcut",
        n_qubits=n_qubits,
        parameters={
            "n_qubits": n_qubits,
            "gamma": gamma,
            "beta": beta,
            "graph": graph,
        },
        circuit_data=InternalCircuit(
            n_qubits=n_qubits,
            operations=operations,
            measurements=list(range(n_qubits)),
        ),
        metadata={
            "family": "optimization",
            "algorithm": "qaoa",
            "problem": "maxcut",
            "graph": graph,
            "edges": edges,
            "target_states": optimal_states,
            "optimal_cut_size": optimal_cut_size,
        },
    )


def _graph_edges(n_qubits: int, graph: str) -> list[tuple[int, int]]:
    edges = [(qubit, qubit + 1) for qubit in range(n_qubits - 1)]
    if graph == "ring" and n_qubits > 2:
        edges.append((n_qubits - 1, 0))
    return edges


def _optimal_cut_states(n_qubits: int, edges: list[tuple[int, int]]) -> tuple[list[str], int]:
    best_size = -1
    best_states: list[str] = []
    for bits in itertools.product("01", repeat=n_qubits):
        state = "".join(bits)
        cut_size = sum(state[left] != state[right] for left, right in edges)
        if cut_size > best_size:
            best_size = cut_size
            best_states = [state]
        elif cut_size == best_size:
            best_states.append(state)
    return best_states, best_size
