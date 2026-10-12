# Compatibility and Frozen Scope

Compatibility is defined by renderer contracts, required features and the matching Aureon runtime.

Stable AURS library remains API1.1 revision10.
External manifest format_version1 and engine.api_major1 remain unchanged.
Legacy Canvas aurp.standard remains1.0-foundation experimental. Mesh/hybrid and
surface feature IDs keep their experimental names. No API2 is announced.

Use renderer + required feature IDs + the actual host source/build. min_aureon0.21.11
does not establish support for every renderer profile. Disabled geometry module or missing
OpenGL3.3 support can prevent geometry operation even when the app version matches.

## host quality policy

Per-scene profiles use the actual scene ID, up to256 profiles. Imported shader/mesh/
hybrid AURS supports resolution25/50/75/100%, antialiasing and detail; specialized
stars/shadows/reflections toggles are defined for individual built-in scenes, not
all imported packages. Mesh remains three geometry tiers; an Extreme UI setting
does not add an authored fourth mesh tier.

Auto levels: Lowest/Low/Medium/High. Calibration admission uses p95 GPU≤14 ms,
composition/frame interval≤17 ms, or raster CPU≤14 ms. Minimum samples:30 composition/
CPU and8 GPU when present. Missing GPU timer is not interpreted as zero work.
Downshift uses two independent bad2-second windows; overload thresholds are GPU/
CPU>19 ms or composition>25 ms, with enough samples. No speculative upward promotion.
Manual Advanced has priority. Lowest resolution policy is at most50% and within
960×540 unless a manual resolution override applies; it is not a new package quality
schema name. Advanced/Auto is not integrated for AURP in this baseline.

## Accepted, experimental and deferred examples

Native shader v1 import is broken in this pinned source due to None-valued behavior
metadata; the reproduction and exact error are retained in validation/known_issues/.
No production fix is applied. New fullscreen authoring should use shader v2.

Theme examples are restricted to the registered stock build content recorded in
BUNDLED_CONTENT.json. Holo Planet and Spectral Core are the two shipped editable
Canvas packages. Generic starters exercise schemas without becoming stock entries.
Gyro is an existing model; musical expressiveness remains an open concern.
Landscape is a native enum, not a recommended stock package. Later AURP experiments
are excluded entirely.

Stock installer contents are a separate decision. The user requested the WIN11
projection list without Gyro. The source contract may support/import Gyro while
the installer does not register it as stock content. This kit does not alter either
the installed application or the installer list.
