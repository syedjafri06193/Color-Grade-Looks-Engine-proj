# Technical Specification

| | |
|---|---|
| **Product** | color-looks-mvp-v.1 (Color Looks Engine) |
| **Owner** | client of AXIOMS |
| **Version** | 1.0 (MVP) |
| **Language** | C++17, Objective-C++ (Metal glue), Metal Shading Language, Python 3 (tooling) |
| **Colour management** | OpenColorIO v2 |
| **GPU** | Apple Metal (macOS) |
| **Host API** | OpenFX (OFX) 1.4-compatible design |

## 1. Purpose

Provide film-emulation "looks" that can be applied in real time inside professional video hosts,
authored as portable data files rather than code, and rendered identically across machines.

## 2. Scope

**In scope (MVP)**
- Scene-referred look pipeline with 8 creative stages ([look-pipeline.md](look-pipeline.md))
- JSON preset format v1 with formal schema and look packs
- OCIO v2 input/output conversion with host, built-in or file configs
- Metal GPU implementation and CPU reference implementation
- OFX plug-in for macOS hosts
- CLI tools for validation, inspection and packaging

**Out of scope (MVP)**
- Windows/Linux, CUDA/OpenCL/Vulkan backends
- 3D LUT export, ACES AMF interchange
- Spatially-varying operations other than grain and halation (no windows, keys, tracking)
- In-plug-in look editor UI beyond parameter sliders and a look selector

## 3. Processing model

```
Input → OCIO (input → scene_linear) → Look Graph → OCIO (scene_linear → output) → Output
```

* **Working space:** OCIO role `scene_linear`. All look maths assumes linear light with values
  unbounded above (> 1.0 allowed) and floored at 0.
* **No display-referred maths inside the look graph.** The tone mapper is the only stage that
  compresses dynamic range; it outputs a bounded, mid-grey-anchored signal in the working
  primaries and leaves display encoding to the OCIO output transform.
* **Alpha** passes through untouched. Inputs are assumed **unpremultiplied**; if the host supplies
  premultiplied images the plug-in unpremultiplies before and premultiplies after.

## 4. Functional requirements

| ID | Requirement |
|----|-------------|
| FR-1 | Load any preset that validates against `lookpreset.schema.json` v1 |
| FR-2 | Reject invalid presets with a human-readable error identifying the JSON path |
| FR-3 | Expose `defaults` fields as user-adjustable parameters initialised from the preset |
| FR-4 | Apply stages in the fixed order of [look-pipeline.md](look-pipeline.md); disabled stages are identity |
| FR-5 | Honour `working_space` OCIO settings; `host_input` / `host_output` resolve to the host's colour spaces |
| FR-6 | Produce bit-identical output for identical (preset, params, input, frame index, device class) |
| FR-7 | Grain must be temporally varying by frame index yet reproducible |
| FR-8 | Load look packs and list contained looks with thumbnails |
| FR-9 | Fall back to CPU reference when the GPU path is unavailable |
| FR-10 | Never output NaN/Inf; never output negative values |

## 5. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | GPU time per 1080p frame (RGBA16F, all stages) | < 2 ms on M1-class |
| NFR-2 | GPU time per UHD frame | < 8 ms on M1-class |
| NFR-3 | Preset load + graph build | < 20 ms |
| NFR-4 | GPU vs CPU reference max abs error | ≤ 1e-3 (linear), ≤ 0.5 code value at 10-bit display |
| NFR-5 | Memory overhead beyond host buffers | ≤ 2 frames of RGBA16F |
| NFR-6 | Thread safety | Concurrent render calls safe |

## 6. Interfaces

### 6.1 Engine API (specified)

```cpp
namespace colorlooks::engine {

struct Params {
    std::string lookId;
    float exposureStops = 0.f, contrast = 1.f, pivot = 0.18f, saturation = 1.f;
    float warmCool = 0.f;
    std::array<float,3> shadowTint{}, highlightTint{};
    float filmStrength = 1.f, grainAmount = 0.f, halationAmount = 0.f;
    uint32_t frameIndex = 0;
};

struct FrameDesc {
    uint32_t width, height;
    PixelFormat format;          // RGBA16F, RGBA32F
    ColorSpaceRef input, output; // resolved OCIO names
};

class LookEngine {
public:
    explicit LookEngine(EngineConfig cfg);
    Status loadPreset(const std::filesystem::path&);   // or from memory
    Status loadPack(const std::filesystem::path&);
    std::vector<LookInfo> availableLooks() const;
    Status render(const Params&, const FrameDesc&, GPUImage src, GPUImage dst);
    Status renderCPU(const Params&, const FrameDesc&, ImageView src, ImageViewMut dst);
};
}
```

### 6.2 GPU uniform block (implemented, partial)

`ColorLooksParamsCommon` in `Common.metal` — see [gpu-metal-backend.md](gpu-metal-backend.md).

### 6.3 Preset format

JSON, `schema = "com.clientofaxioms.colorlooks.lookpreset"`, `schema_version = 1`.
Full reference: [preset-schema-reference.md](preset-schema-reference.md).

## 7. Parameter mapping

User-facing `defaults` combine with `pipeline` stage settings as follows:

| User param | Stage | Combination |
|------------|-------|-------------|
| `exposure_stops` | Exposure | gain = 2^E |
| `contrast`, `pivot` | Contrast | log2-domain slope about pivot |
| `film_strength` | Film matrix | effective mix = `film_matrix.strength × film_strength` |
| `saturation` | Saturation | chroma scale |
| `warm_cool`, `shadow_tint`, `highlight_tint` | Balance (inside saturation node) | see pipeline doc |
| `grain_amount` | Grain | amplitude; 0 disables |
| `halation_amount` | Halation | effective = `halation.strength × halation_amount`; also requires `halation.enabled` |

Rule: **`pipeline` describes the look's character; `defaults` are the user's dials on top.**

## 8. Determinism

* All random values are hash-based (PCG / integer hash of pixel coordinate + `frameIndex` + look
  seed), never `rand()` or time.
* No reductions with floating-point atomic order dependence.
* Fast-math must not reorder operations in ways that differ CPU vs GPU for tested tolerances.

## 9. Platform constraints

* macOS 13+, Apple silicon primary, Intel Macs with Metal 2.4 best-effort.
* Builds require `OBJCXX` support; CMake ≥ 3.22.
* Distribution as signed, notarised `.ofx.bundle` ([packaging-and-release.md](packaging-and-release.md)).
