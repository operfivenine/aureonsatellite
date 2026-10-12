# Validation and Troubleshooting

## Tool boundaries

`tools/pack_theme.py` builds a ZIP from the exact authoring folder, preserving
relative paths and checking basic path/link/output conditions. It is not the native
schema checker. `tools/validate_theme.py` runs the complete matching host's native
store.prepare in an isolated temporary profile. It performs preparation only and
does not install or play a package. Importantly, source/ is a partial reference
excerpt and is not a runnable host root.

The host requires its actual Python dependencies, including PySide6 and NumPy for
geometry. The wrapper exits nonzero on errors and prints structured JSON. A PASS
means preparation succeeded, not that all shaders rendered, the camera route is
well-composed, audio latency is acceptable, or resource cost fits every device.
Fresh shader compilation/linking checks in this edition, if available, are recorded
separately in validation/EN01_CHECK.json with device and exact scope.

## Common failures

| Failure | What to check |
|---|---|
| manifest/descriptor missing | ZIP root, not a nested folder; entry matches extension |
| Unsupported requirement | Exact feature spelling, compatible frozen host, geometry enabled |
| Missing/unsupported fields | Use the chosen profile's closed schema; remove foreign keys |
| Invalid/duplicate path | Slash paths; no drive/traversal/link or case-insensitive duplicates |
| Duplicate JSON field / invalid number | UTF-8 JSON, unique keys, no NaN/Infinity |
| Unknown library | Distinguish aurs.standard, aurp.standard and geometry profile imports |
| Reserved namespace / uniform | Correct type/name; do not redefine aur_ helpers or host uniforms |
| Quality define mismatch | Same names in all tiers, integer bounds, no author #define directives |
| Loop rejected | Canonical bounded form; correct profile's loop budget |
| Missing texture/sampler | Declare every sampler exactly once and reference a valid decoded file |
| Mesh resource/batch mismatch | 40-byte vertices; correct quality paths and exact offset/count partition |
| Invalid camera route | Matching closed eyes/targets/times, separated eye/target, valid ranges |
| Hybrid depth mismatch | Common camera basis/clip, gl_FragDepth from authored world hit |
| GPU surface extra file | Only manifest.json + projection.json; no preview/shader/assets |
| Gyro refused | Require renderer, spectrum64 and gyro feature; native model name gyro_rings |

## Runtime verification checklist

Verify music/quiet/pause and supported seeks, reactive mode, camera cuts/full route,
resize/F11, restyle/import update and GL cleanup. Exercise unsupported hardware or
GL failure paths deliberately only in an isolated test. Check texture color spaces,
thin-pattern aliasing, transparent sorting and reflection fallback visually. Measure
frame interval/CPU/GPU with conditions recorded; a single readback duration does
not measure the entire player FPS.

Use validation/EN01_CHECK.json for fresh kit checks. validation/preserved/ reports
belong to their original deliveries and devices. Do not relabel those as fresh EN
tests or imply that an old passed report establishes a new installer's behavior.
