# Reproduced frozen-host shader v1 import failure

The v1 parser accepts the minimal descriptor. Native store.prepare fails with
AttributeError: NoneType has no attribute get. SceneDefinition.behavior defaults
to None; store.py constructs camera_presets by calling .get on that value.
Use shader v2 for new packages. The exact baseline remains unmodified.

Reproduce from the kit root:

```powershell
python tools/validate_theme.py validation/known_issues/shader_v1.aurs --host-source C:\Aureon\Source
```

This is an intentionally failing fixture, excluded from working starter/example
counts. Its source is in shader_v1/ and exact result in SHADER_V1_IMPORT.json.
