# Passes, audio textures and postprocessing

[← API](../README.md) · [Русский](render-graph.ru.md)

`scene.multipass.experimental.v1` enables `multipass.passes` and `multipass.inputs`. Each pass declares an ID, shader, size and inputs; optional fields include format/filter/wrap/uniforms/libraries/quality. Size is either fixed [width,height] or scale 0.125–1.0. Formats are rgba8/rgba16f; filtering linear/nearest; wrapping clamp/repeat. Pass files use `shaders/mp_<id>.frag`. `u_mp_delta` and `u_mp_frame` are available.

An input edge refers to a texture, audio spectrum or pass with frame current/previous. Current inputs read an earlier pass in execution order; previous inputs read completed history. Feedback uses ping-pong: do not sample the active write target. Rendering again at the same clock must not advance history. Time jumps/reversal and resizing may reset it. This contract does not supply automatic TAA, reprojection or motion vectors.

`scene.audio_texture.experimental.v1` enables `audio_texture.sampler`: a read-only RG32F 32×1 texture. R contains published bands and G contains peaks, in the same order and with the same values as the uniform arrays. There is no extra analysis or hidden gain. Graph inputs use `audio="spectrum"`.

Hybrid backgrounds read the shared graph through `hybrid.background.inputs`, requiring `scene.hybrid_background_inputs.experimental.v1`. The background shares the scene camera and clock; a separate background `behavior.camera` is forbidden. Background depth must agree with scene geometry.

Order: shared multipass → shadows/reflections → background → geometry → host fog → color/depth snapshot → author post_geometry → AA/scaling → UI. `scene.post_geometry.experimental.v1` runs in the main camera, with read-only inputs; writing `gl_FragDepth` is forbidden. Depth represents opaque surfaces/background, not individual transparent or volumetric layers. Reflections of author post-volume effects are not generated automatically.

Limits: 8 passes, 8 inputs per program, axis up to 8192, and 512 MiB combined history-buffer pairs. These are separate profile limits, not multipliers of every general container limit.
