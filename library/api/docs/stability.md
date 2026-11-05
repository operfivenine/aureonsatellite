# Stability and compatibility

[← API](../README.md) · [Русский](stability.ru.md)

**AURS API 1.1 · 5 November 2026 edition · stable.** The November registry targets Aureon 0.23.0 / v385. Supported Mesh/Hybrid, material, geometry, pass-graph, audio-texture, camera and track-input capabilities have stable status.

`experimental` in existing identifiers such as `scene.hybrid_mesh.experimental.v1`, `scene.post_geometry.experimental.v1` and `aurs.geometry.experimental` is historical spelling. Do not remove it or invent stable aliases: the host rejects unknown required IDs. Stable status does not imply every field combination works on every GPU.

Profile versions v1/v2, `format_version=1`, `engine.api_major=1` and `aurs.standard=1.1` are unchanged. Existing packages do not need rebuilding solely for this documentation edition. Schemas, limits and implementation remain unchanged. Host Python modules are not an external Python SDK.

The registry also contains AURP projection metadata. This guide covers AURS scenes; do not apply a projection contract to a scene package.

