# GPU Surface Contract

Renderer **`projection.surface.experimental.v2`**. This is the fixed-model host
extension in the documented Aureon runtime. Its suffix does not announce API2.
Later AURP stages are frozen and intentionally excluded.

The ZIP contains **exactly two files**: manifest.json and projection.json.
No assets, preview, package GLSL, mesh, libraries, expressions or Python. Required
features: projection.surface.experimental.v2 and projection.spectrum64.experimental.v2.
Model gyro_rings additionally requires projection.gyro_rings.experimental.v1.

## JSON fields

Root accepts only canvas/surface/palette/camera. Canvas and surface are required;
palette and camera are optional. All nested schemas reject unknown keys.

| Field | Type / range | Default |
|---|---|---|
| canvas.width / height | Number64–512, converted with int; use whole pixels | Required |
| surface.model | spectral_landscape or gyro_rings | Required |
| surface.detail | Integer16–64 | 48 |
| surface.amplitude | Number0.2–1.5 | 1 |
| surface.glow | Number0–1 | 0.5 |
| surface.intensity | Number0.2–1.5 | 1 |
| palette.primary | #RRGGBB / #AARRGGBB | #41d7ff |
| palette.secondary | Same | #795afa |
| palette.accent | Same | #ff548f |
| camera.tilt | Number25–70 | 48 |
| camera.yaw | Number−35–35 | −12 |

Complete editable files:
[manifest](examples/starters/surface/manifest.json) and
[projection](examples/starters/surface/projection.json).
Spectral Landscape remains an accepted native enum in the documented runtime, but its visual
work was deferred. It is documented as an existing contract value, not included
as a current recommended projection package. New model names fail validation.

## Rendering and audio

The trusted host owns model geometry, GLSL, animation and glow post-pass. It uses
PySide6 OpenGL3.3 Core offscreen context, depth and RGBA FBO, premultiplied alpha
and QImage delivery into a transparent projection window. Rendering scale accounts
for DPR with at least2× supersampling and a3× cap. GL failure uses QPainter fallback;
hide/close releases resources, show recreates them.

There are 64 bands from the existing 20-Hz analyzer, not 64 new audio analyzers
or FFT recalculation on each render frame. The host supplies bounded spring-based
band dynamics, smoothed energy/treble, attack detection from positive spectral
changes, musical rotation, pause/silence decay and backwards-seek reset. Repeated
audio timestamps do not create duplicate attacks. These internal dynamics are not
exported as arbitrary JSON coefficients or expression graphs.

Gyro has three independently rotating rings with spectral illumination and bass
expansion. Detail changes host geometry generation, not a user-supplied mesh.
Advanced/Auto is implemented for scenes, **not integrated for AURP**.

## Artistic and release status

Glow is a mandatory artistic requirement from the project owner. The frozen
validator still accepts glow0; this edition does not change that schema. Keep a
visible base halo, add localized music flashes and make attack/return movement
readable at 208×186. A fast gesture followed by a slower return is a recommendation,
not a new implemented model or a measured end-to-end latency guarantee.

Gyro is technically implemented, but its musical expressiveness was criticized.
Native render tests prove response, not artistic acceptance. Its presence in the
cumulative source patch does not imply inclusion in the installer's stock list:
the user separately requested the WIN11 projection list without Gyro. This kit
does not install or change that list. No new AURP variants are declared implemented.
