# Testing Strategy

Status: **Specified.** `tests/` and fixtures are not yet in the repository; `COLORLOOKS_BUILD_TESTS`
(default `ON`) already calls `enable_testing()`.

## 1. Goals

Every change must keep the output:

* **Free of banding** — smooth gradients stay smooth.
* **Free of hue skew** — colours don't drift in hue except where the look intends it.
* **Deterministic** — identical inputs give identical bits.
* **Safe** — no NaN, Inf or negative values ever reach the output.

## 2. Test layers

| Layer | Framework | What it covers | Runs on |
|-------|-----------|----------------|---------|
| Unit | Catch2 / GoogleTest via CTest | Maths functions (CPU reference), preset parsing, schema, versioning | Any macOS CI |
| Golden image | CTest + EXR compare | Full pipeline per built-in look on fixtures | macOS CI |
| GPU parity | CTest | Metal output vs CPU reference | Apple-silicon CI |
| Property / fuzz | Custom + random seeds | Random params within schema ranges never yield NaN/neg | Nightly |
| Schema | `check-jsonschema` | Every preset in `assets/` validates | Every PR |
| Performance | `bench_render` | Budgets in [performance.md](performance.md) | Apple-silicon CI |
| Host | Manual + scripted Natron | Plug-in loads, renders, params map | Pre-release |

## 3. Test files (planned)

| File | Contents |
|------|----------|
| `tests/test_ramps.cpp` | Grey and per-channel ramps through each stage; monotonicity; banding metric |
| `tests/test_gamut.cpp` | Gamut compression: in-gamut untouched below threshold, out-of-gamut pulled in, continuity at threshold |
| `tests/test_tonemap.cpp` | Mid-grey anchoring, monotonicity, ceiling, `preserve_hue` ratio preservation |
| `tests/test_presets.cpp` | Load built-ins, reject invalid fixtures, error paths, versioning |

## 4. Fixtures

| Fixture | Content | Purpose |
|---------|---------|---------|
| `fixtures/ramps.exr` | Horizontal grey ramp −10…+8 stops (log-spaced), plus R/G/B/C/M/Y ramps | Banding, monotonicity, highlight roll-off |
| `fixtures/chart.exr` | 24-patch colour chart in scene linear, plus out-of-gamut patches (AP0 primaries) | Hue stability, gamut compression |
| `fixtures/skin.exr` | Range of skin tones at −2…+2 stops | Skin hue preservation |
| `fixtures/presets/invalid_*.json` | One schema violation each | Validator error reporting |

EXR files: half-float, linear Rec.709, ZIP compression, ≤ 1 MB each. Store with Git LFS.

## 5. Acceptance criteria

| Test | Criterion |
|------|-----------|
| Identity preset | max abs diff vs input ≤ 1e-5 (float) / 1 half ULP |
| Mid-grey | 0.18 in → within ±1/3 stop at each built-in look's defaults |
| Monotonicity | Grey ramp output strictly non-decreasing per channel |
| Banding | Second difference of 10-bit encoded ramp has no spikes > 2 code values |
| Neutral axis | Grey stays neutral: `max(rgb)−min(rgb) < 1e-3·max(rgb)` (matrices with unit row sums) |
| Hue skew | Chart patches: hue change ≤ look's intended shift + 2° (CIELAB) |
| Gamut | Output inside working gamut (no negatives) for all chart + AP0 patches |
| Tone map | `preserve_hue: true` keeps channel ratios to 1e-4 |
| Determinism | Two renders of frame N: bit-identical; frames N and N+1 differ only in grain |
| GPU parity | max abs diff ≤ 1e-3 linear |
| Safety | 10 000 random param sets, random inputs incl. NaN/Inf/neg/1e6 → finite, ≥ 0 |
| Grain mean | Mean of grain over 256×256 flat patch within 0.5 % of patch value |

## 6. Golden images

* Stored as `tests/golden/<look>/<fixture>.exr`.
* Compared with tolerance (default 1e-3 abs, per-test overrides).
* Regenerate deliberately: `ctest -R golden -- --update-golden`, and review the diff images in the PR.

## 7. Running

```bash
cmake -S . -B build -DCOLORLOOKS_BUILD_TESTS=ON
cmake --build build -j
ctest --test-dir build --output-on-failure
ctest --test-dir build -L gpu      # GPU-only tests
ctest --test-dir build -L golden   # golden-image tests
```

Schema check for every preset (works today):

```bash
check-jsonschema --schemafile src/presets/schema/lookpreset.schema.json \
  $(git ls-files '*.json' | grep -v -e schema -e pack.json)
```
