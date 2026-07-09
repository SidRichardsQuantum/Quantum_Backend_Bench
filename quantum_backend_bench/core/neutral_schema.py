"""Neutral translation schema identifiers and metadata helpers."""

from __future__ import annotations

NEUTRAL_SCHEMA_VERSION = "0.1"

NEUTRAL_SCHEMA_IDS = {
    "internal-json": "internal-circuit",
    "pauli-json": "pauli-json",
    "workflow-json": "workflow-json",
    "result-json": "result-json",
}

NEUTRAL_SCHEMA_FILES = {
    "internal-json": "docs/schemas/internal-circuit.schema.json",
    "pauli-json": "docs/schemas/pauli-json.schema.json",
    "workflow-json": "docs/schemas/workflow-json.schema.json",
    "result-json": "docs/schemas/result-json.schema.json",
}


def schema_id_for_format(format_name: str | None) -> str | None:
    """Return the neutral schema identifier for a CLI format name, when any."""

    if format_name is None:
        return None
    return NEUTRAL_SCHEMA_IDS.get(format_name)


def schema_file_for_format(format_name: str | None) -> str | None:
    """Return the documented JSON Schema path for a CLI format name, when any."""

    if format_name is None:
        return None
    return NEUTRAL_SCHEMA_FILES.get(format_name)


def report_schema_metadata(
    *, from_format: str | None = None, to_format: str | None = None
) -> dict[str, object]:
    """Return schema metadata shared by translation reports."""

    return {
        "neutral_schema_version": NEUTRAL_SCHEMA_VERSION,
        "input_schema": schema_id_for_format(from_format),
        "input_schema_path": schema_file_for_format(from_format),
        "output_schema": schema_id_for_format(to_format),
        "output_schema_path": schema_file_for_format(to_format),
    }
