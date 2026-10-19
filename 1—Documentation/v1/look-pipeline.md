# Look Pipeline

The look pipeline is a fixed sequence of stages. A preset cannot reorder stages; it can only
configure or disable them. A fixed order keeps looks predictable, lets the engine fuse stages into a
single GPU kernel, and makes presets comparable to each other.

## Stage order

| # | Stage | Domain | Preset block | User params | Status |
|---|-------|--------|--------------|-------------|--------|
| 1 | Input transform | OCIO | `working_space` | — | Specified |
| 2 | Exposure | linear | — | `exposure_stops` | **Implemented (GPU)** |
| 3 | Contrast | log2 about pivot | — | `contrast`, `pivot` | **Implemented (GPU)** |
| 4 | Film matrix | linear | `film_matrix` | `film_strength` | Specified |
| 5 | Saturation & balance | linear luma/chroma | — | `saturation`, `warm_cool`, `shadow_tint`, `highlight_tint` | Saturation **implemented**; balance specified |
| 6 | Curves | HSL-like | `curves` | — | Specified |
| 7 | Tone map | linear → [0,1) | `tone_map` | — | Specified |
| 8 | Gamut compression | linear | `gamut_compress` | — | Specified |
| 9 | Grain | linear | `grain` | `grain_amount` | Specified |
| 10 | Halation | linear, spatial | `halation` | `halation_amount` | Specified |
| 11 | Output transform | OCIO | `working_space` | — | Specified |

> Curves (stage 6) are defined in the preset schema but were missing from the original stage list;
> they sit between saturation and tone mapping so they act on scene colour before compression.

