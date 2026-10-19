# Documentation Index

Welcome to the Color Looks Engine documentation. Pick a path based on what you need.

## By role

**Colourist / look designer**
1. [Look pipeline](look-pipeline.md) — what each stage does to the image
2. [Preset authoring](preset-authoring.md) — building a look step by step
3. [Preset schema reference](preset-schema-reference.md) — every field and its range
4. [Look packs](look-packs.md) — bundling looks for distribution

**Engine / GPU developer**
1. [Getting started](getting-started.md)
2. [Architecture](architecture.md)
3. [Technical specification](technical-spec.md)
4. [Colour management](color-management.md)
5. [Metal GPU backend](gpu-metal-backend.md)
6. [Performance](performance.md)
7. [Testing](testing.md)

**Integrator / release engineer**
1. [OFX integration](ofx-integration.md)
2. [Packaging & release](packaging-and-release.md)
3. [Tools](tools.md)

**Everyone**
- [Project status & roadmap](project-status.md)
- [Contributing](contributing.md)
- [Glossary](glossary.md)
- [Changelog](../CHANGELOG.md)

## Conventions used in these docs

| Marker | Meaning |
|--------|---------|
| **Implemented** | Exists in the repository today and behaves as described |
| **Specified** | Design is fixed (schema, interface, or contract) but code is not yet written |
| **Planned** | Direction agreed; details may change |

Maths uses linear-light RGB unless stated. `log2` is base-2 logarithm. Vectors are column vectors;
a 3×3 matrix `M` applied to colour `c` is `M·c` with **row-major** storage (row *i* produces output
channel *i*).
