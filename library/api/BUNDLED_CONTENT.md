# Stock Content — the documented Aureon runtime

Inventory checked against the final application source archive,
`aureon_content/builtins.py`, shipped assets and App ZIP. BUNDLED_CONTENT.json
records source member paths, hashes and matching package bytes. Files placed under
data/examples or tests/fixtures are not treated as registered stock content.

| Kind | Name | ID | Implementation |
|---|---|---|---|
| Scene | Default | default | builtin.painter |
| Scene | Warp | warp | builtin.painter |
| Scene | Orbital Dawn | orbital_dawn | builtin.painter |
| Scene | Orbital Sun | orbital_dawn_gl | builtin.gl |
| Scene | Storm Tornado | storm_tornado_gl | builtin.gl |
| Scene | Volcanic Valley | volcanic_valley_gl | builtin.gl |
| Scene | Stellar Horizon | stellar_horizon_gl | builtin.gl |
| Scene | Aureon Satellite | lava_horizon_gl | builtin.gl |
| Projection | Orbital Atlas | orbital_atlas | builtin.projection_window |
| Projection | Reactor Core | reactor_core | builtin.projection_window |
| Projection | Holo Planet | org.aureon.holo_planet | projection.canvas.v1,3.0.1 |
| Projection | Spectral Core | org.aureon.spectral_core | projection.canvas.v1,3.0.1 |

Only Holo Planet and Spectral Core are shipped editable projection packages in the
stock assets folder. Their exact package bytes and unpacked authoring JSON are in
examples/stock/. Built-in scenes/windows are implemented in trusted Python/GLSL,
and are not external AURS/AURP packages. The stock selector contains no registered
mesh/hybrid AURS theme or Gyro projection.

The kit retains five generic package-schema starters under examples/starters/.
Those are clearly marked fixtures, not added stock content. Surface support and
model names are documented as the frozen API, without introducing later stages or
adding models to the stock list. Only bundled content is used for theme walkthroughs.
