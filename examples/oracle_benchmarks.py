"""Run deterministic oracle benchmarks on installed local backends."""

from __future__ import annotations

from _common import installed_local_backends
from quantum_backend_bench.benchmarks.bernstein_vazirani import (
    build_benchmark as build_bernstein_vazirani,
)
from quantum_backend_bench.benchmarks.deutsch_jozsa import build_benchmark as build_deutsch_jozsa
from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.summary import format_summary, summarize_results
from quantum_backend_bench.utils.formatting import format_results_table


def main() -> None:
    backends = installed_local_backends(limit=2)
    benchmarks = [
        build_bernstein_vazirani(n_qubits=4, secret_string="101"),
        build_deutsch_jozsa(n_qubits=4, oracle_type="balanced", bitmask="101"),
        build_deutsch_jozsa(n_qubits=4, oracle_type="constant", constant_value=1),
    ]

    results = []
    for benchmark in benchmarks:
        results.extend(run_benchmark(benchmark, backends, shots=128))

    print(f"Backends: {', '.join(backends)}")
    print(format_results_table(results))
    print()
    print(format_summary(summarize_results(results)))


if __name__ == "__main__":
    main()
