#!/usr/bin/env python3
"""Validate look presets and look packs.

    validate.py <preset.json | pack.json | directory> [...]

* A preset is checked against src/presets/schema/lookpreset.schema.json.
* A pack (a pack.json) must list looks that exist, and each of those looks
  must itself be a valid preset.
* A directory is searched recursively for both.

Exit status is 0 when everything is valid and 1 otherwise, so it can gate CI.
Requires: pip install jsonschema
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    sys.exit("validate.py needs jsonschema: pip install -r tools/preset_validator/requirements.txt")

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "src" / "presets" / "schema" / "lookpreset.schema.json"


def _load(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_preset(path: Path, validator) -> list[str]:
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path}: {e}"]
    return [
        f"{path}: {'/'.join(map(str, err.path)) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    ]


def validate_pack(path: Path, validator) -> list[str]:
    try:
        pack = _load(path)
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path}: {e}"]
    errors = []
    looks = pack.get("looks")
    if not isinstance(looks, list) or not looks:
        return [f"{path}: `looks` must be a non-empty list"]
    for rel in looks:
        look = (path.parent / rel).resolve()
        if not look.is_file():
            errors.append(f"{path}: listed look does not exist: {rel}")
        else:
            errors.extend(validate_preset(look, validator))
    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    schema = _load(SCHEMA_PATH)
    validator = jsonschema.validators.validator_for(schema)(schema)

    files: list[Path] = []
    for arg in argv:
        p = Path(arg)
        files.extend(sorted(p.rglob("*.json")) if p.is_dir() else [p])

    errors: list[str] = []
    checked = 0
    for f in files:
        if f.name == "pack.json":
            errors.extend(validate_pack(f, validator))
        else:
            errors.extend(validate_preset(f, validator))
        checked += 1

    for e in errors:
        print(e)
    print(f"{checked} file(s) checked, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
