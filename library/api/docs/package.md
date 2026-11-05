# Package structure and fields

[← API](../README.md) · [Русский](package.ru.md)

An `.aurs` is a ZIP archive with `manifest.json`, `scene.json` and permitted assets. Both JSON files belong at the archive root, without an extra enclosing folder.

Fullscreen uses `shaders/main.frag`. Mesh also uses `shaders/main.vert` and binary mesh assets. Hybrid adds `shaders/background.frag`. Custom passes use `shaders/mp_<id>.frag`; postprocessing uses `shaders/post_geometry.frag`. A `preview.png` declaration requires `scene.preview.v1`.

Required manifest fields are `format`, `package_type`, `format_version`, `id`, `version`, `name`, `engine`, `renderer` and `entry`. `name` is a localization object containing at least `en`. The package version has three numeric components. The ID is a lower-case dotted identifier, not a path. `author` only contains `name`; `parameters`, when present in this profile, only permits an empty object. Unknown fields, including arbitrary metadata fields, are rejected.

Links, absolute paths, `..` traversal, case-insensitive duplicate paths, executable payloads and disallowed/unreferenced assets are rejected. JSON is UTF-8; duplicate object keys and nonnumeric NaN/Infinity values are rejected.

Fullscreen scene fields include `shader`, `quality`, `signals` and `uniforms`; v2 additionally supports `behavior`, `libraries`, `textures`, `lights`, `graphics`, `multipass` and `audio_texture`. Dependencies still apply. Mesh/Hybrid schemas are distinct: a field supported somewhere in Aureon is not necessarily valid in another renderer or object.

An index of internal Python field checks is not a JSON Schema. This public reference does not supply a complete JSON Schema or a standalone validator. Verify the completed package by importing it into the target Aureon build and then testing native rendering.
