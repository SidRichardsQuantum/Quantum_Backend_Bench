"""Backend registry."""

from __future__ import annotations

from quantum_backend_bench.backends.base_backend import BaseBackend
from quantum_backend_bench.backends.braket_backend import BraketLocalBackend
from quantum_backend_bench.backends.cirq_backend import CirqBackend
from quantum_backend_bench.backends.cudaq_backend import CudaQBackend
from quantum_backend_bench.backends.pennylane_backend import PennyLaneBackend
from quantum_backend_bench.backends.pyquil_backend import PyQuilQVMBackend
from quantum_backend_bench.backends.qiskit_backend import QiskitAerBackend
from quantum_backend_bench.backends.qutip_backend import QuTiPBackend

BACKEND_REGISTRY: dict[str, type[BaseBackend]] = {
    "braket_local": BraketLocalBackend,
    "cirq": CirqBackend,
    "cudaq": CudaQBackend,
    "pennylane": PennyLaneBackend,
    "pyquil_qvm": PyQuilQVMBackend,
    "qiskit_aer": QiskitAerBackend,
    "qutip": QuTiPBackend,
}


def get_backend(name: str) -> BaseBackend:
    """Instantiate a backend by name."""

    try:
        return BACKEND_REGISTRY[name]()
    except KeyError as exc:
        available = ", ".join(sorted(BACKEND_REGISTRY))
        raise ValueError(f"Unknown backend '{name}'. Available backends: {available}") from exc


__all__ = ["BACKEND_REGISTRY", "BaseBackend", "get_backend"]
