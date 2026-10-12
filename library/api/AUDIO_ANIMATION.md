# Audio, State and Animation

## What each profile receives

| Path | Musical data available to the author |
|---|---|
| Shader v1 / Canvas numeric expressions | low/mid/high, energy/flux/brightness/crest/beat, fast/medium/slow/presence/phase, zone0–7 |
| Shader v2 | Above plus onset/onset_strength/flare/glint; uniforms bands[32], peaks[32], bounded event slots |
| Hybrid expressions | low/mid/high/energy/beat/presence; no independent FFT array |
| Mesh legacy batch audio | Five coefficients for RMS/low/mid/high/beat |
| surface | Internal 64-band20-Hz input; JSON does not expose an expression graph |

These are normalized host controls, not raw PCM or an API for device capture.
Shader v2 uniforms are not automatically usable as hybrid material expressions.
Many display bars driven by three channels do not become independent FFT bins.
`audio.beat` is a trusted reactive control, not a guaranteed BPM/beat-grid estimate.

## Numeric and temporal grammar

time/dt are seconds; pi is the numeric constant. Basic functions and extended
functions are listed in API_REFERENCE.md. Signals reference `signal.<name>` and
are evaluated in acyclic dependency order. Numeric expressions have no script side
effects or arbitrary state mutation.

Basic Canvas/shader v1 signal forms:

| Type | Required field | Optional fields/defaults |
|---|---|---|
| expression | expr | type defaults to expression |
| envelope | expr | attack0.04, release0.3; each0.001–60 s |
| integrator | rate | wrap360 (0.001–100,000), initial0 (±100,000) |

Shader v2 adds initial for envelope and these types:

| Type | Operation / main parameters |
|---|---|
| derivative | Filtered change of expr; attack0.03/release0.25, scale1 (±1000), absolute false, initial0 |
| spring | Target expr; frequency1.5 (0.05–8), damping0.85 (0.05–4), min/max, initial |
| gate | Hysteresis with on0.6/off0.4, off<on; attack0.05/release0.25, initial0–1 |
| state | Rate plus damping0–60, initial, min/max, optional wrap0–100,000 |
| history | expr, window0.1–10 s, mode mean/max/min/interval/rate; bounded signal statistics |

V2 history interval/rate additionally bounds threshold/rise/min_interval/stale/
min_events (2–32). It stores signal aggregates/events, not arbitrary object positions
or frames. Presets: bass_punch, beat_punch, air, music_energy, broadband_pressure,
slow_orbit. Each expands into existing primitives; it is not a new analyzer.
Exact defaults/formulas are in source/aureon_packages/scene_v2_schema.py.
Hybrid permits only expression/envelope/integrator/gate/spring, with its own32-signal
and channel limits. Derivative/history/state and full shader presets must not be
copied into hybrid without checking the native restricted result.

For a basic musical pulse:

```json
{
 "bass": {"type":"envelope", "expr":"clamp(audio.low*2,0,1)",
 "attack":0.025, "release":0.18}
}
```

For three-channel rise compensation in hybrid, use short and long envelopes plus
`max(0,signal.fast-signal.slow)`. Clamp any boost. This estimates movement of the
available controls; it cannot recover missing spectral bins or erase upstream delay.

## Motion units and clocks

Shader helper object transforms conventionally use +Y-up and radians. Host mesh
graph uses Z-up and degrees. Canvas transforms/arc angles use degrees. The numeric
integrator has no inherent angle unit: set its rate/wrap to match its consumer.
Use a stable scene-time camera independent of the track position unless your artistic
design deliberately requires another behavior. Media seeking and scene clocks are
different concepts. Mesh routes keep moving during pause; music gains decay.

For shader v2, runtime flags are playing/audio_mode/audio_active/reactive/paused/
ambient; identical names are supported in hybrid expression contexts. Basic Canvas
and shader v1 expressions do not expose runtime.*. AURP surface's pause/seek handling
is fixed inside host. Do not promise a JSON pause-freeze switch that is not present.

## Practical dynamics

Separate fast attack, slower return and slow environment modulation. Avoid making
every light, camera and object pulse identically. Preserve base illumination during
silence if that is required for scene readability; let musical additions decay.
Test isolated bass/high inputs, an actual sparse track and a dense master at the
final display size. Avoid time-only random heights presented as spectrum response.

Runtime fixture response times do not measure end-to-end device latency. Merge
small display cells at distance to reduce aliasing. pixel-response tests
likewise do not establish musical expressiveness. Only stock projections
are used as content examples; the generic fixtures exercise supported API schemas.
