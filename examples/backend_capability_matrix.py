"""Print installed backend capabilities for planning local studies."""

from __future__ import annotations

from quantum_backend_bench import backend_capabilities


def main() -> None:
    headers = [
        "name",
        "installed",
        "noise",
        "shots",
        "statevector",
        "external",
        "transpile_time",
    ]
    rows = []
    for capability in backend_capabilities():
        rows.append(
            [
                capability.name,
                "yes" if capability.installed else "no",
                capability.noise_support,
                "yes" if capability.shot_sampling else "no",
                "yes" if capability.exact_statevector else "no",
                "yes" if capability.external_process else "no",
                "yes" if capability.includes_transpilation_time else "no",
            ]
        )

    widths = [
        max(len(str(value)) for value in [header, *column])
        for header, column in zip(headers, zip(*rows, strict=False))
    ]
    print(" | ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(width) for value, width in zip(row, widths)))


if __name__ == "__main__":
    main()
