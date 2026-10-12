# Aureon AURS / AURP Authoring Reference — EN

English reference for creating scenes and projections in Aureon.

| Contract | Version / status |
|---|---|
| ZIP manifest format / engine API major | 1 / 1 |
| AURS GLSL library `aurs.standard` | 1.1, stable, implementation revision 10 |
| AURP Canvas library `aurp.standard` | 1.0-foundation, experimental |
| Mesh/hybrid and AURP GPU surface | Individually versioned experimental profiles |

Start with [Getting Started](GETTING_STARTED.md). Then select a
[rendering profile](RENDERING_PROFILES.md) and read its contract:
[shader AURS](AURS_SHADER.md), [geometry AURS](AURS_GEOMETRY.md),
[Canvas AURP](AURP_CANVAS.md), or [GPU surface AURP](AURP_SURFACE.md).

- [Common manifest and package API](API_REFERENCE.md)
- [Audio and animation](AUDIO_ANIMATION.md)
- [Scene authoring using stock content](AUTHORING_GUIDE.md)
- [Verified stock-content inventory](BUNDLED_CONTENT.md)
- [GLSL modules, structures and signatures](GLSL_CATALOG.md)
- [Compatibility and frozen scope](COMPATIBILITY.md)
- [Validation, packaging and troubleshooting](VALIDATION_TROUBLESHOOTING.md)
- [Baseline, evidence and known limitations](BASELINE_AND_EVIDENCE.md)
- [Machine-readable API index](API_INDEX.json) and [example index](EXAMPLES_INDEX.json)
- [Fresh checks](validation/EN01_CHECK.json), [source provenance](SOURCE_MANIFEST.json),
 and [file hashes](FILE_MANIFEST.json)

`examples/starters/` contains five editable minimal examples and their packages.
`examples/stock/` contains the shipped Holo Planet and Spectral Core packages and
editable JSON. The five generic starters are schema-validation fixtures, not stock
themes. No outside-theme walkthrough or reference-theme package is included.

`tools/` contains a ZIP builder and a native validation wrapper. Validation requires
a **complete matching Aureon source tree** and its dependencies; `source/` is only
a reference excerpt. This kit is not a standalone player or a general mesh exporter.
Original code/assets and preserved JSON reports remain unmodified; all new author
documentation is English. No later AURP graph, model or API is implied.

Fresh checking found a frozen-host shader v1 import failure (`behavior=None` in
store metadata construction). The v1 contract is documented, but it is not offered
as a working starter. A reproduction is included under validation/known_issues/;
use shader v2 for a new fullscreen package. No host fix was applied.
