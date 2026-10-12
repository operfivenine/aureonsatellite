"""Strict AURP API 1 subset; unknown requirements fail before installation."""
from .limits import LIMITS, dependency_order

from dataclasses import dataclass
import re
from .expressions import Expression, PackageError
from .aurp_standard_library import AURP_STANDARD_LIBRARY_FEATURE, resolve_libraries as resolve_aurp_libraries, expression_functions as aurp_expression_functions

PRIMITIVES = {'group', 'line', 'polyline', 'polygon', 'ellipse', 'ring', 'arc', 'radial_glow', 'image', 'hologram'}
HOLOGRAM_FEATURE = 'projection.hologram.experimental.v1'
LIGHT_FEATURE = 'projection.light_canvas.experimental.v1'
FEATURES = {'projection.surface.experimental.v2', 'projection.spectrum64.experimental.v2', 'projection.gyro_rings.experimental.v1',
            'behavior.expression.v1', 'behavior.integrator.v1', 'behavior.envelope.v1',
            'projection.gradient.v1', 'projection.transform.v1',
            AURP_STANDARD_LIBRARY_FEATURE, HOLOGRAM_FEATURE, LIGHT_FEATURE} | {'projection.'+p+'.v1' for p in PRIMITIVES if p != 'hologram'}
SCENE_FEATURES = {'scene.fullscreen_frag.v1', 'scene.quality.v1', 'scene.uniforms.v1',
                  'behavior.expression.v1', 'behavior.integrator.v1', 'behavior.envelope.v1'}
CAPABILITIES = {'audio.reactive.v1', 'audio.spectrum.v1', 'audio.events.v1', 'time.elapsed.v1'}


def obj(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise PackageError('Missing or unsupported fields: '+', '.join(sorted(set(value) - set(allowed)) if isinstance(value, dict) else ['object expected']))
    return value


def number(value, low, high):
    if type(value) not in (int, float) or not low <= value <= high:
        raise PackageError(f'Number must be within {low}..{high}')
    return float(value)


def text(value, limit=160):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 for c in value):
        raise PackageError('Invalid text value')
    return value


