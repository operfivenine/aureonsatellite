# Current-track inputs

[← API](../README.md) · [Русский](track-inputs.ru.md)

`scene.track_palette.experimental.v1` publishes vec3 uniforms `u_track_palette0` and `u_track_palette1`: six finite nonnegative weights whose sum is 1. The initial state is the first turquoise scheme; target schemes cycle during a session. Track changes and replay after the end select the next target; pause, seek and reanalysis do not. The 2.4-second transition continues from the current blend on rapid Next changes and survives GL recreation. The author chooses colors from these weights.

`scene.track_text.experimental.v1` is available in Hybrid. Root `track_text` contains only `sampler`, named `u_tex_...`. The host draws the current title into a read-only RGBA8 2048×128 texture; the package samples pixels, not a metadata string or filesystem path. Qt handles Unicode. Control characters are removed, titles are limited to 160 characters, long text is visually ellipsized and empty text clears the atlas.

`u_track_text_metrics` is vec4: width/2048, nonempty flag, 1/2048, 1/128. Float `u_track_text_age` measures time since the title changed. Redrawing an unchanged title does not trigger a new texture upload every frame. Track text occupies its own sampler, distinct from image/material/audio/buffer names.

Palette and text are independent. Neither provides arbitrary tags, Python execution, filesystem or network access. Custom song_title JSON fields or string GLSL uniforms are not this contract.
