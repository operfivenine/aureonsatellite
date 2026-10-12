# Getting Started

Use an Aureon host that implements the documented rendering profiles. Application
version 0.21.11 alone is insufficient to identify its supported feature set.
You need no Python inside a theme package. Python is used only for local authoring
tools and validation against the complete trusted host source.

## Choose a starter

| Editable folder under `examples/starters/` | Output | Purpose |
|---|---|---|
| `shader_v2/` | `shader_v2.aurs` | Stable GLSL helpers and a bass-driven uniform |
| `mesh/` | `mesh.aurs` | One real triangle and a closed camera route |
| `hybrid/` | `hybrid.aurs` | Real geometry with a depth-compatible distant sky |
| `canvas/` | `canvas.aurp` | JSON ring/glow primitives and safe numeric helpers |
| `surface/` | `surface.aurp` | Fixed Gyro GPU model, without package GLSL |

The geometry starters have a labelled structural preview placeholder. Replace it
with an actual render of your scene before publishing. They demonstrate the data
contract; identical three-vertex quality levels do not demonstrate performance scaling.

Shader v1 has a reproduced native import failure in this frozen host; see
validation/known_issues/SHADER_V1_IMPORT.md. Use shader v2 for a new fullscreen theme.

## Edit, pack, validate, import

Copy a starter to your own authoring folder. Set a new lowercase dotted ID,
`name.en`, author and version in `manifest.json`. Keep that ID for updates; raise
the package version. Edit only resources allowed by the chosen profile.

Run from the reference kit's root, using a local Python installation:

```powershell
python tools/pack_theme.py C:\Themes\MyScene C:\Themes\MyScene.aurs
python tools/validate_theme.py C:\Themes\MyScene.aurs --host-source C:\Aureon\Source
```

For a projection, use `.aurp`. Package files must be at the ZIP root, not inside
`MyScene/`. The packer writes ZIP_STORED/DEFLATED files, omits directory entries,
rejects links and requires the correct descriptor. It refuses to overwrite an
existing output unless you explicitly pass `--overwrite`. It does not silently
omit extra files: native validation will reject unsupported payload resources.

The native wrapper checks the frozen reference modules against the host by default.
It uses a temporary profile/preview cache and calls `store.prepare`; it does not
install a package, change your library, or launch playback. For intentional testing
on a different source tree, `--allow-different-host` makes that comparison explicit.
Such a result does not certify compatibility with this frozen baseline.

After validation, use Aureon's package import command and select your scene/projection.
Test its reactive mode with music, quiet audio, pause, seeking and scene changes.
Inspect all cameras, resize/fullscreen and Low/Medium/High. Import preparation is
not a GLSL execution, frame-rate guarantee or complete integration test.

## Keep boundaries clear

Shader v2: write GLSL and use the 32 reserved spectral bands. Mesh/hybrid: supply
real vertex data, use the limited shared audio channels and fixed host operations.
Canvas: write numeric expressions and primitives. Surface: select a fixed model
and its validated parameters. Fields from one descriptor cannot be pasted into
another profile merely because both extensions are ZIP files.
