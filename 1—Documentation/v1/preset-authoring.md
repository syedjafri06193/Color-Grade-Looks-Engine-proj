# Preset Authoring Guide

This guide walks through designing a look, writing it as a preset, and getting it ready to ship.

## Rules every preset must follow

1. **Validate against the schema** — `schema_version: 1`, no unknown keys.
2. **Stay deterministic** — no field may depend on time, machine or randomness; grain is seeded.
3. **Avoid extreme matrix values** — keep film-matrix rows summing to 1.0 ± 0.03 and off-diagonals
   within ±0.15 unless there is a deliberate creative reason.
4. **Keep highlights stable** — a +4-stop ramp must roll off smoothly with no hue flip, banding or
   inversion (see the checklist below).
5. **Mid-grey sanity** — at default parameters, 18 % grey should land within ±1/3 stop of 18 %
   before the output transform.

## 1. Start from a base

Copy `assets/presets/builtin/neutral_film.json` and change `id`, `name`, `description`, `tags`,
`created_utc`. The `id` must be unique across all installed packs and match `^[a-z0-9_\-]{3,64}$`.

## 2. Design order

Work through the stages in pipeline order; each one assumes the previous is settled.

| Step | Adjust | Aim |
|------|--------|-----|
| 1 | `contrast`, `pivot` | Overall density and punch. Film bases: 0.9–1.15 |
| 2 | `film_matrix` | Colour separation / stock character |
| 3 | `saturation`, `warm_cool` | Overall chroma and temperature |
| 4 | `shadow_tint`, `highlight_tint` | Split tone (teal/orange, cool shadows, etc.) |
| 5 | `curves` | Targeted hue fixes (skin, foliage, skies) |
| 6 | `tone_map` | Toe (shadow density) and shoulder (highlight roll-off) |
| 7 | `gamut_compress` | Clean up saturated lights and neons |
| 8 | `grain`, `halation` | Texture last — evaluate at 100 % zoom and in motion |

## 3. Parameter cookbook

**Contrast**
- `contrast: 0.92` + `toe_strength: 0.4` → lifted, "soft" shadows (see *Soft Contrast Film*).
- `contrast: 1.15` + `toe_strength: 0.1` → punchy, deep blacks.
- Move `pivot` up (e.g. 0.25) to darken mids with contrast > 1, down to brighten them.

**Film matrix** — row *i* gives the output of channel *i* as a mix of input R, G, B:

```
[[ 1.00, 0.02, 0.01 ],   R_out = 1.00 R + 0.02 G + 0.01 B
 [ 0.01, 1.00, 0.02 ],   G_out = …
 [ 0.02, 0.01, 1.00 ]]   B_out = …
```

Positive off-diagonals desaturate (channels share signal); negative ones increase separation.
To keep neutrals neutral, subtract the off-diagonal sum from the diagonal:
`[0.97, 0.02, 0.01]` sums to 1.00.

**Split tone**
- Classic teal/orange: `shadow_tint: [-0.02, 0.0, 0.02]`, `highlight_tint: [0.03, 0.01, -0.02]`.
- Keep tint components within ±0.05; above that, skin goes off quickly.

**Tone map**
- `shoulder_strength` 0.5–0.7 is a natural film roll-off; 1.0 is very compressed.
- Use `preserve_hue: true` for most looks. Use `false` only for a deliberately "bleached" highlight
  response.

**Curves examples**

```json
"curves": {
  "enabled": true,
  "hue_vs_sat": [[0.0, 1.0], [0.33, 0.85], [0.6, 1.1], [1.0, 1.0]],
  "hue_vs_hue": [[0.05, 0.0], [0.10, -0.01], [0.15, 0.0]],
  "luma_vs_sat": [[0.0, 0.7], [0.55, 1.0], [1.0, 0.8]]
}
```
— slight green desaturation, richer blues, skin nudged toward red, desaturated deep shadows and
extreme highlights.

**Grain**
- `size` 0.3–0.6 for 35 mm feel, > 1.0 for 16 mm.
- `colorful` 0.2–0.4 is realistic; 0 is monochrome grain.
- Always set `grain.enabled: true` and control visibility with `defaults.grain_amount`.

**Halation**
- `threshold` 1.0–1.5 (scene linear: 1.0 is ~2.5 stops over mid-grey).
- `radius` 4–12 px at UHD.
- Ship with `halation.enabled: true` and `halation_amount` low (0.05–0.2) so users can raise it.

## 4. Worked example — the two built-ins

| Field | Neutral Film | Soft Contrast Film | Effect of the difference |
|-------|-------------|--------------------|--------------------------|
| `contrast` | 1.05 | 0.92 | Soft is flatter |
| `saturation` | 1.0 | 0.95 | Soft slightly muted |
| `warm_cool` | 0 | 0.05 | Soft slightly warm |
| tints | none | cool shadows (B−), cool-ish highlights | subtle split tone |
| `toe_strength` | 0.2 | 0.4 | Soft has denser toe… combined with low contrast reads as "lifted" |
| `shoulder_strength` | 0.6 | 0.55 | Soft rolls off a touch later |
| matrix off-diagonals | 0.005–0.01 | 0.01–0.02 | Soft has more crosstalk |
| `film_strength` × `strength` | 0.8 × 0.7 = 0.56 | 0.9 × 0.85 = 0.765 | |
| grain | 0.15, size 0.45 | 0.25, size 0.55 | Soft is grainier |
| halation | off | on, 0.05 × 0.15 | Faint glow |
| `curves` | enabled, empty | disabled | Equivalent (both identity) |

## 5. Validation & review checklist

Before submitting a preset:

- [ ] Validates: `check-jsonschema --schemafile src/presets/schema/lookpreset.schema.json my_look.json`
- [ ] `id` unique; file name is `<id>.json`
- [ ] Thumbnail `assets/thumbnails/<id>.png` (512×512, sRGB, no alpha)
- [ ] Grey ramp (−8 … +6 stops): monotonic, no banding, neutral stays neutral (a*, b* < 1 ΔE)
- [ ] Macbeth chart: no patch flips hue by more than ~10°
- [ ] Skin fixture: skin hue within the skin-tone line ±5°
- [ ] Highlights +4 stops on saturated colours: smooth roll-off, no clipping artefacts
- [ ] Grain checked in motion at 100 % (no crawling patterns, no frame-to-frame flicker of mean level)
- [ ] All `defaults` set to 0 / identity reproduces the "look character only" render without errors
- [ ] Added to a pack's `looks` list if it is to ship in a pack ([look-packs.md](look-packs.md))

## 6. Common mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Matrix rows sum ≫ 1 | Look brightens / shifts neutrals | Normalise rows |
| Large tints | Skin turns green/magenta | Keep within ±0.05 |
| `halation.enabled: false` but `halation_amount > 0` | Slider does nothing | Enable the block |
| Typo in key | Validation error `unexpected property` | Check against reference |
| `config: "path"` without `config_path` | Validation error | Add path or use `builtin_or_host` |
| Saturation boosted before gamut compress disabled | Neon edges clip | Keep gamut compression on (0.4–0.6) |
