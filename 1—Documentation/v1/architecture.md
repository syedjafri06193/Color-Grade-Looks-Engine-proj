# Architecture

## 1. Overview

The engine is a layered C++17 library with a thin host adapter (OFX) on top and a GPU backend
(Metal) underneath. Looks are pure data; the engine compiles a preset plus user parameters into a
**render graph** of nodes and dispatches it to the GPU, with a CPU reference path for validation.

```
┌──────────────────────────── Host application (Resolve, Nuke, …) ────────────────────────────┐
│                                       OFX API                                               │
└───────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                            │
┌───────────────────────────────── ofx/ ────▼──────────────────────────────────────────────────┐
│  OfxPlugin · ParamsBinding · HostUtils         (host params ⇄ engine Params, image fetch)   │
└───────────────┬──────────────────────────────────────────────────────┬──────────────────────┘
                │                                                      │
┌──── ui/ ──────▼─────────┐                         ┌──────── engine/ ─▼───────────────────────┐
│ ParamModel · LookSelector│ ───── selected look ──► │ LookEngine · RenderGraph · Nodes         │
└──────────────────────────┘                         │ Params · Frame · Cache · CPUFallback     │
                                                     └───┬───────────────┬──────────────┬──────┘
                                                         │               │              │
                                         ┌──── presets/ ─▼──┐   ┌── color/ ▼────┐  ┌── gpu/ ▼──────────┐
                                         │ Preset · PresetIO│   │ OCIOManager    │  │ GPUBackend        │
                                         │ Schema · Version │   │ ToneMap, Gamut │  │ Dispatch,KernelIDs│
                                         └──────────────────┘   │ Curves, Matrix │  │ metal/ backend    │
                                                                └────────────────┘  └───────────────────┘
                                                         │
                                         ┌──── common/ ──▼──────────────────────────────────────────┐
                                         │ Assert · Hash · Logging · Math · Span · Types · Version  │
                                         └──────────────────────────────────────────────────────────┘
```

Dependency rule: **arrows point downward only.** `common` depends on nothing; `color`, `presets` and
`gpu` depend on `common`; `engine` depends on those three; `ofx` and `ui` depend on `engine`. No
module may include a header from a layer above it.

## 2. Modules

| Module | Responsibility | Key types | Status |
|--------|---------------|-----------|--------|
| `common` | Assertions, logging, hashing, small math, spans, version info | `Hash64`, `Span<T>`, `Log` | Planned |
| `color` | OCIO config/processor management; CPU reference implementations of tone map, gamut compression, curves, matrices | `OCIOManager`, `Matrix3x3`, `ToneMapFilmicV1` | Planned |
| `presets` | Load, validate, migrate and serialise look presets | `Preset`, `PresetIO`, `PresetSchema`, `PresetVersioning` | Schema **implemented**; code planned |
| `engine` | Turn preset + params into a render graph; caching; CPU fallback | `LookEngine`, `RenderGraph`, `Node`, `Params`, `Frame`, `Cache` | Planned |
| `gpu` | Backend-agnostic dispatch interface + Metal implementation | `GPUBackend`, `KernelID`, `MetalBackend`, `MetalPipelineCache` | First kernel **implemented** |
| `ofx` | OpenFX plug-in entry points and parameter binding | `OfxPlugin`, `ParamsBinding` | Planned |
| `ui` | Host-agnostic parameter model and look browser | `ParamModel`, `LookSelector` | Planned |
| `tools` | Command-line utilities | `preset_validator`, `ocio_inspector`, `preset_packager` | Skeletons **implemented** |

## 3. Frame lifecycle

1. **Host calls render** with a source image, a time, and current parameter values.
2. `ParamsBinding` reads host parameters into an immutable `Params` struct (look ID + defaults
   overrides).
3. `LookEngine` fetches the `Preset` (from `Cache`, keyed by look ID + file hash).
4. `LookEngine` resolves colour management via `OCIOManager`: input, working and output colour
   spaces → two OCIO processors (in, out). Processors are cached by
   `hash(config, src, dst)`.
