# Project Status & Roadmap

Snapshot of the repository as of October 2026.

## Implemented

| Area | Item |
|------|------|
| Build | Root `CMakeLists.txt` (C++17, OBJCXX, OCIO + Metal required, tests option) |
| Build | `FindOpenColorIO.cmake`, `FindMetal.cmake`, `CompileShaders.cmake` |
| Presets | JSON Schema v1 (`lookpreset.schema.json`) |
| Presets | Built-in looks: *Neutral Film*, *Soft Contrast Film* |
| Presets | Starter pack manifest (`pack.json`) |
| Colour | Minimal OCIO v2 config (`lin_rec709`, `srgb_display`) |
| GPU | `Common.metal` uniform struct + helpers |
| GPU | `ColorLooks_BasicStage`: exposure, pivoted log contrast, saturation |
| Tools | `ocio_inspector` (prints version), `preset_validator` (stub), `preset_packager` (zip) |
| Repo | `.clang-format`, `.editorconfig`, `.gitignore`, proprietary `LICENSE` |

## Known issues

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| 1 | `tools/ocio_inspector/CMakeLists.txt` missing | CMake configure fails | Add file ([getting-started](getting-started.md#known-build-issues)) |
| 2 | `OCIO` namespace undefined in `ocio_inspector/main.cpp` | Compile error | `namespace OCIO = OCIO_NAMESPACE;` |
| 3 | `preset_validator` never validates | False confidence | Implement schema validation ([tools](tools.md#preset_validator)) |
| 4 | `soft_contrast_film.json` at repo root | Not found by builtin loaders | Move to `assets/presets/builtin/` |
| 5 | `starter_pack/looks/` missing | Pack references dead paths | Add looks ([look-packs](look-packs.md#current-repository-state)) |
| 6 | `curvePoint` uses tuple-form `items` under draft 2020-12 | Point values not type-checked | Use `prefixItems` |
| 7 | OCIO config: 2.2 gamma labelled sRGB, no displays/views, few roles | Inaccurate sRGB; some tools warn | See [colour management §4](color-management.md#4-the-bundled-config-assetsocioconfigocio) |
| 8 | `preset_packager` stores full input path in archive, no compression | Awkward pack archives | See [tools](tools.md#preset_packager) |
| 9 | Luma weights hard-coded to Rec.709 | Slight saturation error in ACEScg | Pass weights from OCIO |
| 10 | Kernel can overflow `half` on write | `inf` pixels at extreme contrast/exposure | Clamp to 65504 before half write |
| 11 | `LICENSE` file contains markdown wrapper and an unclosed code fence | Cosmetic | Keep plain text only |
| 12 | Empty `1—Documentation/README.md` folder (em-dash in name) | Confusing, awkward in shells | Remove; docs live in `docs/` |
| 13 | Root `README.md` was a tree in an unclosed code fence | Poor landing page | Replaced by new README |
| 14 | `ci/` workflows outside `.github/workflows/` | Won't run on GitHub Actions | Move or call |
| 15 | `preset_validator` links OCIO unnecessarily | Extra dependency | Drop or use for name checks |

## Roadmap

### Milestone 1 — Foundations
- Fix known issues 1–8
- `common`, `presets` modules (load, validate, version)
- `color` CPU reference: exposure, contrast, matrix, saturation, balance, tone map, gamut
- Unit tests + fixtures; schema check in CI

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
