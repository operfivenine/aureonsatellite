"""Internal content contracts. No package code is imported by this subsystem."""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ContentEntry:
    id: str
    kind: str
    name: str
    renderer: str
    label_key: str = ''
    reactive_id: str = ''
    factory: Callable | None = None
    fragment: str = ''
    transport: bool = False
    spectrum_method: str = ''
    shader_cache: bool = False
    source: str = 'builtin'
    revision: str = ''
    names: tuple = ()
    camera_presets: tuple = ()
    supports_extreme: bool = False


@dataclass(frozen=True)
class SceneFrame:
    audio: object
    playing: bool | None
    audio_mode: bool
    visualizer: str


class BuiltinSceneRuntime:
    """Compatibility adapter: scene-specific hooks live outside the GL host."""
    def __init__(self, entry, quality, reactive):
        self.entry = entry
        self.scene = entry.factory(quality, reactive)

    def update(self, dt, frame):
        if self.entry.transport:
            self.scene.set_transport(frame.playing, frame.audio_mode)
        if self.entry.spectrum_method:
            getattr(self.scene, self.entry.spectrum_method)(frame.visualizer == 'spectrum')
        self.scene.advance(dt, frame.audio)

    def uniforms(self):
        return self.scene.uniforms()

    def __getattr__(self, name):
        # Built-in camera-capable scenes expose the same trusted controls as AURS.
        scene = self.__dict__.get('scene')
        if scene is None: raise AttributeError(name)
        return getattr(scene, name)
