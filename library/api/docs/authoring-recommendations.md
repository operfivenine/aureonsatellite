# Recommendations for AURS authors

[← API](../README.md) · [Русский](authoring-recommendations.ru.md)

These are authoring recommendations, not new API requirements. They consolidate the November archive's general techniques without shipping artistic scene implementations.

## Start with a readable scene

Write one sentence describing the place, mood and main action. Identify a focal object, foreground/middle/background layers and a quiet area. Check the composition at a small preview size before adding detail. A large archive, many textures or many objects do not by themselves make a scene convincing.

Choose fullscreen v2 for bounded analytical/procedural surfaces and shader-led environments; use Hybrid when architecture, machinery or other real geometry needs materials and a shared background. Do not force every scene into expensive raymarch loops or add a full render graph without a visible purpose.

## Give music a clear role

Choose one primary response and one or two supporting responses. For example, low frequencies can drive heavy motion, mids can control a local mechanism, and highs can affect a restrained detail. These are artistic mappings, not fixed API assignments. Keep the scene readable during silence; independent weather/world motion can continue while music-driven motion settles.

Use an envelope for smoothed levels, a spring for elastic motion, and an integrator for accumulated phase or distance. Multiplying absolute time by a changing instantaneous speed causes discontinuities. Use bounded events/volleys for effects with a birth time, lifetime and cooldown. An arbitrary energy peak is not a reliable beat or BPM estimate.

Apply each user gain once in its intended response path. Test Low/Mid/High, Bump, Light Pulse and Release separately, and test v1 as well as v2 if you claim both. Regional attack inputs are neutral in v1. Do not rename internal analyzer bands or expose an invented 64-band author contract: the published spectrum has 32 bands; spectrum_panels has 16 columns.

## Keep camera, light and materials coherent

Share world coordinates and clocks between related objects and the camera. Preserve a meaningful silhouette from Automatic and fixed views. Declare scene-clock cameras or zero-transition cuts only with the relevant feature. Do not treat the media seek position as the clock for every independent world system.

Emission does not illuminate neighboring surfaces automatically. Plan light sources, contact/shadow cues and reflections separately. Use albedo/normal/ORM consistently where the selected profile supports them; avoid expensive fine detail that is smaller than a pixel. View textures at different camera distances and output sizes to catch shimmer and unstable normals.

## Budget the complete frame

Schema limits are ceilings, not targets. Budget decoded textures with mipmaps, mesh buffers, shadows, reflections, color/depth snapshots and both history buffers. Reduce auxiliary pass resolution where its contribution permits it. Bound volume/trace work to visible regions. Check a lower-end GPU as well as the development device before advertising a hardware target.

Define quality options that remove real work: fewer useful samples, reduced secondary detail, lower auxiliary-buffer resolution or a documented optional effect. A UI quality label alone does not prove lower GPU cost. Test reduced scene resolution and AA together; the scene framebuffer and output framebuffer differ.

## Treat history as disposable

Use current pass inputs only in valid execution order and previous inputs for completed history. Never read the current write target. Expect history to reset after resizing or time discontinuities, and expect GL resources to be recreated after a scene switch. New frames must settle without stale flashes, replayed attacks or dependence on the previous scene.

## Release what you tested

Use portable relative paths, exact filename case and UTF-8. Keep a separate test profile. Verify import/update, quality, silence/pause/seek, cameras, fullscreen and restart on each claimed OS/GPU. Record observed frame time and memory alongside resolution/settings. A Windows pass or stable API status is not a Linux/macOS compatibility result.

Use the [release checklist](release-checklist.md) and [portability guide](portability.md). Keep unreleased artistic experiments and internal build labels out of the public package description.
