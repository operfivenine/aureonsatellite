"""Bounded declarative GPU surface extension. Packages contain no executable code."""
from dataclasses import dataclass
from .schema import obj, number, color
from .expressions import PackageError

RENDERER = 'projection.surface.experimental.v2'
FEATURE = RENDERER
SPECTRUM_FEATURE = 'projection.spectrum64.experimental.v2'
GYRO_FEATURE = 'projection.gyro_rings.experimental.v1'

@dataclass(frozen=True)
class SurfaceDefinition:
    width: int
    height: int
    detail: int
    amplitude: float
    glow: float
    intensity: float
    primary: str
    secondary: str
    accent: str
    tilt: float
    yaw: float
    model: str = 'spectral_landscape'

def projection_surface(data):
    obj(data, ('canvas','surface','palette','camera'), ('canvas','surface'))
    canvas=obj(data['canvas'], ('width','height'), ('width','height'))
    # The new GPU path has its own finite framebuffer budget, independent of
    # the historic expanded Canvas capacities.
    width,height=(int(number(canvas[k],64,512)) for k in ('width','height'))
    surface=obj(data['surface'], ('model','detail','amplitude','glow','intensity'), ('model',))
    if surface['model'] not in ('spectral_landscape','gyro_rings'):raise PackageError('Unknown AURP surface model')
    detail=surface.get('detail',48)
    if type(detail) is not int or not 16<=detail<=64:raise PackageError('Surface detail must be an integer 16..64')
    palette=obj(data.get('palette',{}), ('primary','secondary','accent'))
    camera=obj(data.get('camera',{}), ('tilt','yaw'))
    return SurfaceDefinition(width,height,detail,number(surface.get('amplitude',1),.2,1.5),
        number(surface.get('glow',.5),0,1),number(surface.get('intensity',1),.2,1.5),
        color(palette.get('primary','#41d7ff')),color(palette.get('secondary','#795afa')),
        color(palette.get('accent','#ff548f')),number(camera.get('tilt',48),25,70),
        number(camera.get('yaw',-12),-35,35),surface['model'])
