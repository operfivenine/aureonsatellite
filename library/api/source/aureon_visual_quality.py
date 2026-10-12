"""Validated per-scene overrides. Empty profiles preserve preset rendering."""
import json
import re

COMMON = ('resolution', 'antialiasing')
BUILTIN_EFFECTS = {
    'default': ('stars',), 'warp': ('stars',), 'orbital_dawn': ('stars',),
    'orbital_dawn_gl': ('detail', 'stars', 'atmosphere'),
    'stellar_horizon_gl': ('detail', 'stars', 'nebula', 'reflections'),
    'lava_horizon_gl': ('detail', 'stars', 'shadows', 'soft_shadows', 'highlights'),
    'volcanic_valley_gl': ('detail', 'shadows', 'occlusion', 'smoke', 'particles'),
    'storm_tornado_gl': ('detail', 'shadows', 'reflections'),
}
TOGGLES = frozenset(key for fields in BUILTIN_EFFECTS.values() for key in fields if key != 'detail') | {'antialiasing'}


def scene_key(style, registry=None):
    if registry is None:
        from aureon_content import get_registry
        registry = get_registry()
    entry = registry.resolve(str(style), 'scene')
    return entry.id if entry else str(style)


def capabilities(style, registry=None):
    if registry is None:
        from aureon_content import get_registry
        registry = get_registry()
    entry = registry.resolve(str(style), 'scene')
    key = entry.id if entry else str(style)
    if entry and entry.source != 'builtin':
        return COMMON + (('detail',) if entry.renderer in ('scene.fullscreen_frag.v1', 'scene.fullscreen_frag.v2',
                'scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1') else ())
    return COMMON + BUILTIN_EFFECTS.get(key, ())


def decode(value):
    if isinstance(value, str):
        if len(value) > 131072:
            return {}
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return {}
    if not isinstance(value, dict):
        return {}
    clean = {}
    for scene, profile in list(value.items())[:256]:
        if not isinstance(scene, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', scene) or not isinstance(profile, dict):
            continue
        fields = {}
        for key, item in profile.items():
            if key == 'resolution' and type(item) is int and item in (25, 50, 75, 100):
                fields[key] = item
            elif key == 'detail' and isinstance(item, str) and item in ('low', 'medium', 'high', 'extreme'):
                fields[key] = item
            elif key in TOGGLES and type(item) is bool:
                fields[key] = item
        if fields:
            clean[scene] = fields
    return clean


def encode(value):
    return json.dumps(decode(value), ensure_ascii=True, sort_keys=True, separators=(',', ':'))


def profile_for(value, style, registry=None):
    return {key: item for key, item in decode(value).get(scene_key(style, registry), {}).items()
            if key in capabilities(style, registry)}


def shader_signature(profile):
    return tuple(sorted((key, value) for key, value in profile.items() if key not in COMMON))


def effect_defines(profile):
    return ''.join(f'#define AUR_{key.upper()} {int(profile.get(key, True))}\n'
                   for key in ('stars','atmosphere','nebula','reflections','shadows','occlusion','smoke','particles'))
