# Contributing

This is a proprietary project of client of AXIOMS. Contributions are by invitation; external
redistribution of code or presets is prohibited (see `LICENSE`).

## Workflow

1. Branch from `main`: `feature/<topic>`, `fix/<topic>`, `look/<look_id>`.
2. Keep PRs focused; one stage or one look per PR where possible.
3. PR description: what changed, why, before/after images for anything that changes pixels.
4. CI must pass (build, tests, schema, format).
5. One approving review; two for changes to `src/color/`, the schema, or shaders.

## Code style

Enforced by `.clang-format` and `.editorconfig`:

* C++17, 4-space indent, 100-column limit, **Allman** braces, namespace contents indented.
* No single-line function bodies.
* Sorted includes.
* Files: `PascalCase.hpp/.cpp/.mm/.metal`; namespaces `colorlooks::<module>`.
* Public headers under `src/<module>/include/colorlooks/<module>/`.

```bash
clang-format -i $(git ls-files '*.cpp' '*.hpp' '*.mm')
```

Metal shaders follow the same layout manually (clang-format handles MSL reasonably well too).

## Engineering rules

* **Colour maths needs a CPU reference first**, then the GPU version, with a parity test.
* No `rand()`, time, or thread-ID in pixel maths.
* No allocation on the render path.
* Uniform structs: 4-byte scalars only, `static_assert` sizes on the C++ side.
* Any change to output pixels updates golden images in the same PR.
* Schema changes: update `lookpreset.schema.json`, [preset-schema-reference.md](preset-schema-reference.md),
  `PresetVersioning`, and add an invalid-fixture test.

## Commit messages

```
<area>: <imperative summary>

<why, not what>
```

Areas: `engine`, `color`, `gpu`, `presets`, `ofx`, `ui`, `tools`, `looks`, `docs`, `build`, `ci`.

## Documentation

Update the relevant `1—Documentation/` page in the same PR as the behaviour change, and move items in
[project-status.md](project-status.md) from *Planned* to *Implemented*.