5. `RenderGraph` is (re)built only if the graph **topology** changed (stages enabled/disabled, curve
   presence). Pure value changes only update the uniform buffer.
6. `GPUBackend` uploads the frame, runs the input OCIO shader, the look kernels, the output OCIO
   shader, and writes to the destination.
7. On GPU failure or when `CPUFallback` is forced (tests, unsupported host), the same graph runs on
   the CPU reference path.

## 4. Render graph

Nodes correspond 1:1 to [pipeline stages](look-pipeline.md). Each node declares:

```cpp
struct NodeDesc {
    KernelID     kernel;        // which GPU function
    bool         enabled;       // from preset `enabled` flags
    bool         needsNeighbourhood; // halation/blur need full-texture access
    size_t       uniformOffset; // into the packed params buffer
};
```

**Fusion.** Consecutive per-pixel nodes (exposure → contrast → film matrix → saturation → tone map
→ gamut compress → grain) are fused into a single kernel to keep one read + one write per pixel.
Only halation, which needs a blur, breaks fusion into separate passes (threshold → separable blur ×2
→ composite). This gives at most **5 dispatches per frame** with halation, **1** without (plus OCIO).

## 5. Caching

| Cache | Key | Invalidation |
|-------|-----|--------------|
| Preset cache | look ID + content hash | File change / pack reload |
| OCIO processor cache | config hash + src + dst | Config change |
| Pipeline state cache (`MetalPipelineCache`) | `KernelID` + function constants | Never during session |
| Intermediate textures | size + pixel format | Resolution change |
| Curve LUTs (1D, 1024 entries) | hash of curve points | Preset change |

## 6. Threading model

* OFX hosts may call render concurrently on several threads. The engine is **re-entrant**: per-render
  state lives in a `RenderContext` on the stack; shared caches are guarded by a reader/writer lock.
* Metal command buffers are created per render call; a single `MTLCommandQueue` per device is shared.
* Preset loading happens off the render thread when the user selects a look; render uses the last
  fully loaded preset.

## 7. Error handling

* Invalid preset → rejected at load with a schema error; the previous look stays active.
* Missing OCIO colour space → log warning, fall back to `builtin` config (see
  [color-management.md](color-management.md#config-resolution)).
* GPU failure → retry once on CPU fallback, then pass the image through unchanged and report via
  host messaging. The engine **never** returns a black frame.

## 8. Target source tree

The full planned layout (from the original repository README):

```
src/
├─ common/   include/colorlooks/common/{Assert,Hash,Logging,Math,Span,Types,Version}.hpp
├─ color/    include/colorlooks/color/{ColorSpaces,OCIOManager,ToneMap,GamutCompress,Curves,Matrix3x3}.hpp
├─ presets/  include/colorlooks/presets/{Preset,PresetIO,PresetSchema,PresetVersioning}.hpp
│            schema/lookpreset.schema.json            ← present
├─ engine/   include/colorlooks/engine/{LookEngine,RenderGraph,Nodes,Params,Frame,Cache,CPUFallback}.hpp
├─ gpu/      include/colorlooks/gpu/{GPUBackend,KernelIDs,Dispatch}.hpp
│  ├─ metal/ include/…/{MetalBackend,MetalPipelineCache}.hpp, src/*.mm
│  │         shaders/{Common,ColorOps,ToneMap,Grain,GamutCompress,PipelineKernels}.metal
│  │                  ↑ Common & PipelineKernels present
│  └─ cpu/   reference kernels (optional)
├─ ofx/      {OfxPlugin,ParamsBinding,HostUtils}, OfxMain.cpp
└─ ui/       {ParamModel,LookSelector}
tests/       test_{ramps,gamut,tonemap,presets}.cpp, fixtures/{ramps,chart,skin}.exr
packaging/   ofx/{Info.plist,manifest.json,install_mac.sh,bundle_layout.md}, codesign/entitlements.plist
ci/          build_macos.yml, test.yml, release.yml
third_party/ ocio/, nlohmann_json/, stb/   (optional vendoring)
```

Headers live under `include/colorlooks/<module>/` so includes read
`#include <colorlooks/engine/LookEngine.hpp>`.
