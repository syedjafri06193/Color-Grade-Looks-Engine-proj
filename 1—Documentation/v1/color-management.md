# Colour Management

The engine uses **OpenColorIO v2** for every conversion into and out of the look graph. The look
graph itself performs no colour-space conversions — it only operates in the working space.

## 1. Principles

1. **Scene-referred processing.** Creative operations run on linear scene light. Values above 1.0
   are legitimate and preserved until tone mapping, which is what keeps highlight roll-off smooth.
2. **One working space.** Every stage sees the OCIO role `scene_linear`.
3. **No display maths in the graph.** Gamma, display EOTFs and viewing transforms belong to the OCIO
   output transform, never to look stages.
4. **Defer to the host.** By default the plug-in uses the host's OCIO config and colour spaces so the
   look sits correctly inside an existing ACES or custom pipeline.

## 2. The `working_space` block

```json
"working_space": {
  "type": "ocio",
  "config": "builtin_or_host",
  "input": "host_input",
  "working": "scene_linear",
  "output": "host_output"
}
```

| Field | Values | Meaning |
|-------|--------|---------|
| `type` | `"ocio"` | Only OCIO is supported |
| `config` | `builtin_or_host` | Use the host's config if it provides one, else the bundled config |
| | `builtin` | Always use `assets/ocio/config.ocio` |
| | `path` | Load the config at `config_path` (required in that case) |
| `config_path` | string | Absolute path or path relative to the preset/pack |
| `input` | colour space or role name, or `host_input` | Space of the incoming image |
| `working` | colour space or role name | Space the look graph runs in (normally `scene_linear`) |
| `output` | colour space or role name, or `host_output` | Space of the outgoing image |

`host_input` / `host_output` are **tokens**, not OCIO names. The OFX layer replaces them with the
clip's colour space as reported by the host (OFX colour-management suite where available, otherwise a
plug-in parameter defaulting to the working space, i.e. identity).

## 3. Config resolution

```
config == "path"            → load config_path        → fail? → builtin
config == "builtin"         → bundled config
config == "builtin_or_host" → host config available?  → yes: host config
                                                      → no:  bundled config
```

After a config is chosen each name (`input`, `working`, `output`) is resolved via
`config->getColorSpace(name)`; role names resolve through the config's roles. An unresolved name logs
a warning and the stage becomes identity (input/output) so the image is never corrupted.

## 4. The bundled config (`assets/ocio/config.ocio`)

A deliberately minimal OCIO v2 config for override/testing workflows:

| Colour space | Family | Definition |
|--------------|--------|-----------|
| `lin_rec709` | linear | Identity to reference. Rec.709 primaries, D65, linear |
| `srgb_display` | display | to_reference: power 2.2; from_reference: power 0.4545 |

Roles: `scene_linear` and `reference` → `lin_rec709`.

### Limitations and recommended improvements

* **2.2 power ≠ sRGB.** The true sRGB transfer has a linear toe; use
  `!<ExponentWithLinearTransform> {gamma: 2.4, offset: 0.055}` for exact sRGB.
* **Inverse by explicit 0.4545** introduces rounding (1/2.2 = 0.454545…). Prefer one transform with
  `direction: inverse` for exact round-trips.
* **Missing `displays`/`views`/`active_displays`.** OCIO v2 configs normally declare at least one
  display and view; some tools reject or warn on configs without them. Add:

```yaml
displays:
  sRGB:
    - !<View> {name: Standard, colorspace: srgb_display}
active_displays: [sRGB]
active_views: [Standard]
```

* **Missing common roles** (`default`, `data`, `color_picking`, `color_timing`, `compositing_log`).
  Add at least `default: lin_rec709` and a `data` raw space.
* Run `ociocheck --iconfig assets/ocio/config.ocio` after editing.

## 5. Working with ACES

For ACES hosts, set the host to ACEScg as its working space. With `builtin_or_host` the look runs in
**ACEScg (AP1)** linear. Two consequences:

* `luminance()` in `Common.metal` uses **Rec.709** weights. In AP1 use
  `(0.2722287, 0.6740818, 0.0536895)`. The engine should pass luma weights as a uniform derived from
  `OCIO::Config::getDefaultLumaCoefs()` (planned).
* Film matrices authored in Rec.709 primaries should be converted into the working primaries
  (`M_working = P⁻¹ · M_709 · P`) at load time. Presets v1 assume matrices are authored in the
  working space; v2 will add a `matrix_space` field.

## 6. GPU path for OCIO

`OCIOManager` builds processors and obtains `GPUProcessor`s, then uses OCIO's
`GpuShaderDesc` with `LANGUAGE_MSL_2_0` to generate Metal code for the input and output transforms.
Any LUT textures OCIO requests are uploaded once per processor and cached. The generated functions
are compiled into the pipeline alongside the look kernels.

CPU path: `CPUProcessor::apply` on packed RGBA float images.

## 7. Numeric safety

* Inputs may contain negatives (from wide-gamut cameras) — the look pipeline floors to 0 after
  saturation and gamut compression; log operations use `max(x, 1e-6)`.
* NaN/Inf inputs are sanitised to 0 at pipeline entry.
* Output transforms receive values in [0, ∞); clamping, if needed, is the output space's job.

## 8. Checklist for new colour spaces

1. Add to a config, run `ociocheck`.
2. Verify round-trip `A → working → A` error < 1e-5 on a ramp.
3. Render the 18 % grey patch: output must equal the space's encoding of 0.18 with
   exposure 0 and all stages disabled.
