"""Lazy GL registration; importing this package does not import QtOpenGL."""

from aureon_content import get_registry
from collections.abc import Set

GL_BASE_STYLES = tuple((e.name, e.id) for e in get_registry().entries('scene') if e.renderer == 'builtin.gl')
GL_REACTIVE_MAP = {e.id: e.reactive_id for e in get_registry().entries('scene') if e.renderer == 'builtin.gl' and e.reactive_id}


class _GLStyles(Set):
    # Compatibility view, not a frozen duplicate of the catalog.
    def __contains__(self, key):
        return get_registry().is_gl(key)

    def __iter__(self):
        for entry in get_registry().entries('scene'):
            if entry.renderer in ('builtin.gl', 'scene.fullscreen_frag.v1', 'scene.fullscreen_frag.v2', 'scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1'):
                yield entry.id
                if entry.reactive_id:
                    yield entry.reactive_id

    def __len__(self):
        return sum(1 for _ in self)


GL_STYLES = _GLStyles()


def _resolve_quality(parent, requested, previous=None):
    requested = str(requested or "auto").lower()
    if requested == "lowest":
        return "low"  # Keep existing shader/package tier numbering unchanged.
    if requested in ("low", "medium", "high", "extreme"):
        return requested
    resolver = getattr(parent, "auto_quality_selection", None)
    if callable(resolver):
        value = resolver()
        return "low" if value == "lowest" else value
    return "medium"


def create_scene_widget(parent, style):
    import os
    from PySide6.QtGui import QGuiApplication
    if os.environ.get("AUREON_DISABLE_GL") == "1":
        raise RuntimeError("OpenGL disabled by AUREON_DISABLE_GL")
    if QGuiApplication.platformName() in ("offscreen", "minimal"):
        raise RuntimeError("Platform does not support QOpenGLWidget")
    from .gl_scene_widget import GLSceneWidget
    # Environment override is kept for diagnostics; normal users are driven by
    # visual/quality through FloatingIdleSurface._gl_quality.
    env_quality = os.environ.get("AUREON_GL_QUALITY", "").lower()
    requested = env_quality if env_quality in ("lowest", "low", "medium", "high", "extreme") else getattr(parent, "_gl_quality", "auto")
    quality = _resolve_quality(parent, requested)
    advanced = getattr(parent, 'advanced_profile', lambda: {})()
    if advanced.get('detail') in ('low', 'medium', 'high', 'extreme'):
        quality = advanced['detail']
    from aureon_gl_diagnostics import record
    record('create',scene=style,quality=quality,requested=requested)
    entry = get_registry().resolve(style, 'scene')
    if quality == 'extreme' and entry and not entry.supports_extreme:
        quality = 'high'
    if entry and entry.renderer in ('scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1'):
        from aureon_geometry.widget import MeshWidget
        return MeshWidget(parent, quality, style)
    return GLSceneWidget(parent, quality, style)
