# Command-Line Tools

| Tool | Language | Built by | Status |
|------|----------|----------|--------|
| `preset_validator` | C++17 | CMake (`tools/preset_validator`) | Skeleton — prints, no checks |
| `ocio_inspector` | C++17 | CMake (needs CMakeLists, see below) | Prints OCIO version |
| `preset_packager` | Python 3 | — | Working zip packer |

---

## preset_validator

```
preset_validator <file.json>
```

**Current behaviour:** prints `Validating preset: <file>` then `Validation complete.` and exits 0 for
any input. Schema validation is a `TODO`. Exit 1 with usage if no argument.

> ⚠ Because it always succeeds, do not rely on it in CI yet. Use `check-jsonschema` (see
> [getting-started.md](getting-started.md#5-run-the-tools)).

**Specified behaviour (v1):**

```
preset_validator [--schema PATH] [--pack] [--json] [--strict] FILE...
```

| Flag | Effect |
|------|--------|
| `--schema PATH` | Override schema (default: embedded copy of `lookpreset.schema.json`) |
| `--pack` | Treat FILE as `pack.json`; validate the pack and every listed look |
| `--json` | Machine-readable output |
| `--strict` | Also run *lint* rules (below) as errors |

Lint rules (warnings by default):

| Rule | Check |
|------|-------|
| `matrix-row-sum` | Each film-matrix row sums to 1 ± 0.03 |
| `matrix-offdiag` | Off-diagonals within ±0.15 |
| `tint-magnitude` | Tint components within ±0.05 |
| `halation-dead-slider` | `halation.enabled = false` but `halation_amount > 0` |
| `grain-dead-slider` | Same for grain |
| `id-filename` | File name equals `<id>.json` |
| `thumbnail-missing` | `assets/thumbnails/<id>.png` exists |

Exit codes: `0` valid, `1` usage, `2` schema error, `3` lint error under `--strict`, `4` I/O error.

Implementation plan: `nlohmann/json` + `nlohmann/json-schema-validator` (or `valijson`), schema
embedded at build time via `file(READ …)` into a generated header. Note the CMake target currently
links `OpenColorIO::OpenColorIO`, which the validator does not need — drop it, or use it to check
that `working_space` names resolve in the bundled config (a useful extra check).

---

## ocio_inspector

```
ocio_inspector
```

Prints `OCIO Version: <x.y.z>`.

**Build fixes required:** add `tools/ocio_inspector/CMakeLists.txt` and `namespace OCIO =
OCIO_NAMESPACE;` (see [getting-started.md](getting-started.md#known-build-issues)).

**Specified behaviour:**

```
ocio_inspector [--config PATH|builtin|env] [--list] [--roles] [--check]
               [--transform SRC DST R G B]
```

| Flag | Output |
|------|--------|
| `--config` | Config to inspect; `env` uses `$OCIO` |
| `--list` | Colour spaces with family and encoding |
| `--roles` | Role → colour space mapping |
| `--check` | Runs `config->validate()` and reports errors |
| `--transform` | Converts one RGB triplet, prints result — handy for preset debugging |

---

## preset_packager

```
python3 tools/preset_packager/main.py <input_folder> <output.zip>
```

Walks `input_folder` recursively and writes every file into a ZIP. No third-party dependencies.

**Caveats in the current implementation:**

1. **Archive paths include the input path.** `z.write(path)` stores the path as given, e.g.
   `assets/presets/packs/starter_pack/pack.json`. Packs should be rooted at the pack folder. Fix:
   `z.write(path, arcname=os.path.relpath(path, os.path.dirname(input_folder.rstrip('/'))))`
   (keeps `starter_pack/` as the top folder).
2. **No compression** — `ZipFile` defaults to `ZIP_STORED`; pass `compression=zipfile.ZIP_DEFLATED`.
3. **No filtering** — `.DS_Store` and editor temp files are included.
4. **No validation** — invalid looks are packaged.
5. **Non-deterministic** — `os.walk` order and file mtimes vary; sort names and set a fixed
   `ZipInfo.date_time` for reproducible archives.
6. Signing ("zip/sign packs", per the original README) is not implemented. Planned: Ed25519 detached
   signature `pack.sig` over a manifest of SHA-256 hashes.

**Specified CLI:**

```
preset_packager PACK_DIR OUT.zip [--validate] [--sign KEYFILE]
```
