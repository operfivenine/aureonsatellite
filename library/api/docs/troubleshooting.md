# Common authoring problems

[← API](../README.md) · [Русский](troubleshooting.ru.md)

| Symptom | Check first |
| --- | --- |
| Unknown required feature | Exact ID spelling and the selected renderer's registry; keep historical experimental strings |
| Missing/unsupported fields | The correct object and renderer schema; do not merge fullscreen fields into Hybrid |
| Import succeeds but the scene is blank | Native GLSL errors, declared resources, sampler names and device limits; import alone does not compile every GPU program |
| Works on Windows, missing assets elsewhere | Filename case, archive-root layout, relative paths and the target GPU/driver |
| Response absent under v1 | Regional attack inputs are neutral; provide the intended level-based fallback |
| Unexpectedly strong response | Duplicated gains in signals/materials; check each user control independently |
| Motion jumps as music changes | Absolute time multiplied by a changing speed; use integrated phase |
| Flash after resize or scene switch | Stale history/feedback or assumptions that old GL resources remain alive |
| Custom track-title field rejected | Hybrid uses the host track_text texture atlas, not arbitrary metadata fields/string uniforms |
| Stable feature still rejected | Wrong profile, missing dependencies or unsupported field combination; stable status does not bypass schema validation |

See [getting started](getting-started.md), [limits](limits-and-qa.md) and [the release checklist](release-checklist.md).
