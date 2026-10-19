# Glossary

| Term | Meaning |
|------|---------|
| **ACES / ACEScg** | Academy Color Encoding System; ACEScg is its linear working space with AP1 primaries |
| **AP0 / AP1** | ACES primaries sets; AP0 encloses all visible colours, AP1 is closer to real-world gamuts |
| **Achromatic axis / neutral axis** | Line of greys where R = G = B |
| **Chroma** | Colourfulness; here `c − L(c)`, the colour minus its luminance |
| **Crosstalk** | Film dyes responding to light meant for other layers; modelled by the film matrix |
| **Display-referred** | Values encoded for a display (0–1, gamma-encoded) |
| **EOTF** | Electro-optical transfer function — display encoding curve (sRGB, PQ, gamma 2.4) |
| **Film matrix** | 3×3 matrix mixing RGB channels to emulate stock colour character |
| **Function constant** | Metal compile-time specialisation value used to strip disabled code |
| **Gamut compression** | Smoothly pulling out-of-gamut colours inside the gamut boundary |
| **Golden image** | Approved reference render used for regression tests |
| **Grain** | Film's random silver/dye particle texture |
| **Halation** | Red-orange glow around highlights from light reflecting off the film base |
| **Half / RGBA16F** | 16-bit IEEE floating point; max 65504 |
| **Look** | A creative colour transform; in this project, a preset |
| **Look pack** | Collection of looks with a `pack.json` manifest |
| **Luminance (L)** | Weighted sum of linear RGB approximating perceived brightness |
| **Metal / MSL** | Apple's GPU API / Metal Shading Language |
| **metallib** | Compiled Metal shader library |
| **Mid-grey** | 18 % reflectance, linear 0.18 — the usual exposure anchor |
| **OCIO** | OpenColorIO, the industry colour-management library |
| **OFX** | OpenFX, the open plug-in API for image-effect hosts |
| **Pivot** | Value left unchanged by the contrast operation |
| **Preset** | JSON document describing one look |
| **PSO** | Pipeline state object — compiled GPU program with its configuration |
| **Role** | OCIO alias such as `scene_linear` resolved by the config to a colour space |
| **Scene-referred** | Values proportional to scene light, unbounded above |
| **Shoulder / toe** | Highlight and shadow regions of a tone curve |
| **Split toning** | Tinting shadows and highlights different hues |
| **Stop** | Doubling (or halving) of light; `log2` units |
| **Tone mapping** | Compressing scene dynamic range for display |
| **Working space** | Colour space in which the look graph operates |
