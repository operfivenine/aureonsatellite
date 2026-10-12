# Experimental AURS Mesh and Hybrid Contract

These profiles supply actual vertices to the host. They are separate from procedural
GLSL object/instance helpers and retain experimental status in the frozen host.
Plain mesh imports `aurs.geometry.experimental`; hybrid imports that library followed
by `aurs.standard`. Required base features are listed in RENDERING_PROFILES.md.

## Descriptor and binary layout

Both descriptors require libraries/environment/quality/camera/statistics. Hybrid
also requires hybrid and optionally adds textures/materials/signals/object_graph/
reflections. Root fields are closed. Environment requires fog_color RGB0–1,
fog_density0–0.1, ambient0–1, planet_fill0–1 and fill_origin XYZ. Statistics requires
integer buildings0–100,000 and objects0–1,000,000; it does not create geometry.

Exactly Low/Medium/High are authored. Each quality requires mesh path
`meshes/<quality>.bin` and batches. Resources: manifest.json, scene.json, preview.png,
shaders/main.vert, shaders/main.frag and three quality binaries. Hybrid adds
shaders/background.frag and declared textures. Extra/unused resources fail validation.

Vertex stride **40 bytes**: ten little-endian float32 values, ordered
**position XYZ, color RGBA, normal XYZ**. No index buffer, OBJ/FBX/GLTF importer
or skeleton format. Positions are finite and within ±30,000; colors0–2; normal
components within ±2. Batches partition the entire array in order: offset must
equal the running cursor, count is positive, triangles have count divisible by3,
lines by2. Max2,000,000 vertices and128 batches per quality.

Each batch requires offset/count/mode/model/lit/emission/fog/rim/style/point_size/
point_pixels/blend/depth/surface_gain/audio. Optional fields include animation,
material, bindings, template and gated blend_mode. Numeric bounds:
lit0–1; emission0–10; fog0–5; rim0–2; style0–7; point sizes0–16;
surface_gain0–4; depth−1000–1000. `audio` is five weights0–10 for RMS/low/mid/high/beat.
Blend is boolean; mode is triangles/lines/points. Use the
[mesh starter scene](examples/starters/mesh/scene.json) for a complete batch.

## Coordinates and transforms

Mesh world is **Z-up**, angles are degrees. JSON batch model is row-major16 numbers
with final row `[0,0,0,1]`; Qt converts it to GL storage. Graph local transform is
`T * Rx * Ry * Rz * S`; world transform is parentWorld*local. Only positive uniform
scale is supported for graph nodes; shear/nonuniform graph scale is excluded.
GLSL `AurObjectPose` uses +Y-up and radians. Convert conventions deliberately.

Vertex input locations0/1/2 are position/color/normal. The host supplies
modelView/projection and other documented render uniforms. The material program is
package-authored, GLSL330 Core, with bounded constant loops up to256 and128 KiB
per shader. Geometry shaders are validated by a different checker from fullscreen
fragment shaders; do not assume their permitted uniform/attribute syntax is identical.

## Camera

camera requires times/eyes/targets/fov/near/far/presets. There are4–128 keys, start
time0, time gaps at least0.05 s, final time at most3600 s. Eye and target sequences
must match times and each close exactly; each eye must differ sufficiently from
its target. Bounds: fov30–110 degrees, near0.05–5, far100–40,000.

Presets are up to12 lists `[id, nameEn, nameRu, routeTime]`. IDs are unique lowercase
identifiers and cannot use host `auto`. Optional camera.micro_motion0–1 requires
`scene.mesh_camera_settings.experimental.v1` in hybrid. Camera motion continues
on music pause; audio-derived gains decay independently. Test interpolated positions,
not only control keys: a closed Catmull–Rom route can overshoot the authored points.

## Hybrid background and shared signals

`hybrid.background` requires shader/libraries/quality/uniforms. Shader path is
shaders/background.frag; libraries exactly `["aurs.standard"]`. Background uses
the common scene time/audio/camera and explicitly writes gl_FragDepth. Its descriptor
must declare vec3 u_hyb_right/up/forward and vec2 u_hyb_clip, matching GLSL declarations;
host replaces their camera values. Separate camera/texture resources are not supported
in this background profile.

The minimal hybrid starter draws a distant sky at depth1. If you introduce a finite
surface, derive its depth from the same camera/projection as the geometry; leaving
depth1 would produce wrong intersections. Perspective-correct ray construction uses
the common camera basis, not an independently animated shader camera.

`scene.mesh_bindings.experimental.v1` enables up to32 shared signals of type
expression/envelope/integrator/gate/spring and batch bindings emission_add/surface_gain/
rim. Expression audio channels are **low, mid, high, energy, beat, presence**;
runtime playing/audio_mode/audio_active/reactive/paused/ambient are supported.
No FFT array, zones, flux, onset or audio.rms is exposed here. Legacy batch RMS
weight is a distinct interface. There is no second analyzer inside a package.

