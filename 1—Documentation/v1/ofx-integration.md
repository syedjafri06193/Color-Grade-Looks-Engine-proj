# OFX Integration

Status: **Specified.** The `src/ofx/` module and `packaging/ofx/` are not yet in the repository.

## 1. Plug-in identity

| Property | Value |
|----------|-------|
| Identifier | `com.clientofaxioms.colorlooks` |
| Version | 1.0 |
| Label | Color Looks |
| Grouping | `client of AXIOMS` |
| Contexts | `Filter` (one source clip, one output) |
| Bundle | `ColorLooks.ofx.bundle` |

## 2. Supported features

| Feature | Setting |
|---------|---------|
| Pixel depths | `kOfxBitDepthHalf`, `kOfxBitDepthFloat` (8/16-bit int converted on entry) |
| Components | RGBA (RGB accepted, alpha treated as 1) |
| Tiles | Supported for CPU path; GPU path requests full frames when halation is enabled |
| Multi-resolution | Supported |
| Temporal access | Not required (frame index derived from render time) |
| Render thread safety | `kOfxImageEffectRenderFullySafe` |
| GPU render | OFX Metal render suite (`kOfxImageEffectPropMetalRenderSupported`) where host supports it |
| Colour management | OFX colour management suite where available, else parameters |

## 3. Parameters

| Param (script name) | Type | Range | Default | Maps to |
|---------------------|------|-------|---------|---------|
| `look` | Choice | installed looks | first look | preset `pack_id/id` |
| `exposure` | Double | −20 … 20 (UI −5 … 5) | preset | `exposure_stops` |
| `contrast` | Double | 0.1 … 4 (UI 0.5 … 2) | preset | `contrast` |
| `pivot` | Double | 0.0001 … 4 (UI 0.05 … 0.5) | preset | `pivot` |
| `saturation` | Double | 0 … 4 (UI 0 … 2) | preset | `saturation` |
| `warmCool` | Double | −1 … 1 | preset | `warm_cool` |
| `shadowTint` | RGB | −1 … 1 | preset | `shadow_tint` |
| `highlightTint` | RGB | −1 … 1 | preset | `highlight_tint` |
| `filmStrength` | Double | 0 … 1 | preset | `film_strength` |
| `grainAmount` | Double | 0 … 1 | preset | `grain_amount` |
| `halationAmount` | Double | 0 … 1 | preset | `halation_amount` |
| `inputSpace` / `outputSpace` | Choice | OCIO spaces | host / working | when host has no CM suite |
| `resetToLook` | Push button | — | — | reloads `defaults` from current look |
| `mix` | Double | 0 … 1 | 1 | blend with source in working space |

Behaviour when `look` changes: parameters are **reset to the new look's defaults** unless the user
has keyframes on them (keyframed params are left alone). This is the `resetToLook` logic.

## 4. Action flow

| OFX action | Engine call |
|-----------|-------------|
| `kOfxActionLoad` | Create shared `LookEngine`, scan pack search paths |
| `kOfxActionDescribe` | Declare plug-in properties |
| `kOfxImageEffectActionDescribeInContext` | Declare clips and parameters; populate `look` choice |
| `kOfxActionCreateInstance` | Allocate instance data (pointer to engine + cached `Params`) |
| `kOfxActionInstanceChanged` | If `look` changed → load preset, update param defaults |
| `kOfxImageEffectActionGetRegionsOfInterest` | Expand RoI by halation radius when enabled |
| `kOfxImageEffectActionIsIdentity` | Identity if `mix == 0` or all params at identity values |
| `kOfxImageEffectActionRender` | Build `Params` (+ `frameIndex = round(time)`) and call `LookEngine::render` |
| `kOfxActionUnload` | Destroy engine |

## 5. `HostUtils`

Encapsulates host quirks: Metal command-queue sharing, host colour-space name mapping (e.g. Resolve's
"Rec.709 Gamma 2.4" → OCIO names), message suite for user-visible errors, and detection of
premultiplied inputs.

## 6. Tested hosts (target matrix)

| Host | Version | GPU path | Notes |
|------|---------|----------|-------|
| DaVinci Resolve | 19+ | Metal | Primary target |
| Nuke | 15+ | CPU | OFX GPU not supported → CPU fallback |
| Natron | 2.5 | CPU | Open-source test host |
| Fusion Studio | 19+ | Metal | |

## 7. Host colour pipeline guidance

* In Resolve with *DaVinci YRGB Color Managed*, set the timeline working space to a scene-linear or
  wide-gamut log space and place the plug-in in the node graph; with `builtin_or_host`, the plug-in
  receives the timeline space.
* In Nuke, set `inputSpace`/`outputSpace` to match the project's working space (`scene_linear`).
