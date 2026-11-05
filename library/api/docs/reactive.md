# Audio and declarative behavior

[← API](../README.md) · [Русский](reactive.ru.md)

`audio.low`, `audio.mid`, `audio.high`, energy and regional attacks have different meanings. `audio.low_attack`, `audio.mid_attack` and `audio.high_attack` require `audio.regional_attacks.v2`. Regional attacks are neutral under Reactive v1; provide a level-based fallback if the scene should respond under both engines. There is no new FFT or universal BPM API.

Fullscreen v2 publishes `u_bands[32]`, `u_peaks[32]`, `u_events[8]` and typed reserved uniforms. The analyzer's 64 internal bands are not the 32 published values. `scene.spectrum_panels.v1` is a separate opt-in: 16 columns with renderer-rate smoothing, enabled through `behavior.spectrum_panels`.

Declare supported UI controls in `behavior.reactive_controls`, with `behavior.reactive_controls.v1`. Expressions using `runtime.bump`, `bump_strength`, `low_gain`, `mid_gain`, `high_gain`, `light_pulse` and `release_scale` need matching declarations. Bump, band gains and Light Pulse should each control the intended effect. Applying the same gain twice changes the response unintentionally.

The v2 signal graph supports expression, integrator, envelope, derivative, spring, state, history and permitted named presets, subject to schema dependencies and bounded graph evaluation. History operations include mean/max/min/interval/rate; windows are 0.1–10 seconds. Interval/rate use a threshold, minimum interval, stale handling and 2–32 events. This is bounded signal history, not arbitrary package memory or a guaranteed BPM estimator.

Hybrid history requires `scene.mesh_history_signals.experimental.v1`. Hybrid channels are a separate subset and are not identical to the complete fullscreen-v2 table. Use an integrator and delta-time for continuous motion. Handle pause, seek and engine changes without replaying past attacks.

Exact channels and types: [uniform/channel reference](../reference/UNIFORMS_AND_CHANNELS.json).

The index records u_events[8] as the baseline event-array size. The profile permits an explicit size within the event_slots limit, large enough for all declared event slots. Eight is not a universal ceiling for every event configuration.
