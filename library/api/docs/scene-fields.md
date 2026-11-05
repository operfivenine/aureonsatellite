# Scene fields: selected profiles

[← API](../README.md) · [Русский](scene-fields.ru.md)

This is a field guide for common entry points, not a complete JSON Schema. Optional objects still have their own required fields and feature dependencies.

## Fullscreen v1/v2

| Field | Meaning |
| --- | --- |
| `shader` | Required; exactly `shaders/main.frag` |
| `quality` | Preset objects containing `defines`; v1 supports low/medium/high, v2 also permits declared extreme |
| `signals` | Named bounded signal descriptors |
| `uniforms` | Custom shader uniform bindings to expressions or expression vectors |
| v2 additions | behavior, libraries, textures, lights, graphics, multipass, audio_texture |

Quality presets declare identical define names. Define names are upper-case identifiers, cannot start with GL_ or contain a double underscore, and values are integers. Ordinary quality bounds are positive; declared boolean graphics bindings use 0/1. Do not put your own #define directives in the shader.

A custom uniform binds one to four expression components: float/vec2/vec3/vec4. It may also use an object with `type` and `source`, whose declared type must match the components. Declare the same name and type in GLSL. Do not take reserved host names, u_audio_ or u_lightcfg_ prefixes, array names or occupied samplers.

The fragment shader starts with `#version 330 core` and provides `void main()`. Only that version directive is accepted; custom includes/defines and unsupported shader operations are rejected. This is a constrained package profile, not unrestricted desktop GLSL.

### Smoothed-response fragment

The following is a `scene.json` fragment, not a complete package or an artistic scene. The shader must declare `uniform float u_low;`, use the response and implement its own image. The STEPS define only changes workload if the shader actually uses it meaningfully.

In addition to the base fullscreen-v2 features from [the manifest example](getting-started.md), declare `behavior.envelope.v1`, `behavior.temporal.v2`, `behavior.transport.v1` and `behavior.reactive_controls.v1` for this example.

```json
{
  "shader": "shaders/main.frag",
  "libraries": [
    "aurs.standard"
  ],
  "quality": {
    "low": {
      "defines": {
        "STEPS": 24
      }
    },
    "medium": {
      "defines": {
        "STEPS": 48
      }
    },
    "high": {
      "defines": {
        "STEPS": 64
      }
    }
  },
  "signals": {
    "low": {
      "type": "envelope",
      "expr": "clamp(audio.low*runtime.low_gain*runtime.light_pulse*runtime.audio_active,0,1)",
      "attack": 0.06,
      "release": 0.4
    }
  },
  "uniforms": {
    "u_low": "signal.low"
  },
  "behavior": {
    "reactive_controls": [
      "low",
      "light_pulse",
      "release"
    ]
  }
}
```

## Mesh/Hybrid

Both profiles require the root objects `libraries`, `environment`, `quality`, `camera` and `statistics`. Hybrid additionally requires `hybrid`. `graphics` and `behavior` are optional with their dependencies. Hybrid-only root extensions include textures, materials, signals, object_graph, reflections, volley_emitter, volumetrics, vertex_layout, multipass, audio_texture, post_geometry and track_text.

| Object | Common contract |
| --- | --- |
| libraries | Mesh: `["aurs.geometry.experimental"]`; Hybrid: `["aurs.geometry.experimental", "aurs.standard"]`, in that order |
| environment | fog_color, fog_density, ambient, planet_fill, fill_origin |
| statistics | buildings, objects |
| camera | times, eyes, targets, fov, near, far, presets; optional micro_motion/clock have Hybrid feature requirements |
| quality | low, medium, high are required; each has mesh and batches, with optional defines |
| mesh assets | `meshes/low.bin`, `meshes/medium.bin`, `meshes/high.bin` |
| vertex layout | Default p3c4n3; p3c4n3uv2t4 requires the UV/tangent feature |
| hybrid.background | shader, libraries, quality and uniforms are required; textures/inputs are optional with dependencies |

Camera route vectors match the number of times, and eye/target routes close. Presets and resource/batch layouts have additional validation. Mesh/Hybrid requires the corresponding shaders and a preview resource. This table does not replace renderer-specific validation or make every listed extension usable in every object.

See [Mesh/Hybrid](mesh-hybrid.md), [camera semantics](cameras.md) and [package layout](package.md).
