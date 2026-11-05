# Build your first AURS package

[← API](../README.md) · [Русский](getting-started.ru.md)

1. Choose a renderer before authoring scene fields: fullscreen v2 for a shader-led scene; Mesh for base geometry; Hybrid for geometry with a shared procedural background. Use [the profile table](contract.md).
2. Give the scene its own dotted ID and three-part package version. Updating the same scene normally keeps its ID and increments its version; do not reuse another author's ID for an unrelated scene.
3. Declare only the required features/capabilities used by the selected profile. Use the exact strings from the [registry](../reference/FEATURE_REGISTRY.json), including historical `experimental` spelling.
4. Author `scene.json` for that renderer, then add the declared shaders/assets. Establish the composition and camera before expensive effects and music response.
5. ZIP the contents with `manifest.json` and `scene.json` at the root; use the `.aurs` extension. Merely renaming an arbitrary ZIP does not make it a valid scene.
6. Import using **Settings → Visuals → Import scene**, in a separate test profile. Check the actual error message if import fails, then select the scene in Scene Picker. Import acceptance is followed by native shader/GPU testing.
7. Follow the [release checklist](release-checklist.md), record the tested Aureon version, OS/GPU and settings, then distribute the `.aurs` separately from the player installer.

## Manifest example

This illustrates the manifest contract only. It is not a complete or runnable scene: `scene.json`, shader programs, assets and their dependencies still need to be authored. Add required features for each extension you actually use.

```json
{
  "format": "aureon.theme",
  "package_type": "scene",
  "format_version": 1,
  "id": "org.example.my_scene",
  "version": "1.0.0",
  "name": {
    "en": "My Scene",
    "ru": "Моя сцена"
  },
  "author": {
    "name": "Your name"
  },
  "engine": {
    "api_major": 1,
    "min_aureon": "0.23.0"
  },
  "renderer": "scene.fullscreen_frag.v2",
  "entry": "scene.json",
  "features": {
    "required": [
      "scene.fullscreen_frag.v2",
      "scene.quality.v1",
      "scene.uniforms.v1",
      "scene.shaderlib.v1",
      "scene.standard_library.v1"
    ],
    "optional": []
  },
  "capabilities": {
    "required": [
      "audio.reactive.v1",
      "time.elapsed.v1"
    ],
    "optional": []
  },
  "parameters": {}
}
```

Do not add made-up manifest fields for BPM, track paths, custom Python callbacks or UI windows. The host supplies the documented inputs. See [package fields](package.md), [audio](reactive.md) and [authoring recommendations](authoring-recommendations.md).
