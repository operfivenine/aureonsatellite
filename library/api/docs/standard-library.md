# Standard GLSL library

[← API](../README.md) · [Русский](standard-library.ru.md)

New fullscreen v2 scenes request `libraries: ["aurs.standard"]` and the required feature `scene.standard_library.v1`. Hybrid declares the standard library in both the manifest and shared background. GLSL uses `#version 330 core`; custom `#include` and arbitrary preprocessing directives are not supported. Quality defines are declared in JSON.

The `aur_` namespace belongs to the host. Do not redefine its functions. The eight standard-library sections are Camera, Reactive, Environment, Objects, Lighting, Atmosphere, Motion and Presentation. They are API sections, not eight rendering passes.

The [symbol index](../reference/STANDARD_LIBRARY_SYMBOLS.json) records function names and arguments, structures and module dependencies. The public edition adds verified return types and structure fields. See the [readable index](glsl-symbols.md). Function bodies are not included.

Aureon supplies the requested library when loading a package. Do not embed a copy of the host implementation in the scene. Optional modules are not automatically included: check `public_libraries`, `legacy_libraries` and `requires`. An internal implementation revision is not the author's package version.
