# Baseline, Evidence and Known Limitations

This reference describes implemented contracts and provides minimal editable examples. Reference source files, GLSL and packages include SHA-256 provenance.

## Preserved results

- Projection validation:102 tests,100 passed,2 skipped; native RTX3070, gyro/surface/post GLSL,
 real-audio integration, legacy projections/switch-back, pause decay and lifecycle/
 raster fallback. The source-patch report had exe_built=false. Its GPU/readback
 median≈0.52 ms/p95≈0.72 ms is a narrow original run, not total application FPS.
- Scene / quality validation:90 passed plus2 existing skips; RTX3070 scene/quality checks. A further
 test of restoring actually playing audio after calibration did not run due to
 the permission-check service limitation at that stage.
- Stock content was checked against Installer-SRC and App ZIP. Both shipped Canvas
 packages match their source bytes; built-in registration IDs were read from the
 matching source. The75 pinned reference modules also match Installer-SRC.
- Older stage checks remain in the earlier RU archive. This kit does not import
 outside themes into its examples or relabel old reports as fresh certification.

Original selected JSON reports are copied to validation/preserved/. Fresh EN kit
checks have their own report and explicitly state whether GL checks ran.

## Open limitations

Fresh EN checking reproduced a shader v1 import error: SceneDefinition.behavior
is None, while store.prepare constructs camera presets with `.get('camera')`.
The native v1 scene parser accepts the descriptor, but package preparation fails
with AttributeError. A minimal source/package reproduction is included under
validation/known_issues/. The five working starters therefore use shader v2,
mesh/hybrid, Canvas and surface. The frozen host is not patched in this edition.

Gyro is technically reactive, but the user found new AURP dynamics insufficiently
expressive. Mandatory glow is an artistic requirement while schema glow0 remains
allowed. Later proposed projection variants are not implemented in this edition.
Advanced/Auto for AURP is not implemented. Intel/frozen installer behavior needs
its own verification; the English kit is not installer acceptance.

Mesh/hybrid has no independent FFT array, skeletal animation, physics, universal
distance-based mesh LOD, shadow maps, SSR, recursive mirrors or generic HDR bloom.
Glass is an alpha/reflection approximation without refraction/interior rendering.
Graph culling does not automatically sectorize every baked batch in a new scene.

One old artificial hybrid-background shader-failure test with MP3 stalled shutdown
at QMediaPlayer.stop. Cause was not established; WAV, ordinary MP3 and frozen tests
completed in those reports. This documentation refresh does not close that issue.
Avoid broad claims of "no regressions" based on package validation alone.

## What this kit provides

English documents, exact indexed symbols/features/limits, five working minimal starters,
stock package examples, reference source/GLSL, ZIP packaging and native
preparation tools, plus reproducible evidence and integrity manifests. It does
not provide a general-purpose scene editor, automatic exporter, standalone player
or finalized stable mesh SDK. New host operations remain separate development work.
