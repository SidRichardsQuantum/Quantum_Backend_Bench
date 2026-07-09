"""Save available backend-native circuit diagrams."""

from __future__ import annotations

from _common import installed_draw_backends
from quantum_backend_bench.benchmarks.bernstein_vazirani import build_benchmark as build_bv
from quantum_backend_bench.benchmarks.ghz import build_benchmark as build_ghz
from quantum_backend_bench.core.draw import draw_benchmark


def main() -> None:
    saved = []
    for backend in installed_draw_backends():
        if backend == "cirq":
            path = "artifacts/bernstein_vazirani_cirq.txt"
            draw_benchmark(build_bv(n_qubits=4, secret_string="101"), backend, save_path=path)
        elif backend == "tket":
            path = "artifacts/ghz_tket.txt"
            draw_benchmark(build_ghz(n_qubits=4), backend, save_path=path)
        elif backend == "pennylane":
            path = "artifacts/ghz_pennylane.png"
            draw_benchmark(build_ghz(n_qubits=4), backend, save_path=path)
        else:
            continue
        saved.append(path)
    print("Saved circuit diagrams:")
    for path in saved:
        print(f"- {path}")


if __name__ == "__main__":
    main()
