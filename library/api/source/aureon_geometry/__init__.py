"""Optional, lazy mesh AURS host. No Qt/OpenGL imports during stable startup."""
import os

FEATURE='scene.mesh.experimental.v1'
LIBRARY='aurs.geometry.experimental'

def enabled():
    return os.environ.get('AUREON_DISABLE_GEOMETRY_AURS') != '1'
