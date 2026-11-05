# Contract and compatibility

[← API](../README.md) · [Русский](contract.ru.md)

The manifest uses `format="aureon.theme"`, `package_type="scene"`, `format_version=1`, `engine.api_major=1` and `entry="scene.json"`. Aureon 0.23.0 does not mean API 2.0. The renderer profile, Reactive engine version and `aurs.standard` version are independent.

| Renderer | Scope |
| --- | --- |
| `scene.fullscreen_frag.v1` | Legacy single fragment shader and limited signal graph |
| `scene.fullscreen_frag.v2` | GLSL, expanded signals, camera, textures and an optional pass graph |
| `scene.mesh.experimental.v1` | Base geometry, camera and quality |
| `scene.hybrid_mesh.experimental.v1` | Geometry with a shared procedural background, materials, animation and opt-in passes |

`features.required` and `capabilities.required` are checked before installation. Unknown required identifiers are rejected. An optional declaration cannot create an implementation that the host lacks. For newer features, `engine.min_aureon="0.23.0"` may be appropriate, but the required feature declarations remain necessary.

The [feature registry](../reference/FEATURE_REGISTRY.json) lists manifest-level support per renderer. A supported feature does not remove dependencies between scene fields.

Packages contain declarative JSON/GLSL and permitted assets. They cannot execute Python, access the network, use arbitrary paths, control the player/window, or manage the OpenGL lifecycle. Existing packages without new opt-ins retain their earlier execution paths.

The November edition changes the documented stability status, not the technical identifiers, package format or implementation. See [stability](stability.md).
