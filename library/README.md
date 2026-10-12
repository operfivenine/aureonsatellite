# AURS / AURP library

[← Aureon](../README.md) · [Русский](README.ru.md)

Custom scenes and projections for Aureon. The catalog is being prepared; download links will be added with the packages.

| Package type | What it does | Import |
| --- | --- | --- |
| **AURS** | Adds a visual scene | Settings → Visuals → Import scene |
| **AURP** | Adds a projection | Settings → Tray |

## AURS scenes

Scene previews, descriptions, package versions and download links will appear here.

## AURP projections

Projection previews, descriptions, package versions and download links will appear here.

## For scene and projection authors

**[Authoring API reference (English)](api/README.md)** · **[Download the complete authoring kit](aureon-authoring-api-en.zip)**

Target: AURS standard library API **1.1** is preserved; the AURP Canvas library remains **1.0-foundation, experimental**.

| Resource | Open |
| --- | --- |
| First package | [Getting started](api/GETTING_STARTED.md) |
| Package contract and rendering profiles | [API reference](api/API_REFERENCE.md) · [Profiles](api/RENDERING_PROFILES.md) |
| Five technical starters | [Shader v2](api/examples/starters/shader_v2.aurs) · [Mesh](api/examples/starters/mesh.aurs) · [Hybrid](api/examples/starters/hybrid.aurs) · [Canvas](api/examples/starters/canvas.aurp) · [Surface](api/examples/starters/surface.aurp) |
| Packaging and validation | [Guide](api/VALIDATION_TROUBLESHOOTING.md) · [Package builder](api/tools/pack_theme.py) · [Validator](api/tools/validate_theme.py) |
| Checked baseline | [Compatibility](api/COMPATIBILITY.md) · [Evidence](api/BASELINE_AND_EVIDENCE.md) |

The starters are minimal technical examples. The kit also includes the shipped Holo Planet and Spectral Core packages. Validation needs a complete matching Aureon source tree and its dependencies.

## How to install

1. Download the **.aurs** or **.aurp** package.
2. Import an AURS scene in **Settings → Visuals → Import scene**, or an AURP projection in **Settings → Tray**.
3. Select the imported scene or projection in the corresponding settings.

[Scene import tutorial](../docs/tutorials/19_Import_AURS_Scene.md) · [Tray mode and projections](../docs/tutorials/20_Tray_Mini_Player.md)
