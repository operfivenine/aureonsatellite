# AURS Fullscreen Shader Contract

**Frozen-host limitation:** the basic v1 descriptor compiles, but store.prepare
fails during metadata construction because definition.behavior is None. The
reproduction is in validation/known_issues/. This edition preserves the host and
documents v1 for contract reference; use the validated v2 starter for new imports.

## Descriptor and resources

Required resource: `shaders/main.frag`. The descriptor requires
`"shader": "shaders/main.frag"`; optional v1 fields are quality/signals/uniforms.
V2 additionally allows behavior/libraries/textures/lights.
Only supported resources may be packed; see native `store.py` for its allowlist.

The shader starts with `#version 330 core` followed by a newline and contains
`void main()`. Only that source directive is permitted: no `#define`, `#include`
or extension directives. Host-injected quality defines and imported library bodies
are inserted after the version line. Do not paste the resolved library into your
shader when using an import, or redefine the reserved `aur_` function namespace.

`while`, `do`, `discard`, arbitrary layout/storage/image/atomic operations and
unapproved samplers are rejected in this single-pass profile. V2 permits declared
`sampler2D u_tex_*` resources. GLSL validation constrains syntax; it is not a GPU
execution sandbox or cost proof.

## Quality

`quality` maps low/medium/high to `{ "defines": {"STEPS": 16} }`.
Missing tiers use empty defines, and define names must match across all tiers.
Names are uppercase identifiers, max 48 chars, without `GL_` prefix or `__`.
Values are integers 1–25,600; at most 1600 defines per tier. The host supplies
`AUR_QUALITY_TIER` and `AUR_QUALITY_LEVEL` separately.

V2 optionally adds extreme when manifest requires
`scene.quality_extreme.experimental.v1`. V1 supports only three tiers.
Loops must satisfy the profile's bounded canonical-loop rules; literal/declared
bounds and nested-work budgets are checked. Read scene_v2_schema.loop_limits for
the structural v2 rules. A larger numeric define cannot bypass those checks.
Use fewer iterations/noise octaves/shadow samples at lower tiers; a menu entry alone
does not reduce shader work.

## Standard library

V2 import: `"libraries": ["aurs.standard"]`, with manifest required
`scene.standard_library.v1`. API **1.1 revision 10** is unchanged. Compatibility
`core.*` and opt-in `experimental.*` modules are listed with dependencies and exact
overloads in [GLSL_CATALOG.md](GLSL_CATALOG.md). Host resolves dependencies.
Stable additions include object_motion, attachments, instances and trails_lod.
These are procedural GLSL helpers; they do not allocate mesh objects or GPU passes.

## Uniforms

Common reserved uniforms: `u_resolution` vec2, `u_mouse` vec2, `u_time` float,
`u_zones0/1` vec4 and `u_audio_<channel>` float. Declare only what is used, with
the exact type. Shader v2 adds `u_bands[32]`, `u_peaks[32]`, `u_events[N]` vec4,
modes/variant/playing and standard camera uniforms. The event array must cover
configured slots and stay within the host limit. User arrays are not supported.

Custom uniform names start with `u_` and must avoid reserved names, `u_audio_`
and `u_lightcfg_`. Descriptor values are expressions or lists of 2–4 expressions:

```json
{
 "u_pulse": "signal.bass",
 "u_tint": {"type": "vec3", "source": [0.2, 0.1, "0.5 + signal.bass*0.3"]}
}
```

Declare `uniform float u_pulse; uniform vec3 u_tint;` in GLSL. The descriptor's
optional explicit type must agree with component count. Every custom uniform and
texture sampler must be declared; unknown, duplicate or mismatched declarations fail.
Custom float/vec2/vec3/vec4 are allowed; custom int/bool/mat uniforms are not.

## Behavior and cameras

V2 `signals` support bounded temporal primitives and presets; behavior supports
events, modes, clock and cameras. [AUDIO_ANIMATION.md](AUDIO_ANIMATION.md) describes
the audio boundary. Camera config fields: shots, mode_shots, transition, impulses,
driver, easing, loop, limits, presets, manual. Shots require expression-valued xyz
position/target; defaults: fov45, roll0, hold6 seconds; distance is optional.
Drivers: mode/static/timeline; easing: linear/smoothstep/smootherstep/sine.
Presets/manual require their respective experimental feature IDs.

Common camera uniforms include `u_camera_pos/target` vec3, fov/roll/distance/shot/
shot_age floats and `u_camera_impulse` vec4. A shader may instead keep its own
camera. A declared host rig must actually be used to compute rays; merely declaring
its uniforms does not alter shader-authored geometry.

## Textures and lights

Texture import requires `scene.textures2d.experimental.v1`. Keys are sampler names
`u_tex_*`; values have source/color_space and optional wrap/filter/mipmaps:

```json
{
 "u_tex_stone": {
 "source": "textures/stone.png", "color_space": "srgb",
 "wrap": "repeat", "filter": "linear", "mipmaps": true
 }
}
```

PNG/JPG/JPEG content must match its extension. color_space: srgb/linear; wrap:
repeat/clamp; filter: linear/nearest. Albedo/emissive usually use srgb, normal/ORM
linear. ORM convention is R=AO, G=roughness, B=metallic. Normal-map green convention
must match your shader; normal maps do not change silhouette or geometric depth.

Opt-in helpers: texture_materials, normal_mapping, triplanar, normal_filtering,
scene_lights. Corresponding feature IDs are in API_INDEX.json. JSON `lights` requires
`scene.lights_config.experimental.v1`; host creates reserved parameter uniforms
and accessors. The shader remains responsible for intersections, visibility and
material response. This is not a universal shadow renderer or global bloom pass.

## Limits

Fragment 12.5 MiB; 4800 uniforms including generated light parameters; 400 textures;
400 configured lights. Shader texture axis ceiling 204,800 and aggregate decoded
texture/mipmap ceiling 3200 MiB are native validation limits, not recommended sizes.
Mesh/hybrid has much stricter texture limits. All native values are in API_INDEX.json.
Preview decoding follows a separate cache path.
