"""Run the smoke suite and save JSON/CSV artifacts."""

from quantum_backend_bench.core.runner import run_benchmark
from quantum_backend_bench.core.suites import build_suite
from quantum_backend_bench.core.summary import format_summary, summarize_results
from quantum_backend_bench.utils.formatting import format_results_table
from quantum_backend_bench.utils.io import save_csv, save_json


def main() -> None:
    results = []
    for benchmark in build_suite("smoke"):
        results.extend(run_benchmark(benchmark, ["cirq"], shots=64))

    print(format_results_table(results))
    print()
    print(format_summary(summarize_results(results)))

    save_json(results, "artifacts/smoke_suite.json")
    save_csv(results, "artifacts/smoke_suite.csv")
    print("\nSaved artifacts/smoke_suite.json and artifacts/smoke_suite.csv")


if __name__ == "__main__":
    main()