## Materials and textures

`scene.mesh_materials.experimental.v1`: up to24 material IDs; each has uniforms
mapping u_mat_* to expression/scalar/vector values. Max12 per material and12 distinct
names across the program; declared float/vec2/vec3/vec4 types must match. The package
defines how roughness/metal/activity affect shading; there is no implicit universal PBR
material schema. Material fields do not permit separate arbitrary GLSL files per ID.

Textures also require scene.textures2d.experimental.v1: max8 PNG/JPEG, axis≤2048,
file≤8 MiB, aggregate decoded+mip estimate≤64 MiB. Use srgb albedo/emissive and
linear normal/ORM. These are stricter than fullscreen shader texture ceilings.

## Object graph and instancing

Feature `scene.mesh_objects.experimental.v1`; object_graph contains templates/nodes/
lights, optionally lighting with its own feature. Up to24 template IDs map to batch
indices for every quality. A template batch is marked template:true, opaque static
triangles with identity model and rendered via instances. Every template/reference
must be valid and used; indices are unique per quality.

Up to2048 nodes require id/position/rotation/scale/tint/gain/distance. Optional parent
references a node, mesh references a template, animation is rotate or path; groups
omit mesh. The graph is acyclic, ancestry≤8, composed scale≤1000. Gain multiplies
through parents, tint is applied to the mesh node rather than inherited automatically.
Distance is a three-tier array. Culling applies to graph instances; baked batches
are not automatically sectorized. Entire distant nodes are skipped, without intermediate
distance-based mesh LOD switching.

Attributes3–6 form mat4 instanceModel;7 is vec4 instanceGain (tint RGB/gain).
Instance stride80 bytes: column-major matrix plus tint/gain. `u_mesh_instanced`
selects instanced processing. In that path modelView is view; otherwise view*batchModel.
Use these inputs only when instanced; preserve the noninstanced path.

`scene.mesh_animation.experimental.v1` adds rotate(axis/pivot/angle expression) and
closed Catmull–Rom path(points/duration/phase/orient) to supported batches. Node rotate
has no pivot. Paths:4–32 unique controls plus repeat of first; duration10–600 s,
phase0–1, orient boolean. Legacy drift/shuttle remains available. These operations
do not constitute skeletal animation, arbitrary per-field keyframes or physics.

## Lights and reflections

Lights require id/parent/local position/color/world radius/gain expression; max64.
Gain is independent of node gain. Host transforms lights to eye space and selects
at most1/2/4 point-light slots. Shader receives u_mesh_light_count and slot0–3
position/color/radius/gain; package GLSL determines material response. No shadow maps
or geometric light occlusion.

`scene.mesh_light_selection.experimental.v1` adds lighting={quality,fade_seconds,
hysteresis}; quality low/medium/high has sources/reach, nondecreasing by tier.
sources maxima1/2/4, reach20–400, fade0.15–2 s, hysteresis0.05–0.75; light priority
0.1–4. Slot identity changes after fade-out, then fades in; no extra-light crossfade.
Without this feature old nearest-source behavior remains.

`scene.mesh_reflections.experimental.v1` adds reflections={planes,quality}. Up to3
unit-normal plane equations [nx,ny,nz,d], max_distance20–1500; keep halfspace
dot(n,p)+d≥0. Quality passes maxima0/1/2 and nondecreasing; size integer128–1024,
multiple32, long-side cap. `scene.mesh_reflection_resolution.experimental.v1` raises
that cap to4096, not the number of passes. Buffers are RGBA8+depth/stencil, no MSAA.

Material shader uses u_reflection0/1 samplers, corresponding mat4 *_matrix, float
*_id (authored index+1,0 absent), and mat4 u_inverse_view. Vertex contract uses
u_mesh_model, u_reflection_pass, u_reflection_plane and gl_ClipDistance[0]. Host
provides mirrored cameras/FBO/clipping; package provides sampling/roughness/edge fade.
u_mat_reflector>0 batches are omitted from reflected geometry to prevent recursion.
FBO failure falls back to the material's environment approximation.

## Transparency and AA

`scene.mesh_transparency.experimental.v1` enables hybrid batch blend_mode alpha/
additive with blend:true. Opaque draws first; alpha batches sort by center back-to-front,
depth-tested without depth writes, SRC_ALPHA/ONE_MINUS_SRC_ALPHA. This is an
approximation, not order-independent transparency or refractive glass.

AA is host policy, without a new feature ID. Earlier RTX3070 host checks observed
Low FXAA, Medium2×MSAA+FXAA, High4×MSAA+FXAA; actual support depends on the context.
Reflections use FXAA without MSAA. Advanced can override resolution/AA/detail.
No temporal history, generic SSR, recursive mirrors, shadow maps or global HDR bloom
is introduced by this geometry profile. AURP glow is a separate projection operation.
