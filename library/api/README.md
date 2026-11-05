# AURS API 1.1

**November 2026 · stable · Aureon 0.23.0 / v385**

[Русский](README.ru.md) · [AURS catalog](https://github.com/operfivenine/aureonsatellite/blob/main/library/README.md)

A public reference for authoring AURS scenes. Edition: 5 November 2026. API 1.1 is preserved and supported capabilities have stable status. Keep historical `experimental` spelling in technical identifiers.

Start with [your first package](docs/getting-started.md) and [authoring recommendations](docs/authoring-recommendations.md), then use the selected renderer’s features, channels and limits.

**[Download documentation ZIP](https://github.com/operfivenine/aureonsatellite/raw/refs/heads/main/library/Aureon-AURS-API-1.1-2026-11.zip)**

## Reference

- [Getting started](docs/getting-started.md)
- [Authoring recommendations](docs/authoring-recommendations.md)
- [Contract and renderer profiles](docs/contract.md)
- [Package fields and layout](docs/package.md)
- [Scene fields and response fragment](docs/scene-fields.md)
- [Standard GLSL library](docs/standard-library.md)
- [GLSL function signatures and structures](docs/glsl-symbols.md)
- [Audio and Reactive](docs/reactive.md)
- [Mesh / Hybrid](docs/mesh-hybrid.md)
- [Pass graph and postprocessing](docs/render-graph.md)
- [Cameras and clocks](docs/cameras.md)
- [Track palette and title atlas](docs/track-inputs.md)
- [Limits and quality](docs/limits-and-qa.md)
- [Platform portability](docs/portability.md)
- [Release checklist](docs/release-checklist.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Stability and historical identifiers](docs/stability.md)
- [November edition changes](docs/changes.md)

## Machine-readable references

- [Feature registry](reference/FEATURE_REGISTRY.json)
- [Uniforms and audio channels](reference/UNIFORMS_AND_CHANNELS.json)
- [Standard-library symbol index](reference/STANDARD_LIBRARY_SYMBOLS.json)
- [Edition metadata](API_RELEASE.json)

## Scope and verification

This package contains documentation and interface indexes. It does not contain player source, GLSL-library implementation, executable tools, artistic scene packages or their construction recipes. Installed Aureon supplies the standard library; importing AURS does not require an external Python installation. Every guide has an EN/RU switch.

Container acceptance, native GLSL compilation, performance and platform testing are separate stages. Supported profiles and the scope of stable status are described under [compatibility](docs/stability.md).
