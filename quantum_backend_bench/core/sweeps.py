"""Parameter sweep expansion."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from itertools import product
from typing import Any

from quantum_backend_bench.core.benchmark_spec import BenchmarkSpec
from quantum_backend_bench.core.factory import build_benchmark_from_config


def parse_sweep_specs(specs: Iterable[str] | Mapping[str, Any] | None) -> dict[str, list[Any]]:
    """Parse CLI or manifest sweep specs."""

    parsed: dict[str, list[Any]] = {}
    if isinstance(specs, Mapping):
        for key, values in specs.items():
            parsed[str(key).replace("-", "_").strip()] = (
                list(values) if isinstance(values, list) else _parse_values(str(values))
            )
        return parsed
    for spec in specs or []:
        if "=" not in spec:
            raise ValueError(f"Sweep spec must use name=value syntax: {spec}")
        key, raw_values = spec.split("=", 1)
        key = key.replace("-", "_").strip()
        values = _parse_values(raw_values)
        if not values:
            raise ValueError(f"Sweep spec has no values: {spec}")
        parsed[key] = values
    return parsed


def expand_benchmark_sweep(
    base_config: dict[str, object], sweep_specs: dict[str, list[Any]]
) -> list[BenchmarkSpec]:
    """Build all benchmark cases for a parameter sweep."""

    if not sweep_specs:
        return [build_benchmark_from_config(base_config)]
    keys = list(sweep_specs)
    benchmarks = []
    for values in product(*(sweep_specs[key] for key in keys)):
        config = dict(base_config)
        config.update(dict(zip(keys, values, strict=True)))
        benchmarks.append(build_benchmark_from_config(config))
    return benchmarks


def _parse_values(raw_values: str) -> list[Any]:
    if ":" in raw_values and "," not in raw_values:
        parts = raw_values.split(":")
        if len(parts) not in {2, 3}:
            raise ValueError(f"Invalid range sweep: {raw_values}")
        start = int(parts[0])
        stop = int(parts[1])
        step = int(parts[2]) if len(parts) == 3 else 1
        if step == 0:
            raise ValueError("Sweep range step cannot be zero.")
        end = stop + (1 if step > 0 else -1)
        return list(range(start, end, step))
    return [_coerce_value(value.strip()) for value in raw_values.split(",") if value.strip()]


def _coerce_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value