def color(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', value):
        raise PackageError('Color must be #RRGGBB or #AARRGGBB')
    return value


def requirements(value, supported):
    obj(value, ('required', 'optional'))
    for mode in ('required', 'optional'):
        items = value.get(mode, [])
        if not isinstance(items, list) or len(items) > 64 or any(not isinstance(x, str) for x in items):
            raise PackageError('Invalid feature/capability list')
        missing = set(items) - supported
        if mode == 'required' and missing:
            raise PackageError('Unsupported requirements: '+', '.join(sorted(missing)))


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{1,5}\.\d{1,5}\.\d{1,5}', value):
        raise PackageError('Version must have the form 1.0.0')
    return tuple(map(int, value.split('.')))


def manifest(data, app_version, kind='projection'):
    obj(data, ('format', 'package_type', 'format_version', 'id', 'version', 'name', 'author',
               'engine', 'renderer', 'entry', 'features', 'capabilities', 'parameters', 'preview'),
              ('format', 'package_type', 'format_version', 'id', 'version', 'name', 'engine', 'renderer', 'entry'))
    if 'preview' in data and (kind != 'scene' or data['preview'] != 'preview.png'):
        raise PackageError('Scene preview must be preview.png')
    renderer = 'projection.canvas.v1' if kind == 'projection' else 'scene.fullscreen_frag.v1'
    entry_point = 'projection.json' if kind == 'projection' else 'scene.json'
    if (kind not in ('projection', 'scene') or data['format'] != 'aureon.theme' or data['package_type'] != kind
        or type(data['format_version']) is not int or data['format_version'] != 1
        or data['renderer'] not in ((renderer,'scene.fullscreen_frag.v2','scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1') if kind == 'scene' else (renderer,'projection.surface.experimental.v2')) or data['entry'] != entry_point):
        raise PackageError('Unsupported package format, renderer or entry point')
    if not isinstance(data['id'], str) or not re.fullmatch(r'[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,7}', data['id']) or len(data['id']) > 120:
        raise PackageError('Package ID must be a lowercase dotted identifier')
    version(data['version'])
    names = data['name']
    if not isinstance(names, dict) or not 1 <= len(names) <= 16 or 'en' not in names:
        raise PackageError('A localized name with an English fallback is required')
    for lang, name in names.items():
        if not re.fullmatch(r'[a-z]{2,3}(?:-[a-z]{2,4})?', lang):
            raise PackageError('Invalid name language')
        text(name)
    engine = obj(data['engine'], ('api_major', 'min_aureon'), ('api_major',))
    if type(engine['api_major']) is not int or engine['api_major'] != 1:
        raise PackageError('Unsupported engine API')
    if 'min_aureon' in engine and version(engine['min_aureon']) > version(app_version):
        raise PackageError('This package requires a newer Aureon version')
    if 'author' in data:
        text(obj(data['author'], ('name',), ('name',))['name'])
    scene_features = SCENE_FEATURES | ({'scene.fullscreen_frag.v2', 'scene.spectrum.v2', 'behavior.events.v2', 'behavior.modes.v2',
                                      'behavior.temporal.v2', 'behavior.history.v2', 'behavior.state.v2',
                                      'behavior.camera.v2', 'scene.camera_presets.experimental.v1', 'scene.camera_manual.experimental.v1', 'behavior.presets.v2', 'behavior.math.v2',
                                      'behavior.transport.v1', 'scene.shaderlib.v1', 'scene.environment_core.v1',
                                      'scene.standard_library.v1', 'scene.object_core.v1', 'scene.lighting_rig.v1', 'scene.atmosphere_core.v1', 'scene.motion_core.v1', 'scene.presentation_core.v1', 'scene.object_motion.v1', 'scene.attachments.v1', 'scene.instances.v1', 'scene.trails_lod.v1', 'scene.textures2d.experimental.v1', 'scene.texture_materials.experimental.v1', 'scene.normal_mapping.experimental.v1', 'scene.triplanar.experimental.v1', 'scene.scene_lights.experimental.v1', 'scene.lights_config.experimental.v1', 'scene.normal_filtering.experimental.v1', 'scene.preview.v1', 'scene.quality_extreme.experimental.v1'}
                                     if data['renderer'] == 'scene.fullscreen_frag.v2' else set())
    if data['renderer'] in ('scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1'):
        from aureon_geometry import enabled, FEATURE
        if not enabled(): raise PackageError('Geometry AURS module is disabled')
        scene_features = {FEATURE, 'scene.preview.v1', 'scene.quality.v1'}
        if data['renderer'] == 'scene.hybrid_mesh.experimental.v1':
            from aureon_geometry.extensions import FEATURES as MESH_EXTENSIONS
            scene_features |= MESH_EXTENSIONS
            scene_features |= {'scene.hybrid_mesh.experimental.v1', 'scene.standard_library.v1'}
            if not {'scene.hybrid_mesh.experimental.v1','scene.standard_library.v1'} <= set(data.get('features',{}).get('required',[])): raise PackageError('Hybrid requires its renderer and standard library features')
        if FEATURE not in data.get('features',{}).get('required',[]): raise PackageError('Mesh profile requires '+FEATURE)
    requirements(data.get('features', {}), FEATURES if kind == 'projection' else scene_features)
    requirements(data.get('capabilities', {}), CAPABILITIES)
    if data.get('parameters', {}) != {}:
        raise PackageError('Package parameters are not supported in this API profile')
    return data


def compile_signals(signals, *, functions=None, audio_channels=None, runtime_channels=()):
    """Compile the bounded expression graph shared by AURP and AURS API 1.

    Optional function/channel tables let opt-in host libraries extend the safe
    expression surface without changing the base package language.
    """
    if not isinstance(signals, dict) or len(signals) > LIMITS["signals"]:
        raise PackageError('At most 4800 signals are supported')
    for key in signals:
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,47}', key):
            raise PackageError('Invalid signal name')
    compiled = {}
    for key, spec in signals.items():
        obj(spec, ('type', 'expr', 'rate', 'wrap', 'initial', 'attack', 'release'))
        kind = spec.get('type', 'expression')
        if kind == 'expression':
            obj(spec, ('type', 'expr'), ('expr',))
            expr = Expression(spec['expr'], signals, functions=functions, audio_channels=audio_channels, runtime_channels=runtime_channels)
            compiled[key] = (kind, expr, 0.0, 0.0)
        elif kind == 'integrator':
            obj(spec, ('type', 'rate', 'wrap', 'initial'), ('rate',))
            compiled[key] = (kind, Expression(spec['rate'], signals, functions=functions, audio_channels=audio_channels, runtime_channels=runtime_channels),
                             number(spec.get('wrap', 360), .001, 100000),
                             number(spec.get('initial', 0), -100000, 100000))
        elif kind == 'envelope':
            obj(spec, ('type', 'expr', 'attack', 'release'), ('expr',))
            compiled[key] = (kind, Expression(spec['expr'], signals, functions=functions, audio_channels=audio_channels, runtime_channels=runtime_channels),
                             number(spec.get('attack', .04), .001, 60),
                             number(spec.get('release', .3), .001, 60))
        else:
            raise PackageError('Unsupported signal type: '+str(kind))
    return tuple((key, *compiled[key]) for key in dependency_order(
        compiled, lambda key: compiled[key][1].dependencies))


