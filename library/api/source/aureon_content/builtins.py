"""Trusted application registrations. Import targets are never package input."""
from importlib import import_module
from .models import ContentEntry


def lazy_factory(module, name):
    def create(*args, **kwargs):
        return getattr(import_module(module), name)(*args, **kwargs)
    return create


def register_builtins(registry):
    for name, key, reactive in (
        ('Default', 'default', ''), ('Warp', 'warp', 'warp_audio_drive'),
        ('Orbital Dawn', 'orbital_dawn', 'orbital_dawn_reactive'),
    ):
        registry.add_builtin(ContentEntry(key, 'scene', name, 'builtin.painter', 'scene.'+key, reactive))
    scenes = (
        ('Orbital Sun', 'orbital_dawn', 'OrbitalDawnGL', True, ''),
        ('Storm Tornado', 'storm_tornado', 'StormTornadoGL', False, ''),
        ('Volcanic Valley', 'volcanic_valley', 'VolcanicValleyGL', True, ''),
        ('Stellar Horizon', 'stellar_horizon', 'StellarHorizonGL', True, 'set_floor_spectrum_enabled'),
        ('Aureon Satellite', 'lava_horizon', 'LavaHorizonGL', True, 'set_panel_spectrum_enabled'),
    )
    for name, module, cls, transport, spectrum in scenes:
        key = module+'_gl'
        presets = ()
        if module == 'lava_horizon':
            from .satellite_camera import camera_presets
            presets = camera_presets()
        registry.add_builtin(ContentEntry(key, 'scene', name, 'builtin.gl', 'scene.'+key,
            key+'_reactive', lazy_factory('idle.gl.'+module, cls), module+'.frag',
            transport, spectrum, module == 'lava_horizon',
            camera_presets=presets,
            supports_extreme=(module == 'lava_horizon')))
    for name, key, cls in (('Orbital Atlas', 'orbital_atlas', 'HolographicOrbitWindow'),
                           ('Reactor Core', 'reactor_core', 'ReactorCoreWindow')):
        registry.add_builtin(ContentEntry(key, 'projection', name, 'builtin.projection_window',
            'settings.projection.'+key, factory=lazy_factory('projection.controller', cls)))

