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

## License

Proprietary — see [LICENSE](LICENSE).