Notation: `c = (r, g, b)` linear working-space colour; `L(c) = w·c` luminance with weights `w`
(Rec.709 `(0.2126, 0.7152, 0.0722)` today; see [colour management](color-management.md#5-working-with-aces)).

---

## 1. Input transform

OCIO processor `input → working`. Followed by sanitisation:
`c = isfinite(c) ? c : 0`.

## 2. Exposure

```
c ← c · 2^exposure_stops
```

Range −20…+20 stops. A pure gain in linear light — physically equivalent to changing the exposure at
capture. 0 is identity.

## 3. Contrast (pivoted, log domain)

```
v     = log2(max(c, 1e-6))
p     = log2(max(pivot, 1e-6))
v     ← (v − p) · contrast + p
c     ← 2^v
```

* `pivot` (default 0.18, mid-grey) is the value left unchanged.
* `contrast` > 1 expands stops away from the pivot; < 1 compresses (flatter, "soft" looks).
* Working in log2 means contrast scales *stops*, so highlights are not clipped by the operation.
* Per-channel application means contrast also changes saturation slightly — this is film-like and
  intentional.
* Values ≤ 1e-6 are lifted to 1e-6 before the log; with contrast ≠ 1 true black becomes
  `2^((log2(1e-6) − p)·contrast + p)`, which is negligible (< 1e-5) for sane ranges.

## 4. Film matrix

Emulates the dye crosstalk of film stock.

```
M_eff = I + (M − I) · (film_matrix.strength · film_strength)
c     ← M_eff · c
```

* `matrix_3x3` is row-major: row 0 produces red. Element range ±4.
* Interpolating towards identity (rather than mixing outputs) keeps the operation linear and cheap.
* **Authoring rule:** keep each row summing to ≈ 1.0 (± 0.03) so neutrals stay neutral. The
  built-in `neutral_film` rows sum to 1.015 — a slight brightness lift (~+0.02 stop).
* Normalisation option (planned): `M_eff` rows rescaled so that `M_eff · (1,1,1) = (1,1,1)`.

## 5. Saturation and balance

### Saturation (implemented)

```
l = L(c)
c ← l + (c − l) · saturation
```

0 = monochrome, 1 = identity, up to 4. Luma-preserving by construction.

### Warm / cool (specified)

Temperature-style shift with luminance preserved:

```
k   = warm_cool · 0.1                      // ±10 % at the extremes
g   = (1 + k, 1, 1 − k)
c'  = c ⊙ g
c   ← c' · (L(c) / max(L(c'), 1e-6))
```

### Shadow / highlight tint (specified)

Split-toning in a log-luminance weighting so it behaves the same at any exposure:

```
s   = log2(max(l, 1e-6) / 0.18)            // stops from mid-grey
wS  = 1 − smoothstep(−4, 0, s)              // shadows weight
wH  = smoothstep(0, 4, s)                   // highlights weight
c   ← c ⊙ (1 + wS · shadow_tint + wH · highlight_tint)
```

Each tint component is in −1…1; typical values are ≤ 0.05.

Finally `c ← max(c, 0)` (the "safety floor" from the shader — floors only, never clamps highs).

## 6. Curves

Three optional 1D curves, each a list of up to 64 `[x, y]` points, interpolated with monotone cubic
(Fritsch–Carlson) and baked to a 1024-entry LUT.

| Curve | x | y | Identity |
|-------|---|---|----------|
| `hue_vs_sat` | hue in [0,1) (0 = red, wraps) | saturation multiplier | empty, or all y = 1 |
| `hue_vs_hue` | hue in [0,1) | hue offset in turns (−0.5…0.5) | empty, or all y = 0 |
| `luma_vs_sat` | `(log2(l/0.18) + 8) / 14` (−8…+6 stops → 0…1) | saturation multiplier | empty, or all y = 1 |

Hue curves are **periodic** (the point at x≈1 connects to x≈0). Hue is computed from the
chroma vector `c − l` in an opponent space so the operation remains luma-preserving.
`enabled: false` or all lists empty → stage skipped.

## 7. Tone map — `filmic_v1`

Compresses unbounded scene linear to a finite ceiling with a film-like toe and shoulder. With
mid-grey anchoring the ceiling is `0.18 / (s · f(0.18))` (≈ 2.2 with Neutral Film's toe 0.2 / shoulder 0.6), so the output
transform still receives some headroom; the final display mapping is OCIO's job.

Per-value curve on `x ≥ 0`, with `t = toe_strength`, `s = shoulder_strength`:

```
toe(x)      = x² / (x + t · 0.18)                 // t = 0 → identity
shoulder(x) = x / (1 + s · x)                     // s = 0 → identity, s = 1 → Reinhard
f(x)        = shoulder(toe(x))
f̂(x)        = f(x) · 0.18 / f(0.18)               // keep mid-grey anchored
```

* **`preserve_hue: true`** — apply the curve to a norm and scale the colour:
  `n = max(r,g,b); c ← c · f̂(n)/max(n,1e-6)`. Prevents bright saturated colours shifting toward
  yellow/cyan (the classic per-channel "notorious six" skew).
* **`preserve_hue: false`** — apply `f̂` per channel; brighter colours desaturate toward white, a
  more filmic but hue-shifting response.
* No clamp is applied after `f̂`; values stay non-negative and finite.

## 8. Gamut compression — `neutral_axis`

Pulls out-of-gamut and near-boundary colours toward the neutral axis, smoothly, without touching
colours well inside the gamut (based on the ACES Reference Gamut Compression idea).

```
a     = max(r, g, b)                       // achromatic
d_i   = (a − c_i) / |a|                     // distance per channel, 0 = neutral, >1 = out of gamut
thr   = 1 − 0.2 · strength                  // compression threshold (0.8 at strength 1)
lim   = 1.2
d_i'  = d_i                            if d_i < thr
      = thr + (d_i − thr) / (1 + ((d_i − thr)/(lim − thr))^p)^(1/p)  otherwise, p = 1.2
c_i   ← a − d_i' · |a|
```

`strength` 0 = off. Must run in float, never half (see [performance](performance.md#precision-policy)).

## 9. Grain — `procedural_v1`

Deterministic, luminance-dependent film grain.

```
seed       = hash(pixel.xy / size_px, frameIndex, look_hash)
n_mono     = gauss(seed)                          // N(0,1) via Box–Muller on 2 hashed uniforms
n_rgb      = gauss3(seed)
n          = mix(n_mono, n_rgb, colorful)
l          = L(c)  (post-tone-map, display-ish range)
envelope   = (1 + shadows_boost · (1 − l)) · (1 − highlights_rolloff · l²)
c          ← c + c · n · grain_amount · 0.1 · envelope
```

* `size` (0–2) controls grain cell size: `size_px = 1 + 3·size` pixels at UHD, scaled by
  resolution so the look matches across formats.
* Multiplicative application keeps black black.
* `grain_amount = 0` or `enabled = false` → stage skipped.

## 10. Halation

Red-orange glow around bright highlights, from light scattering off film base.

```
h  = max(c − threshold, 0)                        // highlights above threshold (scene linear)
h  = gaussianBlur(h, radius_px)                   // separable, two passes
h  = h ⊙ (1.0, 0.35, 0.10)                         // halation tint
c  ← c + h · halation.strength · halation_amount
```

* `radius` in pixels at UHD, scaled by resolution; up to 200.
* Requires `enabled: true` **and** `halation_amount > 0`.
* Placed after tone mapping in the original design; it therefore uses tone-mapped values. Since
  `threshold` in presets is > 1 (1.1–1.2), implementations should evaluate the threshold on the
  **pre-tone-map** buffer, which the engine keeps for this purpose.

## 11. Output transform

OCIO processor `working → output`, then alpha restored.

---

## Identity configuration

Every stage is identity when:

| Stage | Identity values |
|-------|----------------|
| Exposure | `exposure_stops = 0` |
| Contrast | `contrast = 1` |
| Film matrix | `enabled = false` or `strength·film_strength = 0` or `M = I` |
| Saturation/balance | `saturation = 1`, `warm_cool = 0`, tints `[0,0,0]` |
| Curves | `enabled = false` |
| Tone map | toe and shoulder 0 (identity curve); there is no `enabled` flag |
| Gamut | `enabled = false` or `strength = 0` |
| Grain | `enabled = false` or `grain_amount = 0` |
| Halation | `enabled = false` or `halation_amount = 0` |

Tests rely on this table: an "identity preset" must reproduce the input within float tolerance.
