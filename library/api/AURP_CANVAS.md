# AURP Canvas Contract — Legacy Path in the Frozen Baseline

Renderer `projection.canvas.v1`, entry `projection.json`. Existing Canvas features
are documented for compatibility; later AURP development stages are frozen.
The GPU surface descriptor is separate and does not accept these fields.

## Descriptor

Top-level keys: canvas, nodes (required), signals and libraries (optional).
Canvas requires numeric width/height 32–51,200, converted to integers.
Optional supersample is integer 1–300 (default1), bloom 0–0.8 (default0).
Supersample other than1 or bloom>0 requires
`projection.light_canvas.experimental.v1`. These expanded ceilings do not make a
large supersampled canvas affordable; start near the actual 208×186 projection size.

Signals use the basic expression/envelope/integrator grammar. There is no custom
Python, arbitrary GLSL, indexed FFT array or generic model importer.
`time` and `dt` are seconds; rotation/arc angles are degrees in QPainter coordinates.
Coordinates are logical Canvas pixels, x right and y down.

## Primitives

Every node has type and optional translate `[x,y]` (default `[0,0]`), rotation0,
scale `[1,1]`, opacity1 and blend `add` or `normal` (default add). Numeric coordinates,
sizes and transforms are expressions. Colors are `#RRGGBB` or `#AARRGGBB`.
Primitive-specific keys are closed; do not add fields from a different row.

| Type | Geometry / parameters |
|---|---|
| group | nodes (default empty); applies parent transform |
| line | start/end pairs, color, width |
| polyline | 2–12,800 points, color, width |
| polygon | 2–12,800 points, color, width, optional fill |
| ellipse | center, rx/ry (default20), color, width, optional fill |
| ring | center, rx/ry, color, width; no fill field |
| arc | center, rx/ry, color, width, start_angle0, span_angle180 |
| radial_glow | center, radius20, color, strength1 |
| image | source referencing `assets/*.png`, rect of four expressions |
| hologram | center, radius64, model planet/spectral, primary/secondary, bass/mid/treble/energy/impact |

The hologram primitive requires `projection.hologram.experimental.v1`. It is an
existing host-owned Canvas feature, not the Gyro GPU model. Keep it separate
from later frozen experiments. Nodes must be nonempty overall; total max12,800,
depth limit800, hologram count max200. Practical budgets should be far smaller.

Fill is absent/null, a solid color, or a linear/radial gradient. Linear gradient:
type/start/end/stops; radial: type/center/radius/stops. Stops are 2–12 increasing
`[position,color]` pairs with position0–1. Gradients and transforms have their
manifest feature vocabulary; declare the behavior actually used.

## `aurp.standard` foundation

Opt-in `"libraries": ["aurp.standard"]` and required
`projection.standard_library.experimental.v1`. Version **1.0-foundation**, experimental.
This is a numeric helper set, not the AURS GLSL library despite the `aur_` prefix.

| Function | Meaning |
|---|---|
| aur_sat(x) | Clamp to 0–1 |
| aur_lerp(a,b,t) | Linear interpolation; t is not automatically clamped |
| aur_smoothstep(a,b,x) | Clamped smooth interpolation; equal edges return0 |
| aur_fract(x) | x−floor(x) |
| aur_remap(x,a,b,c,d) | Clamped remap from a..b into c..d; equal input edges return c |

Libraries are unique known names, at most16 imports. These helpers work only in
the opt-in Canvas expression context; `projection.surface.experimental.v2` has no
libraries/signals/nodes field. See the editable
[Canvas starter](examples/starters/canvas/projection.json).
