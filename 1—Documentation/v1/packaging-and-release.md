# Packaging & Release

Status: **Specified.** `packaging/` and `ci/` are not yet in the repository.

## 1. Bundle layout (`packaging/ofx/bundle_layout.md`)

```
ColorLooks.ofx.bundle/
└─ Contents/
   ├─ Info.plist
   ├─ MacOS/
   │  └─ ColorLooks.ofx            # universal binary: arm64 + x86_64
   └─ Resources/
      ├─ manifest.json
      ├─ shaders/ColorLooks.metallib
      ├─ ocio/config.ocio
      ├─ schema/lookpreset.schema.json
      ├─ packs/starter_pack/…
      └─ thumbnails/*.png
```

Install location: `/Library/OFX/Plugins/ColorLooks.ofx.bundle`.

## 2. `Info.plist` (key fields)

| Key | Value |
|-----|-------|
| `CFBundleIdentifier` | `com.clientofaxioms.colorlooks` |
| `CFBundleExecutable` | `ColorLooks.ofx` |
| `CFBundlePackageType` | `BNDL` |
| `CFBundleShortVersionString` | `1.0.0` |
| `LSMinimumSystemVersion` | `13.0` |

## 3. `manifest.json`

```json
{
  "product": "color-looks",
  "version": "1.0.0",
  "build": "<git sha>",
  "schema_versions": { "lookpreset": [1], "lookpack": [1] },
  "files": { "MacOS/ColorLooks.ofx": "sha256:…", "Resources/shaders/ColorLooks.metallib": "sha256:…" }
}
```

## 4. Installer (`install_mac.sh`)

1. Require admin (`sudo`).
2. Remove previous `/Library/OFX/Plugins/ColorLooks.ofx.bundle`.
3. Copy bundle, `chown -R root:wheel`, `chmod -R 755`.
4. Create `~/Library/Application Support/ColorLooks/packs/` for user packs.

Distribute as a signed `.pkg` built with `pkgbuild` + `productbuild`.

## 5. Code signing & notarisation

```bash
codesign --force --timestamp --options runtime \
  --entitlements packaging/codesign/entitlements.plist \
  --sign "Developer ID Application: <Team>" \
  ColorLooks.ofx.bundle

productsign --sign "Developer ID Installer: <Team>" ColorLooks-unsigned.pkg ColorLooks.pkg
xcrun notarytool submit ColorLooks.pkg --keychain-profile AC_NOTARY --wait
xcrun stapler staple ColorLooks.pkg
```

Entitlements: none beyond the hardened runtime are expected for an in-process plug-in. Do **not**
add `com.apple.security.cs.disable-library-validation` unless a host requires it.

## 6. CI pipelines (`ci/`)

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `build_macos.yml` | push, PR | Install OCIO (brew, cached) → configure → build (Release, universal) → upload artefacts |
| `test.yml` | push, PR | Build Debug → `ctest` → schema-validate all presets → clang-format check |
| `release.yml` | tag `v*` | Build → test → bundle → sign → pkg → notarise → staple → GitHub Release with checksums |

Secrets: `APPLE_DEVELOPER_ID_P12`, `APPLE_P12_PASSWORD`, `NOTARY_KEY_ID`, `NOTARY_ISSUER`,
`NOTARY_KEY_P8`. Note the files live in `ci/`; GitHub Actions only runs workflows from
`.github/workflows/`, so either move them there or reference them via `workflow_call`.

## 7. Versioning

Semantic versioning: `MAJOR.MINOR.PATCH`.

| Change | Bump |
|--------|------|
| Preset format break / OFX param removal | MAJOR |
| New stage, new param, new built-in look | MINOR |
| Bug fix, perf improvement with identical output | PATCH |
| Bug fix that changes pixels | MINOR, called out in changelog |

## 8. Release checklist

- [ ] All CI green, performance within budget
- [ ] Golden images reviewed; intended changes documented
- [ ] `CHANGELOG.md` updated
- [ ] Version in `CMakeLists.txt` `project(... VERSION)` and `Info.plist` match the tag
- [ ] Bundle signed, pkg notarised and stapled
- [ ] Installed and smoke-tested in Resolve and Nuke on a clean machine
