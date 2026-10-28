# Command-Line Tools

| Tool | Language | Built by | Status |
|------|----------|----------|--------|
| `preset_validator` | Python 3 (+ C++ placeholder) | `validate.py`; CMake builds the placeholder | Working: schema + pack checks; the C++ binary refuses and points to `validate.py` |
| `ocio_inspector` | C++17 | CMake (`tools/ocio_inspector`) | Prints OCIO version; validates a config and lists its spaces and displays |
| `preset_packager` | Python 3 | — | Validates, then zips a pack rooted at its folder |

---

## preset_validator

```
preset_validator <file.json>
```

**Current behaviour:** `tools/preset_validator/validate.py FILE|DIR...` checks presets
against `src/presets/schema/lookpreset.schema.json`; for a `pack.json` it also checks that
every listed look exists and is valid. Exits 0 when everything passes, 1 otherwise, and
runs in CI and `ctest`. The C++ `preset_validator` binary is a placeholder that exits 2 and
points at `validate.py` until native validation lands.

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

Prints `OCIO Version: <x.y.z>`, then loads the config named on the command line (or `$OCIO`),
runs `config->validate()`, and lists its colour spaces and displays. Exits 1 if the config
fails to load or validate:

```
ocio_inspector assets/ocio/config.ocio
```

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

Walks `input_folder` recursively and writes it into a ZIP. Needs `jsonschema` for the validation step.

**Current behaviour:** validates the pack first (and refuses to package on failure), stores
paths rooted at the pack folder (`starter_pack/pack.json`, `starter_pack/looks/...`), uses
`ZIP_DEFLATED`, and skips dotfiles.

**Specified CLI:**

```
preset_packager PACK_DIR OUT.zip [--validate] [--sign KEYFILE]
```
