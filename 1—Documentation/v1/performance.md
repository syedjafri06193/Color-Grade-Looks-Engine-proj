# Performance

## 1. Budgets

GPU time per frame, all stages enabled, RGBA16F in/out, measured as command-buffer GPU time
(`MTLCommandBuffer.gpuEndTime − gpuStartTime`):

| Resolution | Pixels | Budget (M-series) | Per-pixel budget |
|-----------|--------|-------------------|------------------|
| 1920×1080 | 2.07 M | **< 2 ms** | ~0.97 ns |
| 3840×2160 | 8.29 M | **< 8 ms** | ~0.96 ns |
| 4096×2160 (DCI 4K) | 8.85 M | < 8.5 ms | |
| 7680×4320 (8K) | 33.2 M | < 32 ms (best effort) | |

Additional budgets:

| Item | Budget |
|------|--------|
| Preset load + validation | < 10 ms |
| Render graph rebuild (topology change) | < 20 ms incl. PSO lookup (PSOs pre-warmed) |
| Parameter change (value only) | uniform update, no rebuild |
| First-use PSO compile | < 150 ms, done at plug-in load, not first render |

## 2. Why these budgets are achievable

A UHD RGBA16F frame is 66 MB. Reading and writing once is 133 MB; at ~68 GB/s (M1) that's ~2 ms of
bandwidth. The fused per-pixel kernel is bandwidth-bound, leaving most of the 8 ms for halation's
blur passes (run at half resolution: ¼ the pixels) and OCIO.

## 3. Precision policy

| Data | Precision | Reason |
|------|-----------|--------|
| Texture storage (in/out/intermediate) | `half` (RGBA16F) | Bandwidth; matches host buffers |
| Exposure, contrast, saturation, matrix, balance | `float` ALU, `half` OK where proven | Simple ops |
| Log/exp in contrast | `float` | `half` log2 has visible banding in shadows |
| **Tone map** | **`float`** | Divisions and power near 0 and at the shoulder |
| **Gamut compression** | **`float`** | Distance ratios divide by `max(rgb)` |
| Grain hash | `uint` | Determinism |
| Halation blur | `half` | Low-frequency, tolerant |
| Curve LUTs | `float` texture | Smooth interpolation |

"Use half precision where safe" means: storage and blur, yes; any stage with log/exp/division, no.

## 4. Optimisation rules

1. **Fuse** per-pixel stages into one kernel; one read and one write per pixel.
2. **Hoist uniforms**: compute `exp2(exposure)`, `log2(pivot)`, `M_eff`, tone-map normalisation on
   the CPU.
3. **Function constants** to remove disabled stages instead of runtime `if`s.
4. **No dynamic allocation** in render; pool intermediates.
5. **Halation at half resolution**, separable blur, ≤ 64 taps; pyramid for larger radii.
6. **Avoid `waitUntilCompleted`** unless the host needs synchronous results.
7. Use `dispatchThreads` with the PSO's `threadExecutionWidth`.

## 5. Measuring

* Unit benchmark (planned): `bench_render --size 3840x2160 --look neutral_film --frames 200`,
  reports p50/p95/max GPU time; discard first 10 frames (warm-up).
* Xcode Instruments → *Metal System Trace* for per-encoder timing.
* GPU counters: Xcode frame capture → *Performance* to check whether kernels are ALU- or
  bandwidth-limited.

## 6. Regression policy

CI on Apple-silicon runners records p95 GPU time for 1080p and UHD. A > 10 % regression versus the
`main` baseline fails the performance job. Budgets above are hard limits for release.
