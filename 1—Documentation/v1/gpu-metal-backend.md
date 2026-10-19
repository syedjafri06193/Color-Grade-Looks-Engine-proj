# Metal GPU Backend

## 1. Files

| File | Status | Contents |
|------|--------|----------|
| `src/gpu/metal/shaders/Common.metal` | **Implemented** | Uniform struct, `luminance`, `safeLog2`, `safeExp2` |
| `src/gpu/metal/shaders/PipelineKernels.metal` | **Implemented** | `ColorLooks_BasicStage` kernel |
| `ColorOps.metal`, `ToneMap.metal`, `GamutCompress.metal`, `Grain.metal` | Planned | Stage functions |
| `MetalBackend.mm`, `MetalPipelineCache.mm`, `MetalUtils.mm` | Planned | Device, queues, pipeline states |
| `cmake/CompileShaders.cmake` | **Implemented** | `.metal → .air → .metallib` |

## 2. Uniform block — `ColorLooksParamsCommon`

```metal
struct ColorLooksParamsCommon {
    uint  width, height;
    float exposureStops;   // [-20..+20]
    float contrast;        // [0.1..4.0]
    float pivot;           // linear pivot, e.g. 0.18
    float saturation;      // [0..4]
    float filmStrength;    // [0..1]
    float grainAmount;     // [0..1]
    uint  frameIndex;      // temporal seed for grain
};
```

Bound at `[[buffer(0)]]`. Size 36 bytes. The C++ mirror **must** match layout exactly; add a
`static_assert(sizeof(ParamsCommon) == 36)` and keep members 4-byte scalars (no `float3`, which is
16-byte aligned in MSL and silently changes layout).

### Planned extension

```metal
struct ColorLooksParams {
    ColorLooksParamsCommon common;
    float  warmCool;
    float  shadowTint[3];
    float  highlightTint[3];
    float  lumaWeights[3];        // from OCIO config
    float  filmMatrix[9];         // M_eff, row-major, pre-mixed on CPU
    float  toe, shoulder, toneNorm; // toneNorm = 0.18 / f(0.18), precomputed on CPU
    uint   preserveHue;
    float  gamutStrength;
    float  grainSize, grainColorful, grainShadows, grainHighlights;
    uint   lookHash;
    uint   stageMask;              // bit per stage, lets one kernel skip disabled stages
};
```

Values that are constant per frame (`M_eff`, `toneNorm`) are computed on the CPU once, not per pixel.

## 3. The `ColorLooks_BasicStage` kernel

```metal
kernel void ColorLooks_BasicStage(
    texture2d<half, access::read>  inTex  [[texture(0)]],
    texture2d<half, access::write> outTex [[texture(1)]],
    constant ColorLooksParamsCommon& p    [[buffer(0)]],
    uint2 gid                             [[thread_position_in_grid]])
```

Per pixel:

1. Bounds check against `p.width`/`p.height` (grid may be rounded up to threadgroup size).
2. Read `half4`, promote to `float`.
3. Exposure: `rgb *= exp2(exposureStops)`.
4. Contrast in log2 about `pivot`.
5. Saturation around Rec.709 luminance.
6. Floor at 0 (no high clamp).
7. Write `half4` with original alpha.

### Notes and recommended changes

* `exp2(p.exposureStops)` and `log2(pivot)` are uniform — compute once on the CPU and pass in.
* `half` storage caps at 65504 and has ~3 significant digits; fine for RGBA16F host buffers, but the
  final kernel should be templated on `half`/`float` texture types for RGBA32F hosts.
* `safeExp2` doesn't guard against overflow; with contrast 4 and bright inputs, `exp2` can exceed
  `half` max → `inf` on write. Clamp to 65504 before writing half (`min(rgb, 65504.0)`).
* Comment says "don't hard clamp highs in final pipeline" — keep it that way.

## 4. Dispatch

```objc
MTLSize tg = MTLSizeMake(pso.threadExecutionWidth,
                         pso.maxTotalThreadsPerThreadgroup / pso.threadExecutionWidth, 1);
MTLSize grid = MTLSizeMake(width, height, 1);
[enc dispatchThreads:grid threadsPerThreadgroup:tg];  // non-uniform threadgroups (Apple GPUs)
```

On GPUs without non-uniform threadgroup support, use `dispatchThreadgroups` with
`ceil(width/tg.width)` — the in-kernel bounds check handles the overhang.

## 5. Planned pass structure

| Pass | Kernel | Reads | Writes |
|------|--------|-------|--------|
| 1 | OCIO input (generated MSL) + fused look stages 2–9 | src | `work` (RGBA16F) + `preTM` (if halation) |
| 2 | `Halation_Threshold` | `preTM` | `h0` (half res) |
| 3 | `Blur_H` | `h0` | `h1` |
| 4 | `Blur_V` | `h1` | `h0` |
| 5 | `Halation_Composite` + OCIO output | `work`, `h0` | dst |

Without halation: passes 1 and 5 fuse to a single kernel. Halation runs at half resolution with a
separable Gaussian (kernel weights in a `constant` buffer, radius ≤ 64 taps; larger radii use a
downsample pyramid).

## 6. Function constants

Stages are toggled with Metal **function constants** so disabled stages compile out:

```metal
constant bool kFilmMatrix [[function_constant(0)]];
constant bool kCurves     [[function_constant(1)]];
constant bool kGamut      [[function_constant(2)]];
constant bool kGrain      [[function_constant(3)]];
constant bool kPreserveHue[[function_constant(4)]];
```

`MetalPipelineCache` keys pipeline states by `(KernelID, constant bitmask)` — at most 32 variants for
the fused kernel; built lazily, cached for the session, optionally pre-warmed on plug-in load.

## 7. Curves on the GPU

Each curve is baked on the CPU to a 1024-entry `float` LUT, uploaded as a `texture1d_array<float>`
(3 layers), sampled with linear filtering and `address::repeat` for the hue curves, `clamp_to_edge`
for luma.

## 8. Grain hashing

Use an integer hash (e.g. PCG3D) on `(gid / cell, frameIndex ^ lookHash)` → uniform floats →
Box–Muller. Integer maths gives identical results across GPU families, satisfying
determinism (FR-6). Avoid `fract(sin(x)·43758)` hashes — they differ by GPU and precision.

## 9. Memory and synchronisation

* Textures: `MTLStorageModePrivate` for intermediates; host-supplied buffers per OFX host (Metal
  textures when the host supports OFX Metal render, otherwise CPU buffers uploaded via a shared
  staging buffer).
* One command buffer per render; `waitUntilCompleted` only when the host requires synchronous return.
* Intermediates are pooled by `(width, height, format)`.

## 10. Debugging

* Xcode GPU Frame Capture: set `MTL_CAPTURE_ENABLED=1` and trigger via `MTLCaptureManager`.
* `MTL_SHADER_VALIDATION=1` catches out-of-bounds texture access.
* Compile with `-gline-tables-only -frecord-sources` in Debug for shader source in captures.
