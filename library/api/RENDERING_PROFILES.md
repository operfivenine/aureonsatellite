# Rendering Profiles

| Renderer | Entry | Package-owned rendering data | Audio boundary |
|---|---|---|---|
| `scene.fullscreen_frag.v1` | scene.json | One fragment shader, quality defines, basic signals/uniforms | Basic reactive channels and zones |
| `scene.fullscreen_frag.v2` | scene.json | One fragment shader, stable/experimental helpers, behavior, textures/lights | Extended channels, 32 bands/peaks, bounded events |
| `scene.mesh.experimental.v1` | scene.json | Real vertices, normals/colors, batches, route and environment | Legacy five-component batch audio weights |
| `scene.hybrid_mesh.experimental.v1` | scene.json | Geometry plus GLSL background/materials and opt-in host features | Shared low/mid/high/energy/beat/presence; no FFT array |
| `projection.canvas.v1` | projection.json | JSON primitives, groups, gradients, transforms and safe signals | Basic reactive channels/zones; no free spectral array indexing |
| `projection.surface.experimental.v2` | projection.json | Fixed model and palette/camera/surface settings | Host-owned 64-band input at 20 Hz |

The renderer suffix is not the overall API major. AURS v2 means the shader behavior
profile here; mesh/hybrid and surface remain separate experimental contracts.
`aurs.standard` helpers compute values inside GLSL. They do not automatically create
VAOs, traverse a JSON object graph, perform GPU instancing or allocate reflection FBOs.
The mesh host performs those operations only when supported and explicitly requested.

## Required base features

Shader v1/v2 have no mandatory base feature requirement in the manifest validator;
declare the renderer and the features actually used. Library imports in shader v2
require `scene.standard_library.v1`. Hybrid requires all of:

```
scene.mesh.experimental.v1
scene.hybrid_mesh.experimental.v1
scene.standard_library.v1
```

Mesh requires `scene.mesh.experimental.v1`. Surface requires
`projection.surface.experimental.v2` and `projection.spectrum64.experimental.v2`;
the `gyro_rings` model also requires `projection.gyro_rings.experimental.v1`.

Preview, textures, shader Extreme, camera controls and mesh extensions have their
own gates. See [API_INDEX.json](API_INDEX.json) for accepted feature vocabulary
captured from the frozen native validator. A known name is not proof that every
profile supports the associated JSON fields. Required feature checks and descriptor
validation both apply.

## Resource ownership

The package owns checked JSON, GLSL where permitted, meshes/images and metadata.
The application owns the audio analyzer, clocks, window, camera execution, render
context, imports, cache, profiles and cleanup. A package cannot add a new host
operation, executable callback or network loader. Changing the renderer implementation
requires a trusted host change; none is performed by this reference kit.
