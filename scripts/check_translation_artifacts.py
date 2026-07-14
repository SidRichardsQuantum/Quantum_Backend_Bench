"""Check generated translation audit artifacts for drift."""

from __future__ import annotations

import argparse
import json
import runpy
import shutil
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSLATION_EXAMPLES = REPO_ROOT / "examples" / "translation"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate migration and roundtrip audit examples and fail on drift."
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary regenerated example tree for inspection.",
    )
    args = parser.parse_args()

    tmp_path = Path(tempfile.mkdtemp(prefix="quantum-bench-translation-artifacts-"))
    try:
        copied_examples = _copy_translation_examples(tmp_path)
        _run_generator(copied_examples / "migration_audit" / "generate_expected.py")
        _run_generator(copied_examples / "roundtrip_audit" / "generate_expected.py")
        failures = [
            *_compare_migration_artifacts(copied_examples),
            *_compare_roundtrip_artifacts(copied_examples),
        ]
        if failures:
            for failure in failures:
                print(failure)
            if args.keep_temp:
                print(f"Regenerated artifacts kept under: {tmp_path}")
            return 1
        if args.keep_temp:
            print(f"Regenerated artifacts kept under: {tmp_path}")
    finally:
        if not args.keep_temp:
            shutil.rmtree(tmp_path, ignore_errors=True)
    return 0


def _copy_translation_examples(tmp_path: Path) -> Path:
    copied_root = tmp_path / "examples" / "translation"
    copied_root.parent.mkdir(parents=True)
    shutil.copytree(
        TRANSLATION_EXAMPLES,
        copied_root,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    return copied_root


def _run_generator(script_path: Path) -> None:
    namespace = runpy.run_path(str(script_path))
    result = namespace["main"]()
    if result != 0:
        raise SystemExit(f"{script_path} exited with {result}")


def _compare_migration_artifacts(copied_examples: Path) -> list[str]:
    return _compare_expected_files(
        committed_dir=TRANSLATION_EXAMPLES / "migration_audit" / "expected",
        generated_dir=copied_examples / "migration_audit" / "expected",
        names=[
            "qiskit_static_bell_to_cirq_check.json",
            "qiskit_static_bell_to_cirq_check.md",
        ],
    )


def _compare_roundtrip_artifacts(copied_examples: Path) -> list[str]:
    return _compare_expected_files(
        committed_dir=TRANSLATION_EXAMPLES / "roundtrip_audit" / "expected",
        generated_dir=copied_examples / "roundtrip_audit" / "expected",
        names=[
            "qiskit_static_bell_to_cirq_roundtrip.json",
            "qiskit_static_bell_to_cirq_roundtrip.md",
        ],
    )


def _compare_expected_files(
    *, committed_dir: Path, generated_dir: Path, names: list[str]
) -> list[str]:
    failures = []
    for name in names:
        committed = committed_dir / name
        generated = generated_dir / name
        if name.endswith(".json"):
            committed_value = _json_with_normalized_source_paths(committed)
            generated_value = _json_with_normalized_source_paths(generated)
            if generated_value != committed_value:
                failures.append(f"translation artifact drift: {name}")
        elif generated.read_text(encoding="utf-8") != committed.read_text(encoding="utf-8"):
            failures.append(f"translation artifact drift: {name}")
    return failures


def _json_with_normalized_source_paths(path: Path) -> object:
    def normalize(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: "<source_path>" if key == "source_path" else normalize(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    return normalize(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())
