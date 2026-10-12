"""Trusted Satellite camera rig, shared with the validated AURS camera engine."""
import json
from functools import lru_cache
from types import SimpleNamespace
from aureon_paths import resource_path
from aureon_packages.scene_v2_schema import behavior
from aureon_packages.scene_v2_runtime import PackageSceneRuntimeV2

@lru_cache(maxsize=1)
def definition():
    raw=json.loads(resource_path('assets','satellite_camera.json').read_text(encoding='utf-8'))
    return SimpleNamespace(behavior=behavior({'behavior':raw}),signals=(),uniforms={},
        quality={'medium':{}},source='#version 330 core\n',libraries=())

def camera_presets():
    return definition().behavior['camera']['presets']

def create_camera():
    return PackageSceneRuntimeV2(definition(),'medium',False)
