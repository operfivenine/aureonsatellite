# Limits, quality and testing

[← API](../README.md) · [Русский](limits-and-qa.ru.md)

General limits include an 800 MiB archive, 1600 MiB expanded contents, a 400 MiB ordinary resource and 12.5 MiB GLSL. Large mesh resources undergo separate profile checks. Mesh assets allow up to 128 maps, a 16384 texture axis, 1 GiB decoded texture budget, 32 material texture slots, 8 million mesh vertices, 1024 batches and 256 materials. Exact values: [feature registry](../reference/FEATURE_REGISTRY.json).

These values are validation ceilings, not recommended targets. Hardware `GL_MAX_TEXTURE_SIZE`, `GL_MAX_TEXTURE_IMAGE_UNITS` and available memory may be lower. Account for mipmaps, history ping-pong pairs, shadow/reflection targets, scene snapshots and mesh buffers. A supported 4K output does not make every scene affordable.

`scene.graphics_advanced.v1` connects declared graphics switches to the UI. Resolution and antialiasing belong to the host; author switches select permitted boolean quality defines, not arbitrary shader-source replacement. A reduced scene framebuffer and the output MSAA framebuffer are separate targets.

Test manifest/schema → actual import and update → Low/Medium/High and declared Extreme → 50/100% resolution and AA → Reactive v1/v2 → pause/seek/silence → scene switching → fixed/Automatic cameras → fullscreen → application restart. Use a separate test profile. Container acceptance does not prove native shader compilation on Intel/NVIDIA/AMD or memory/frame-time behavior.

The host releases expanded scene definitions on deactivation. A package must not rely on its GL resources surviving a scene switch. Use the [release checklist](release-checklist.md).
