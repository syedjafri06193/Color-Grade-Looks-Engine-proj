# Preset Schema Reference (v1)

Authoritative source: [`src/presets/schema/lookpreset.schema.json`](../src/presets/schema/lookpreset.schema.json)
(JSON Schema draft 2020-12, `$id` `https://schemas.clientofaxioms/color-looks/lookpreset.schema.json`).

Every object in the schema sets `additionalProperties: false` — **unknown keys are errors**,
including typos such as `"saturaton"`.

## Top level

| Key | Type | Req. | Constraint | Description |
|-----|------|:----:|-----------|-------------|
| `schema` | string | ✔ | const `com.clientofaxioms.colorlooks.lookpreset` | Document type marker |
| `schema_version` | integer | ✔ | 1…1 | Format version |
| `id` | string | ✔ | `^[a-z0-9_\-]{3,64}$` | Stable machine ID; also thumbnail file name |
| `name` | string | ✔ | 1–128 chars | Display name |
| `description` | string | | ≤ 2048 | One-line description shown in UI |
| `author` | string | | ≤ 128 | |
| `created_utc` | string | | RFC 3339 date-time | e.g. `2026-02-15T00:00:00Z` |
| `tags` | string[] | | ≤ 32 items, each ≤ 48 | Free-form search tags |
| `defaults` | object | ✔ | see below | User-facing parameter defaults |
| `pipeline` | object | ✔ | see below | Look definition |

## `defaults`

| Key | Type | Req. | Range | Default meaning | Stage |
|-----|------|:----:|-------|----------------|-------|
| `exposure_stops` | number | ✔ | −20 … 20 | 0 = unchanged | Exposure |
| `contrast` | number | ✔ | 0.1 … 4 | 1 = unchanged | Contrast |
| `pivot` | number | ✔ | 0.0001 … 4 | 0.18 = mid-grey | Contrast |
| `saturation` | number | ✔ | 0 … 4 | 1 = unchanged | Saturation |
| `warm_cool` | number | | −1 … 1 | 0 = neutral; + warm | Balance |
| `shadow_tint` | rgbSigned | | each −1 … 1 | `[0,0,0]` | Balance |
| `highlight_tint` | rgbSigned | | each −1 … 1 | `[0,0,0]` | Balance |
| `film_strength` | number | ✔ | 0 … 1 | multiplies `film_matrix.strength` | Film matrix |
| `grain_amount` | number | ✔ | 0 … 1 | 0 = no grain | Grain |
| `halation_amount` | number | ✔ | 0 … 1 | multiplies `halation.strength` | Halation |

## `pipeline`

All seven blocks are **required**, even when disabled.

### `working_space`

| Key | Type | Req. | Values |
|-----|------|:----:|--------|
| `type` | string | ✔ | `"ocio"` |
| `config` | string | ✔ | `builtin_or_host` \| `builtin` \| `path` |
| `config_path` | string | if `config == "path"` | Path to `.ocio` |
| `input` | string | ✔ | OCIO name/role or `host_input` |
| `working` | string | ✔ | OCIO name/role (normally `scene_linear`) |
| `output` | string | ✔ | OCIO name/role or `host_output` |

### `tone_map`

| Key | Type | Req. | Range |
|-----|------|:----:|-------|
| `model` | string | ✔ | `filmic_v1` |
| `shoulder_strength` | number | ✔ | 0 … 1 |
| `toe_strength` | number | ✔ | 0 … 1 |
| `preserve_hue` | boolean | ✔ | |

### `film_matrix`

| Key | Type | Req. | Range |
|-----|------|:----:|-------|
| `enabled` | boolean | ✔ | |
| `matrix_3x3` | number[3][3] | ✔ | each −4 … 4, row-major |
| `strength` | number | ✔ | 0 … 1 |

### `curves`

