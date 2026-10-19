# Look Packs

A **look pack** groups presets for distribution and display as a collection.

## Layout

```
starter_pack/
├─ pack.json
├─ looks/
│  ├─ neutral_film.json
│  └─ soft_contrast_film.json
└─ thumbnails/            (optional)
   ├─ neutral_film.png
   └─ soft_contrast_film.png
```

## `pack.json`

```json
{
  "schema": "com.clientofaxioms.colorlooks.lookpack",
  "schema_version": 1,
  "pack_id": "starter_pack",
  "name": "Starter Pack",
  "author": "client of AXIOMS",
  "license": "builtin",
  "looks": ["looks/neutral_film.json", "looks/soft_contrast_film.json"]
}
```

| Key | Type | Req. | Description |
|-----|------|:----:|-------------|
| `schema` | string | ✔ | const `com.clientofaxioms.colorlooks.lookpack` |
| `schema_version` | integer | ✔ | 1 |
| `pack_id` | string | ✔ | `^[a-z0-9_\-]{3,64}$`; unique across installed packs |
| `name` | string | ✔ | Display name |
| `author` | string | | |
| `license` | string | | `builtin`, or an identifier/URL for the licence terms |
| `looks` | string[] | ✔ | Paths relative to `pack.json`, forward slashes, no `..` |

> There is no JSON Schema file for packs yet. A `lookpack.schema.json` mirroring the table above is
> planned (see [project-status.md](project-status.md)).

## Loading rules

1. Resolve each entry of `looks` relative to the pack directory. Reject absolute paths and `..`.
2. Validate each look; an invalid look is skipped and reported — the rest of the pack still loads.
3. A look's identity is `pack_id/id`. Duplicate `id`s inside a pack are an error.
4. Thumbnails: `thumbnails/<id>.png` inside the pack, else `assets/thumbnails/<id>.png`, else a
   generated swatch.

## Search paths (specified)

| Order | Location |
|-------|----------|
| 1 | Built-in packs inside the plug-in bundle `Contents/Resources/packs/` |
| 2 | `~/Library/Application Support/ColorLooks/packs/` |
| 3 | `/Library/Application Support/ColorLooks/packs/` |
| 4 | Directories in env var `COLORLOOKS_PACK_PATH` (colon-separated) |

## Packaging

```bash
python3 tools/preset_packager/main.py assets/presets/packs/starter_pack starter_pack.zip
```

See [tools.md](tools.md#preset_packager) for current behaviour and its caveats (archive path prefix).

## Current repository state

`assets/presets/packs/starter_pack/pack.json` references `looks/neutral_film.json` and
`looks/soft_contrast_film.json`, but the `looks/` directory does not exist yet, and
`soft_contrast_film.json` sits at the repository root instead of `assets/presets/builtin/`. To fix:

```bash
git mv soft_contrast_film.json assets/presets/builtin/
mkdir -p assets/presets/packs/starter_pack/looks
cp assets/presets/builtin/{neutral_film,soft_contrast_film}.json assets/presets/packs/starter_pack/looks/
```

(Or use symlinks / have the build copy them, to avoid two sources of truth.)
