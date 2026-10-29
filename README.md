# Color Looks MVP

[![CI](https://github.com/syedjafri06193/color-looks-mvp-v.1/actions/workflows/ci.yml/badge.svg)](https://github.com/syedjafri06193/color-looks-mvp-v.1/actions/workflows/ci.yml)

A film-look colour grading engine for OFX hosts (DaVinci Resolve, Nuke,
Natron): versioned JSON look presets, a scene-referred OpenColorIO v2 colour
pipeline, and Metal GPU kernels.

**Status: early foundation (v1).** What exists today is the preset schema
and two built-in looks, a starter look pack, a minimal OCIO config, the first
Metal kernel (exposure, pivoted contrast, saturation), and tooling to
validate and package presets. The engine, OFX plug-in and CPU reference are
designed but not yet built — see the
[project status and roadmap](1—Documentation/v1/project-status.md).

## Quick start

Requires CMake 3.22+, a C++17 compiler, OpenColorIO 2.x and Python 3.

```bash
# macOS:  brew install opencolorio cmake
# Ubuntu: sudo apt install libopencolorio-dev cmake
pip install -r tools/preset_validator/requirements.txt

cmake -S . -B build
cmake --build build
ctest --test-dir build                       # validates every preset and pack

./build/tools/ocio_inspector/ocio_inspector assets/ocio/config.ocio
python3 tools/preset_validator/validate.py assets/presets
python3 tools/preset_packager/main.py assets/presets/packs/starter_pack starter_pack.zip
```

Metal is only enabled on macOS; the tools and checks build on any OS.

## Repository layout

```
.
├── 1—Documentation/          all documentation (start with its README)
├── assets/
│   ├── presets/builtin/      Neutral Film, Soft Contrast Film
│   ├── presets/packs/        starter_pack (pack.json + looks/)
│   └── ocio/config.ocio      bundled OCIO v2 config (lin_rec709, sRGB, raw)
├── src/
│   ├── presets/schema/       lookpreset.schema.json (JSON Schema 2020-12)
│   └── gpu/metal/shaders/    Common.metal, PipelineKernels.metal
├── tools/
│   ├── preset_validator/     validate.py (schema + pack checks)
│   ├── preset_packager/      validated look-pack zips
│   └── ocio_inspector/       OCIO config validation and listing
└── cmake/                    FindOpenColorIO, FindMetal, CompileShaders
```

## Documentation

All documentation lives in [`1—Documentation/`](1—Documentation/README.md):
architecture, colour management, the look pipeline, preset authoring and
schema reference, the Metal backend, OFX integration, packaging, testing and
the roadmap.

<!-- project-metrics:start -->
## Project Metrics

[![Stars](https://img.shields.io/github/stars/syedjafri06193/Color-Grade-Looks-Engine-proj?style=flat-square)](https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj/stargazers) [![Forks](https://img.shields.io/github/forks/syedjafri06193/Color-Grade-Looks-Engine-proj?style=flat-square)](https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj/forks) [![Open issues](https://img.shields.io/github/issues/syedjafri06193/Color-Grade-Looks-Engine-proj?style=flat-square)](https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj/issues) [![Last commit](https://img.shields.io/github/last-commit/syedjafri06193/Color-Grade-Looks-Engine-proj/improvements?style=flat-square)](https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj/commits/improvements) [![Commits](https://img.shields.io/github/commit-activity/t/syedjafri06193/Color-Grade-Looks-Engine-proj?style=flat-square)](https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj/commits/improvements) [![Top language](https://img.shields.io/github/languages/top/syedjafri06193/Color-Grade-Looks-Engine-proj?style=flat-square)](https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj) [![Repo size](https://img.shields.io/github/repo-size/syedjafri06193/Color-Grade-Looks-Engine-proj?style=flat-square)](https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj)

### Code

| Metric | Value |
|---|---|
| Lines of code | 201 |
| Source files | 10 |
| Tracked files | 48 |
| Documentation | 21 Markdown files (12,648 words) |
| Commits | 38 |
| Contributors | 1 |
| Active | 2026-02-15 → 2026-10-28 |

| Language | Lines | Share |
|---|---:|---:|
| Python | 93 | 46.3% |
| Metal | 45 | 22.4% |
| CMake | 34 | 16.9% |
| C++ | 29 | 14.4% |

### Performance

| Metric | Result |
|---|---|
| GPU time per frame, 1080p, all stages | < 2 ms (M-series) |
| GPU time per frame, 4K UHD | < 8 ms |
| Preset load + validation | < 10 ms |

<sub>Design budgets (targets, not yet measured), from [`1—Documentation/v1/performance.md`](1%E2%80%94Documentation/v1/performance.md).</sub>

<sub>Code stats as of 2026-10-28, counted with pygount (comments and blank lines excluded). Badges update live.</sub>
<!-- project-metrics:end -->

## License

Proprietary — see [LICENSE](LICENSE).
