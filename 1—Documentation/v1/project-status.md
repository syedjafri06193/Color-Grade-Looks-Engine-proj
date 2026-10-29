# Project Status & Roadmap

Snapshot of the repository as of October 2026.

## Implemented

| Area | Item |
|------|------|
| Build | Root `CMakeLists.txt` (C++17; OCIO required; Metal + OBJCXX on Apple only; `ctest` preset check) |
| Build | `FindOpenColorIO.cmake`, `FindMetal.cmake`, `CompileShaders.cmake` |
| Presets | JSON Schema v1 (`lookpreset.schema.json`) |
| Presets | Built-in looks: *Neutral Film*, *Soft Contrast Film* |
| Presets | Starter pack (`pack.json` + `looks/`) |
| Colour | Minimal OCIO v2 config: `lin_rec709`, exact sRGB display, `raw`; roles, display and views |
| GPU | `Common.metal` uniform struct + helpers |
| GPU | `ColorLooks_BasicStage`: exposure, pivoted log contrast, saturation; output clamped to the half range |
| Tools | `ocio_inspector` (version + config validation), `validate.py` (schema + pack checks), `preset_packager` (validated, rooted, deflated zip) |
| Repo | `.clang-format`, `.editorconfig`, `.gitignore`, proprietary `LICENSE`, GitHub Actions CI |

## Known issues

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| 9 | Luma weights hard-coded to Rec.709 in `Common.metal` | Slight saturation error in ACEScg | Pass weights from OCIO (`getDefaultLumaCoefs`) through the params struct |
| 16 | C++ `preset_validator` is a placeholder | Native validation pending; the binary exits 2 and points to `validate.py` | Embed the schema and validate natively |

### Fixed

| # | Issue | Fix |
|---|-------|-----|
| 1 | `tools/ocio_inspector/CMakeLists.txt` missing | Added |
| 2 | `OCIO` namespace undefined | `namespace OCIO = OCIO_NAMESPACE;` |
| 3 | `preset_validator` never validated | `tools/preset_validator/validate.py`; the C++ stub no longer reports false success |
| 4 | `soft_contrast_film.json` at repo root | Moved to `assets/presets/builtin/` |
| 5 | `starter_pack/looks/` missing | Added; packs are checked for dead references |
| 6 | `curvePoint` tuple-form `items` | `prefixItems` + `items: false` |
| 7 | OCIO config: 2.2 gamma, no displays/views, few roles | Exact sRGB, display + views, full role set |
| 8 | `preset_packager` full paths, no compression | Rooted at the pack folder, `ZIP_DEFLATED`, validates first |
| 10 | Kernel could overflow `half` on write | Clamp to 65504 before the half write |
| 11 | `LICENSE` wrapped in markdown | Plain text (wording unchanged) |
| 12 | Empty `1—Documentation/README.md` | Now the documentation index; superseded `docs/` stubs removed |
| 13 | Root README was a tree in an unclosed code fence | Rewritten |
| 14 | No CI | `.github/workflows/ci.yml` (Linux + macOS) |
| 15 | `preset_validator` linked OCIO unnecessarily | Dropped |
| — | CMake required Metal/OBJCXX on every OS | Apple-only; tools build anywhere |

## Roadmap

### Milestone 1 — Foundations
- ~~Fix known issues 1–8~~ (done)
- `common`, `presets` modules (load, validate, version)
- `color` CPU reference: exposure, contrast, matrix, saturation, balance, tone map, gamut
- Unit tests + fixtures (schema check in CI: done)

### Milestone 2 — GPU look graph
- Fused Metal kernel for stages 2–9 with function constants
- OCIO GPU shader integration
- `MetalBackend`, `MetalPipelineCache`
- GPU-vs-CPU parity tests, performance benchmark

### Milestone 3 — Texture stages
- Curves (LUT baking + GPU sampling)
- Grain `procedural_v1`
- Halation (threshold, half-res separable blur, composite)

### Milestone 4 — Host integration
- OFX plug-in, parameter binding, look selector, thumbnails
- Pack search paths, user packs
- Tested in Resolve, Nuke, Natron

### Milestone 5 — Release
- Bundle, signing, notarisation, installer
- CI workflows active
- 6–10 additional built-in looks

### Later
- `lookpack.schema.json`, pack signing
- Preset schema v2: `matrix_space`, `filmic_v2`, per-look luma weights
- 3D LUT export (`.cube`) for hosts without the plug-in
- Additional backends (CUDA/Vulkan) behind `GPUBackend`
