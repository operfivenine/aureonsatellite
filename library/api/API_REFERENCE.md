# Common Package API

Normative implementation for this edition: the hash-pinned the documented Aureon runtime source excerpt. The native validator remains the authority for acceptance.
Use [API_INDEX.json](API_INDEX.json) for exact feature/module/limit tables.

## Container

`.aurs` and `.aurp` are ZIP files. `manifest.json` and the entry descriptor sit at
the root. Paths use `/`, are relative, and must not contain empty, `.` or `..`
components, a drive prefix, backslash or NUL. Paths are limited to 160 characters
and duplicate names are checked case-insensitively. Symlinks/special files,
encryption and compression other than STORED/DEFLATED are rejected.

JSON is UTF-8, optionally with BOM. Duplicate keys, NaN and Infinity are rejected.
Numbers and descriptor fields are bounded. Unknown fields are generally rejected
by the closed object schemas. Python, JavaScript, EXE/DLL and arbitrary payloads
are not package resources.

## Manifest

| Field | Required | Contract |
|---|---|---|
| format | Yes | Exactly `aureon.theme` |
| package_type | Yes | `scene` for AURS; `projection` for AURP |
| format_version | Yes | Integer 1 |
| id | Yes | Lowercase dotted identifier; 2–8 components; max 120 chars |
| version | Yes | Numeric `major.minor.patch`; each part 1–5 digits |
| name | Yes | 1–16 localized names, including nonempty `en` fallback |
| author | No | Object containing required nonempty `name` |
| engine | Yes | `api_major: 1`; optional numeric-version `min_aureon` |
| renderer | Yes | One of the six documented profiles |
| entry | Yes | `scene.json` or `projection.json`, matching package type |
| features | No | `required` / `optional` string lists, max 64 per list |
| capabilities | No | Same requirement format; distinct capability vocabulary |
| parameters | No | Only `{}` supported |
| preview | No | Scenes only: exactly `preview.png`, paired with file/feature |

An ID matches `[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,7}`.
Localized names are nonempty, at most 160 characters and contain no control chars.
Unknown required features/capabilities fail; unknown optional names do not grant
support. `min_aureon` compares the application version, not WIN/FIX identity, so
feature gates and a compatible host remain necessary.

Shared capabilities accepted by this baseline are `audio.reactive.v1`,
`audio.spectrum.v1`, `audio.events.v1`, and `time.elapsed.v1`.
These names do not erase profile-specific audio limitations.

For example, the shader v2 starter manifest is
[examples/starters/shader_v2/manifest.json](examples/starters/shader_v2/manifest.json).
For updates, retain the ID and increment the package version. Preserve your last
working package. Use the application's installation/rollback flow rather than
overwriting its cache manually.

## Preview

For shader scenes a preview is optional, but a file, `manifest.preview` and required
`scene.preview.v1` must agree. Mesh/hybrid uses a closed resource set requiring
`preview.png`. Preview decoding requires real PNG content and rejects corrupt data.
The historic 1 MiB and 2048-axis preview-specific caps are removed in this host;
large PNGs are decoded directly toward the roughly 640×360 preview-cache size.
General ZIP/resource limits still apply. Preview limits are not texture limits.
AURP does not accept `manifest.preview`; surface has exactly two files.

## Common capacity ceilings

| Container metric | Native maximum |
|---|---:|
| Compressed archive | 800 MiB |
| Sum of expanded file sizes | 1600 MiB |
| Single resource | 400 MiB, with stricter profile exceptions |
| JSON resource | 50 MiB |
| Archive entries | 7200 |

These expanded ceilings are still present in the frozen source.
They are validator ceilings, not recommended authoring budgets. Hardware, Qt image
allocation, shader cost and profile-specific limits remain separate. Do not infer
safe VRAM use or frame rate from a package passing these limits.

## Expressions

Expression input is a JSON number or a string containing bounded numeric syntax.
Use `+ - * / %`, unary signs, numeric literals, `time`, `dt`, `pi`, supported
`audio.*`, `signal.*` and, where provided, `runtime.*`. No comparisons, boolean
syntax, conditional expression, subscript, arbitrary attribute, import or callback.
Signals must have valid names and an acyclic dependency graph.

Basic functions: sin/cos/abs (one argument), min/max (2–4), clamp (3).
Shader v2/hybrid additionally provide sqrt/exp/floor/ceil/fract (1), pow (2),
lerp/smoothstep (3). Canvas can opt into five `aurp.standard` helpers.
Division/modulo near zero returns zero; finite evaluation is clamped to ±1,000,000.
See [audio and animation](AUDIO_ANIMATION.md) for stateful primitives and units.

Maxima: 25,600 expression characters, 9600 AST nodes, depth 1200, 4800 shader/basic
signals. Hybrid independently limits its shared signals to 32. Large valid graphs
can still be expensive; start small.
