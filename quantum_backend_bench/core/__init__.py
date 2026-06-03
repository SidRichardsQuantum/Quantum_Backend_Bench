"""Core benchmarking abstractions."""

from quantum_backend_bench.core.benchmark_spec import (
    BenchmarkSpec,
    CircuitOperation,
    InternalCircuit,
)
from quantum_backend_bench.core.circuit_export import (
    export_benchmark_circuit,
    import_openqasm_circuit,
)
from quantum_backend_bench.core.diagnostics import diagnose_result_parity
from quantum_backend_bench.core.exact import (
    exact_amplitudes,
    exact_probabilities,
    pauli_z_expectation,
)
from quantum_backend_bench.core.hardware import write_hardware_artifacts
from quantum_backend_bench.core.sweeps import expand_benchmark_sweep, parse_sweep_specs
from quantum_backend_bench.core.draw import draw_benchmark
from quantum_backend_bench.core.diff import (
    compare_result_sets,
    diff_passed,
    format_diff_table,
    load_result_file,
)
from quantum_backend_bench.core.doctor import doctor_checks, doctor_passed, format_doctor_table
from quantum_backend_bench.core.factory import BENCHMARK_BUILDERS, build_benchmark_from_config
from quantum_backend_bench.core.runner import run_benchmark

__all__ = [
    "pauli_z_expectation",
    "import_openqasm_circuit",
    "exact_amplitudes",
    "write_hardware_artifacts",
    "parse_sweep_specs",
    "export_benchmark_circuit",
    "expand_benchmark_sweep",
    "exact_probabilities",
    "diagnose_result_parity",
    "BENCHMARK_BUILDERS",
    "BenchmarkSpec",
    "CircuitOperation",
    "InternalCircuit",
    "build_benchmark_from_config",
    "compare_result_sets",
    "diff_passed",
    "doctor_checks",
    "doctor_passed",
    "draw_benchmark",
    "format_diff_table",
    "format_doctor_table",
    "load_result_file",
    "run_benchmark",
]