| Key | Type | Req. | Constraint |
|-----|------|:----:|-----------|
| `enabled` | boolean | ✔ | |
| `hue_vs_sat` | curvePoint[] | ✔ | ≤ 64 |
| `hue_vs_hue` | curvePoint[] | ✔ | ≤ 64 |
| `luma_vs_sat` | curvePoint[] | ✔ | ≤ 64 |

`curvePoint` = `[x, y]`, two numbers. Semantics in [look-pipeline.md §6](look-pipeline.md#6-curves).

> Schema note: `curvePoint` uses the array form of `items` (`"items": [ {...}, {...} ]`), which is the
> draft-04…2019 tuple syntax. Under draft 2020-12 the tuple keyword is `prefixItems`; strict
> validators ignore array-form `items`. It still works because `minItems`/`maxItems` = 2, but numbers
> are not type-checked. Fix in schema v1.1: `"prefixItems": [{"type":"number"},{"type":"number"}], "items": false`.

### `gamut_compress`

| Key | Type | Req. | Range |
|-----|------|:----:|-------|
| `enabled` | boolean | ✔ | |
| `method` | string | ✔ | `neutral_axis` |
| `strength` | number | ✔ | 0 … 1 |

### `grain`

| Key | Type | Req. | Range |
|-----|------|:----:|-------|
| `enabled` | boolean | ✔ | |
| `model` | string | ✔ | `procedural_v1` |
| `size` | number | ✔ | 0 … 2 |
| `colorful` | number | ✔ | 0 … 1 |
| `shadows_boost` | number | ✔ | 0 … 1 |
| `highlights_rolloff` | number | ✔ | 0 … 1 |

### `halation`

| Key | Type | Req. | Range |
|-----|------|:----:|-------|
| `enabled` | boolean | ✔ | |
| `threshold` | number | ✔ | 0 … 32 (scene linear) |
| `radius` | number | ✔ | 0 … 200 (px at UHD) |
| `strength` | number | ✔ | 0 … 1 |

## Minimal valid preset (identity look)

```json
{
  "schema": "com.clientofaxioms.colorlooks.lookpreset",
  "schema_version": 1,
  "id": "identity",
  "name": "Identity",
  "defaults": {
    "exposure_stops": 0, "contrast": 1, "pivot": 0.18, "saturation": 1,
    "film_strength": 0, "grain_amount": 0, "halation_amount": 0
  },
  "pipeline": {
    "working_space": { "type": "ocio", "config": "builtin_or_host",
                       "input": "host_input", "working": "scene_linear", "output": "host_output" },
    "tone_map": { "model": "filmic_v1", "shoulder_strength": 0, "toe_strength": 0, "preserve_hue": true },
    "film_matrix": { "enabled": false, "matrix_3x3": [[1,0,0],[0,1,0],[0,0,1]], "strength": 0 },
    "curves": { "enabled": false, "hue_vs_sat": [], "hue_vs_hue": [], "luma_vs_sat": [] },
    "gamut_compress": { "enabled": false, "method": "neutral_axis", "strength": 0 },
    "grain": { "enabled": false, "model": "procedural_v1", "size": 0, "colorful": 0,
               "shadows_boost": 0, "highlights_rolloff": 0 },
    "halation": { "enabled": false, "threshold": 1, "radius": 0, "strength": 0 }
  }
}
```

## Versioning

* `schema_version` is bumped only for **breaking** changes (removed/renamed keys, changed semantics).
* `PresetVersioning` migrates older presets in memory on load; files on disk are never rewritten
  silently.
* Adding an optional key with an identity default is non-breaking but still requires a schema update,
  because `additionalProperties: false` would otherwise reject it.
* New enum values (e.g. `tone_map.model: "filmic_v2"`) are additive; older engines reject the preset
  with a clear "unsupported model" error.

## Error messages (specified)

The validator reports JSON Pointer paths:

```
neutral_film.json: /defaults/contrast: 5.0 is greater than maximum 4.0
neutral_film.json: /pipeline/grain: unexpected property "intensity"
neutral_film.json: /pipeline/working_space: "config_path" is required when config = "path"
```
