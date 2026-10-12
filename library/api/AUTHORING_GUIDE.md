# Scene Authoring for Aureon

This guide considers only content registered or bundled as stock in the documented Aureon runtime. The exact inventory and source/App ZIP evidence are in
[BUNDLED_CONTENT.md](BUNDLED_CONTENT.md) and BUNDLED_CONTENT.json.
Five generic starters demonstrate authoring contracts; they are validation fixtures,
not claims that five new themes are installed in the stock build.

## Built-in scene lessons

The painter scenes Default, Warp and Orbital Dawn show the value of a small,
readable composition and a modest redraw budget. The GL scenes Orbital Sun,
Storm Tornado, Volcanic Valley, Stellar Horizon and Aureon Satellite offer useful
reference directions for procedural forms, atmospheric layers and musical accents.
They are trusted built-ins, not drop-in AURS packages. Their renderer IDs, uniforms,
settings and factory code must not be copied into a package manifest as if the
package loader accepted builtin.gl or builtin.painter.

For a new fullscreen AURS, start with the validated shader_v2 fixture. Recreate
only the visual concept you need using allowed uniforms, stable library imports
and bounded GLSL. Use shorter attack and slower return for clear musical gestures;
separate fast object accents from slow ambient movement. If the visual idea requires
new host operations, a package alone cannot add them.

Stellar Horizon and Aureon Satellite expose built-in spectrum-related controls;
this does not grant every AURS the same UI toggles. Shader v2 has its own reserved
32-band arrays, hybrid has limited shared channels, and AURP surface owns its64-band
input internally. Choose the actual package profile before designing musical behavior.

## Stock projection packages

Holo Planet and Spectral Core are shipped Canvas AURP packages, version3.0.1,
under assets/projections. Their editable JSON is included under examples/stock/.
They require the existing hologram/light-canvas features, not the surface descriptor.
Study how center/radius/colors and bass/mid/treble/energy/impact expressions configure
a fixed host-owned hologram primitive. They do not carry Python, GLSL or model files.

Orbital Atlas and Reactor Core are trusted native projection windows. They are
registered stock content, but are not editable AURP ZIP examples. Use their appearance
as a reference only within the capabilities of the chosen package profile.
Do not invent a manifest renderer builtin.projection_window for an external package.

surface remains documented as a supported experimental authoring contract.
Its generic surface fixture exercises gyro_rings; that is not a stock-list entry.
Later AURP stages remain frozen. Keep a visible glow and evaluate a projection's
musical gesture at the final208×186 logical size; schema validity does not establish
artistic acceptance or responsiveness.

## Geometry authoring

No mesh/hybrid theme is registered as stock in this build. Their implemented API
is documented because authors can create/import such packages. The minimal mesh/
hybrid fixtures show real vertex layout, complete batches and a common-camera sky.
They are technical examples, without a separate outside-theme walkthrough.

Set Z-up/degrees deliberately, close the camera route and test interpolated views.
Keep a foreground/midground/background composition so an elevated camera does not
reveal an unfinished scene edge. Separate coincident surfaces to avoid shimmer,
filter tiny repeating patterns, reuse valid graph templates and lower geometry/
reflection cost in quality tiers. Alpha sorting is approximate; reflection FBOs
are separate passes. Emission does not automatically illuminate adjacent surfaces.

## Practical workflow

1. Select a supported package renderer and declare required feature IDs.
2. Edit a generic starter, set your own ID/version/name and validate its package.
3. Establish camera/depth/material conventions before adding visual complexity.
4. Test music, quiet audio, pause/seek and independent frequency responses.
5. Author real lower-cost quality tiers and verify supported host overrides.
6. Inspect the entire route, distant small patterns and fallback paths.
7. Measure behavior/draw/GPU and then verify the actual player workload.
8. Replace geometry preview placeholders with real renders; retain the last working
 release and record exact host/feature/test conditions for delivery.
