"""Save backend-native circuit diagrams."""

from quantum_backend_bench.benchmarks.bernstein_vazirani import build_benchmark as build_bv
from quantum_backend_bench.benchmarks.ghz import build_benchmark as build_ghz
from quantum_backend_bench.core.draw import draw_benchmark


def main() -> None:
    draw_benchmark(
        build_bv(n_qubits=4, secret_string="101"),
        "cirq",
        save_path="artifacts/bernstein_vazirani_cirq.txt",
    )
    draw_benchmark(build_ghz(n_qubits=4), "tket", save_path="artifacts/ghz_tket.txt")
    draw_benchmark(build_ghz(n_qubits=4), "pennylane", save_path="artifacts/ghz_pennylane.png")
    print("Saved circuit diagrams under artifacts/")


if __name__ == "__main__":
    main()