@dataclass(frozen=True)
class ProjectionDefinition:
    width: int
    height: int
    signals: tuple
    nodes: tuple
    libraries: tuple = ()
    supersample: int = 1
    bloom: float = 0.


def projection(data, assets):
    obj(data, ('canvas', 'signals', 'nodes', 'libraries'), ('canvas', 'nodes'))
    canvas = obj(data['canvas'], ('width', 'height', 'supersample', 'bloom'), ('width', 'height'))
    width, height = (int(number(canvas[k], 32, LIMITS["canvas_axis"])) for k in ('width', 'height'))
    supersample = canvas.get('supersample', 1)
    if type(supersample) is not int or not 1 <= supersample <= LIMITS["supersample"]:
        raise PackageError('Supersample must be an integer within 1..300')
    bloom = number(canvas.get('bloom', 0), 0, .8)
    libraries = resolve_aurp_libraries(data.get('libraries', []))
    functions = aurp_expression_functions(libraries)
    signals = data.get('signals', {})
    ordered = compile_signals(signals, functions=functions)

    def expr(v): return Expression(v, signals, functions=functions)
    def pair(v):
        if not isinstance(v, list) or len(v) != 2: raise PackageError('Expected a coordinate pair')
        return tuple(expr(x) for x in v)
    def paint(v):
        if v is None: return None
        if isinstance(v, str): return color(v)
        obj(v, ('type', 'start', 'end', 'center', 'radius', 'stops'), ('type', 'stops'))
        kind = v['type']
        if kind == 'linear':
            obj(v, ('type', 'start', 'end', 'stops'), ('start', 'end'))
            result = {'type':kind, 'start':pair(v['start']), 'end':pair(v['end'])}
        elif kind == 'radial':
            obj(v, ('type', 'center', 'radius', 'stops'), ('center', 'radius'))
            result = {'type':kind, 'center':pair(v['center']), 'radius':expr(v['radius'])}
        else: raise PackageError('Unknown gradient type')
        stops = v['stops']
        if not isinstance(stops, list) or not 2 <= len(stops) <= 12:
            raise PackageError('Gradient needs 2..12 stops')
        result['stops'] = []
        for stop in stops:
            if not isinstance(stop, list) or len(stop) != 2: raise PackageError('Invalid gradient stop')
            result['stops'].append((number(stop[0], 0, 1), color(stop[1])))
        if any(a[0] >= b[0] for a, b in zip(result['stops'], result['stops'][1:])):
            raise PackageError('Gradient stops must be strictly increasing')
        return result
    count = [0]
    holograms = [0]
    def nodes(items, depth=0):
        if not isinstance(items, list) or len(items) > LIMITS["projection_nodes"] or depth > LIMITS["projection_depth"]:
            raise PackageError('Projection node limit exceeded')
        result = []
        common = {'type', 'translate', 'rotation', 'scale', 'opacity', 'blend'}
        fields = {'group': {'nodes'}, 'line': {'start','end','color','width'},
                  'polyline': {'points','color','width'}, 'polygon': {'points','color','width','fill'},
                  'ellipse': {'center','rx','ry','color','width','fill'},
                  'ring': {'center','rx','ry','color','width'},
                  'arc': {'center','rx','ry','color','width','start_angle','span_angle'},
                  'radial_glow': {'center','radius','color','strength'},
                  'image': {'source','rect'},
                  'hologram': {'center','radius','model','primary','secondary','bass','mid','treble','energy','impact'}}
        for raw in items:
            if not isinstance(raw, dict) or raw.get('type') not in PRIMITIVES:
                raise PackageError('Unsupported projection primitive')
            kind = raw['type']
            obj(raw, common | fields[kind])
            count[0] += 1
            if count[0] > LIMITS["projection_nodes"]: raise PackageError('At most 12800 projection nodes')
            node = {'type':kind, 'translate':pair(raw.get('translate',[0,0])),
                    'rotation':expr(raw.get('rotation',0)), 'scale':pair(raw.get('scale',[1,1])),
                    'opacity':expr(raw.get('opacity',1)), 'blend':raw.get('blend','add')}
            if node['blend'] not in ('add','normal'): raise PackageError('Unsupported blend mode')
            if kind == 'group': node['nodes'] = nodes(raw.get('nodes',[]),depth+1)
            elif kind == 'hologram':
                holograms[0] += 1
                if holograms[0] > LIMITS["holograms"] or raw.get('model') not in ('planet','spectral'):
                    raise PackageError('At most 200 holograms; model must be planet or spectral')
                node.update(center=pair(raw.get('center')),radius=expr(raw.get('radius',64)),model=raw['model'],
                            primary=color(raw.get('primary','#62cfff')),secondary=color(raw.get('secondary','#a891ff')))
                for key,channel in (('bass','low'),('mid','mid'),('treble','high'),('energy','energy'),('impact','beat')):
                    node[key] = expr(raw.get(key,'audio.'+channel))
            elif kind == 'image':
                if raw.get('source') not in assets: raise PackageError('Missing image resource')
                rect = raw.get('rect')
                if not isinstance(rect,list) or len(rect)!=4: raise PackageError('Image needs a rectangle')
                node.update(source=raw['source'], rect=tuple(expr(x) for x in rect))
            else:
                node['color'] = color(raw.get('color','#90fff0'))
                node['width'] = expr(raw.get('width',1))
                node['fill'] = paint(raw.get('fill'))
                if kind == 'line':
                    node.update(start=pair(raw.get('start')), end=pair(raw.get('end')))
                elif kind in ('polygon','polyline'):
                    points=raw.get('points')
                    if not isinstance(points,list) or not 2 <= len(points) <= LIMITS["polygon_points"]:
                        raise PackageError('Invalid polygon points')
                    node['points']=tuple(pair(p) for p in points)
                else:
                    node['center']=pair(raw.get('center'))
                    if kind == 'radial_glow':
                        node.update(radius=expr(raw.get('radius',20)),strength=expr(raw.get('strength',1)))
                    else:
                        node.update(rx=expr(raw.get('rx',20)),ry=expr(raw.get('ry',20)))
                        if kind == 'arc':
                            node.update(start_angle=expr(raw.get('start_angle',0)), span_angle=expr(raw.get('span_angle',180)))
            result.append(node)
        return tuple(result)
    graph = nodes(data['nodes'])
    if not graph: raise PackageError('Projection has no nodes')
    return ProjectionDefinition(width, height, tuple(ordered), graph, libraries, supersample, bloom)
