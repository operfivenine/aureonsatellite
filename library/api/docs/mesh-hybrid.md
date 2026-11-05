# Mesh and Hybrid

[← API](../README.md) · [Русский](mesh-hybrid.ru.md)

Base Mesh and Hybrid are separate profiles. Hybrid requires `scene.mesh.experimental.v1`, `scene.hybrid_mesh.experimental.v1` and `scene.standard_library.v1`. Geometry, camera, environment, quality and batch ranges are validated before GL resources are created. Material, binding, animation and object-graph extensions require their own features.

Supported options include material textures, UV/tangent layouts, albedo/normal/ORM, sampler bindings, transparency, reflections, light selection and bounded volumetric fog. UV/tangent changes vertex layout only with the appropriate explicit feature. Older mesh assets keep their earlier layout. Samplers use `u_tex_` names; resource types and occupied names cannot be substituted or reused freely.

GPU procedural instances use `gl_InstanceID` and the declared instance count. Opt-in volleys use 2–16 history slots and 3–256 lanes; instances must equal slots × lanes. Lifetime is 1–60 seconds; the minimum interval is at least 0.25 seconds. Allocate enough slots for all live volleys. Declare `u_mesh_volleys` in the vertex shader with the exact slot count. Independent texture samplers are forbidden in the current vertex profile.

Patterns/signals can control interval and pattern selection through expressions. A signal-driven emitter requires mesh bindings. `travel_clock` requires both `scene.mesh_volley_clock.experimental.v1` and `scene.mesh_volley_signals.experimental.v1`; movement age is measured against the integrated author clock. It is independent of `camera.clock` and does not change audio DSP.

See the [feature registry](../reference/FEATURE_REGISTRY.json) for resource budgets.
