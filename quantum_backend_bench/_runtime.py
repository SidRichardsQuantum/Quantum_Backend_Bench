"""Runtime environment setup for local execution."""

from __future__ import annotations

import os
from pathlib import Path


def configure_runtime_environment() -> None:
    """Prefer writable cache directories in Codespaces-like environments."""

    mpl_dir = Path("/tmp/matplotlib")
    numba_dir = Path("/tmp/numba")
    mpl_dir.mkdir(parents=True, exist_ok=True)
    numba_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    os.environ.setdefault("NUMBA_CACHE_DIR", str(numba_dir))


configure_runtime_environment()
