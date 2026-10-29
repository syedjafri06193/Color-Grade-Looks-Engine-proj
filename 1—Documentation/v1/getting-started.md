# Getting Started

This guide takes you from a fresh clone to a working build of the tools and compiled Metal shaders.

## 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| macOS | 13 Ventura or later | Metal 3 and Apple-silicon are the primary target |
| Xcode / Command Line Tools | 15+ | Provides `clang`, `xcrun metal`, `xcrun metallib` |
| CMake | ≥ 3.22 | Enforced by `cmake_minimum_required` |
| OpenColorIO | 2.x | `brew install opencolorio` |
| Python | 3.8+ | Only for `preset_packager` (stdlib only) |

> The project declares `LANGUAGES C CXX OBJCXX`, so CMake requires an Objective-C++ compiler.
> On Linux or Windows configuration will fail; those platforms are out of scope for the MVP.

Check your toolchain:

```bash
cmake --version
xcrun -sdk macosx metal --version
brew info opencolorio | head -1
```

## 2. Clone

```bash
git clone https://github.com/syedjafri06193/Color-Grade-Looks-Engine-proj.git
cd Color-Grade-Looks-Engine-proj
```

## 3. Configure and build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

### CMake options

| Option | Default | Effect |
|--------|---------|--------|
| `COLORLOOKS_BUILD_TESTS` | `ON` | Calls `enable_testing()`; test targets will hang off this once `tests/` lands |
| `CMAKE_BUILD_TYPE` | — | Use `Debug` for development, `Release` for profiling |
| `CMAKE_PREFIX_PATH` | — | Point at a non-Homebrew OCIO install, e.g. `-DCMAKE_PREFIX_PATH=/opt/ocio` |

### How dependencies are found

* `cmake/FindOpenColorIO.cmake` searches for `OpenColorIO/OpenColorIO.h` and the `OpenColorIO`
  library and exposes the imported target **`OpenColorIO::OpenColorIO`**.
* `cmake/FindMetal.cmake` locates `Metal`, `Foundation` and `QuartzCore` frameworks and exposes the
  interface target **`Metal::Metal`**.

## Build notes

The tree configures and builds on macOS, Linux and Windows. Metal (and
Objective-C++) are only enabled on Apple platforms; elsewhere the tools and
the preset checks still build and run.

If OpenColorIO is not found with Homebrew on Apple silicon, pass
`-DCMAKE_PREFIX_PATH=$(brew --prefix)`.

## 4. Compile Metal shaders

`cmake/CompileShaders.cmake` provides:

```cmake
include(CompileShaders)
compile_metal_shaders(colorlooks_shaders
    "${CMAKE_SOURCE_DIR}/src/gpu/metal/shaders/PipelineKernels.metal")
```

For each file it runs `xcrun metal` → `.air` → `xcrun metallib` → `<name>.metallib` in the build
directory, and creates an `ALL` target `colorlooks_shaders_<name>`.

Manual equivalent:

```bash
cd src/gpu/metal/shaders
xcrun -sdk macosx metal -c PipelineKernels.metal -o /tmp/PipelineKernels.air
xcrun -sdk macosx metallib /tmp/PipelineKernels.air -o /tmp/PipelineKernels.metallib
```

> Pass only *entry* files (those with `kernel` functions) to `compile_metal_shaders`.
> `Common.metal` is a header-style include; compiling it alone yields an empty library.

## 5. Run the tools

```bash
# Prints the linked OpenColorIO version
./build/tools/ocio_inspector/ocio_inspector

# Validate every preset and pack against the schema
pip install -r tools/preset_validator/requirements.txt
python3 tools/preset_validator/validate.py assets/presets

# Zip a look pack
python3 tools/preset_packager/main.py assets/presets/packs/starter_pack starter_pack.zip
```

`ctest` runs the same check (`presets_match_schema`).

## 6. Editor setup

* `.editorconfig` — UTF-8, LF, 4-space indent, final newline.
* `.clang-format` — LLVM base, 4-space, 100 cols, Allman braces. Run
  `clang-format -i $(git ls-files '*.cpp' '*.hpp' '*.mm')`.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `No CMAKE_OBJCXX_COMPILER could be found` | Not on macOS / no Xcode CLT | `xcode-select --install` |
| `Could NOT find OpenColorIO` | Non-standard prefix | `-DCMAKE_PREFIX_PATH=...` |
| `does not contain a CMakeLists.txt file` (ocio_inspector) | Known issue 1 | Add the file above |
| `'OCIO' has not been declared` | Known issue 2 | Add namespace alias |
| `metal: error: cannot execute tool 'metal'` | Only CLT installed, no Metal toolchain | Install full Xcode or `xcodebuild -downloadComponent MetalToolchain` |
