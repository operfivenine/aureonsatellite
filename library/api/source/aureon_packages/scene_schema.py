"""AURS API 1: one fragment pass, bounded numeric behavior, host-owned uniforms."""
from .limits import LIMITS

from dataclasses import dataclass
import re
from .schema import obj, number, compile_signals
from .expressions import Expression, PackageError, AUDIO
from .shader_library import resolve_libraries

RESERVED = {'u_resolution':'vec2', 'u_mouse':'vec2', 'u_time':'float',
            'u_zones0':'vec4', 'u_zones1':'vec4'}
RESERVED.update({'u_audio_'+name:'float' for name in AUDIO})


@dataclass(frozen=True)
class SceneDefinition:
    source: str
    quality: dict
    signals: tuple
    uniforms: dict
    behavior: dict | None = None
    libraries: tuple = ()
    textures: tuple = ()
    lights: tuple = ()
    event_array_size: int = 8


def scene(data, resources, profile=1):
    from .scene_v2_schema import ARRAYS, UNIFORMS, behavior, compile_signals_v2, loop_limits
    from .expressions import V2_FUNCTIONS, AUDIO_V2, RUNTIME_V2
    reserved = dict(RESERVED)
    if profile == 2:
        reserved.update(UNIFORMS)
        reserved.update({'u_audio_'+name:'float' for name in AUDIO_V2})
    obj(data, ('shader','quality','signals','uniforms') + (('behavior','libraries','textures','lights') if profile == 2 else ()), ('shader',))
    from .textures import textures
    texture_specs = textures(data.get('textures', {}), resources) if profile == 2 else ()
    reserved.update({t.name: 'sampler2D' for t in texture_specs})
    shader = data['shader']
    if shader != 'shaders/main.frag' or shader not in resources:
        raise PackageError('AURS requires shaders/main.frag')
    raw = resources[shader]
    if len(raw) > LIMITS["shader_bytes"]: raise PackageError('Fragment shader exceeds 12800 KiB')
    try: source = raw.decode('utf-8-sig')
    except UnicodeError as exc: raise PackageError('Shader must be UTF-8') from exc
    if '\x00' in source or '\\' in source: raise PackageError('Unsupported shader source characters')
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    if not re.match(r'\s*#version\s+330\s+core\s*\n', source):
        raise PackageError('Shader must start with #version 330 core')
    directives = re.findall(r'^\s*#([^\n]*)', clean, re.M)
    if len(directives) != 1 or directives[0].strip() != 'version 330 core':
        raise PackageError('Only #version is allowed; use scene.json for quality defines')
    operation_source = re.sub(r'\buniform\s+sampler2D\s+u_tex_[A-Za-z0-9_]+\s*;', '', clean) if profile == 2 else clean
    if re.search(r'\b(while|do|discard|buffer|shared|atomic_uint|layout)\b|\b(?:[iu]?sampler|image|atomic)\w*\b',operation_source):
        raise PackageError('Unsupported shader operation in the single-pass profile')
    if not re.search(r'\bvoid\s+main\s*\(\s*(?:void\s*)?\)',clean):
        raise PackageError('Fragment main() is missing')
    requested_libraries = data.get('libraries', [])
    if profile == 2 and 'lights' in data:
        if not isinstance(requested_libraries,list): raise PackageError('libraries must be a list')
        requested_libraries = list(requested_libraries)
        if 'experimental.scene_lights' not in requested_libraries:
            requested_libraries.append('experimental.scene_lights')
        if re.search(r'\b(?:u_lightcfg_|aur_light_)[A-Za-z0-9_]*\b', clean):
            # Calls to generated accessors are allowed; their definitions are host-owned.
            if re.search(r'\bu_lightcfg_[A-Za-z0-9_]*\b|\bAurSceneLight\s+aur_light_[A-Za-z0-9_]+\s*\(',clean):
                raise PackageError('Generated light uniforms and accessors are reserved')
    libraries = resolve_libraries(requested_libraries) if profile == 2 else ()
    if libraries and re.search(r'\b(?:void|float|int|bool|vec[234]|mat[234])\s+aur_[A-Za-z0-9_]+\s*\(', clean):
        raise PackageError('The aur_ function namespace is reserved for the AURS Standard Library')
    quality = {}
    raw_quality = data.get('quality', {})
    obj(raw_quality, ('low','medium','high','extreme') if profile == 2 else ('low','medium','high'))
    for level in (('low','medium','high','extreme') if 'extreme' in raw_quality else ('low','medium','high')):
        spec = obj(raw_quality.get(level, {'defines':{}}), ('defines',))
        defines = spec.get('defines', {})
        if not isinstance(defines,dict) or len(defines)>LIMITS["quality_defines"]: raise PackageError('Too many quality defines')
        quality[level] = {}
        for name,value in defines.items():
            if not re.fullmatch(r'[A-Z][A-Z0-9_]{0,47}',name) or name.startswith('GL_') or '__' in name:
                raise PackageError('Invalid quality define')
            if type(value) is not int: raise PackageError('Quality defines must be integers')
            quality[level][name]=int(number(value,1,LIMITS["loop_iterations"]))
    if any(set(v)!=set(quality['low']) for v in quality.values()):
        raise PackageError('Quality levels must declare identical define names')
    if profile == 2:
        loop_limits(clean, quality)
    else:
        # This profile allows only canonical finite for loops; it is not a GPU sandbox.
        headers = re.findall(r'\bfor\s*\(([^)]*)\)',clean)
        if len(headers)!=len(re.findall(r'\bfor\b',clean)) or len(headers)>LIMITS["v1_loops"]:
            raise PackageError('Unsupported shader loop')
        total = 1
        for header in headers:
            match = re.fullmatch(r'\s*int\s+([a-zA-Z_]\w*)\s*=\s*0\s*;\s*\1\s*<\s*(\d+|[A-Z][A-Z0-9_]*)\s*;\s*(?:\1\s*\+\+|\+\+\s*\1)\s*',header)
            if not match: raise PackageError('Only bounded integer for loops are supported')
            limit = match[2]
            bounds = [int(limit)] if limit.isdigit() else [q.get(limit,0) for q in quality.values()]
            if not all(1<=b<=LIMITS["loop_iterations"] for b in bounds): raise PackageError('Invalid loop bound')
            total *= max(bounds)
        if total > LIMITS["v1_loop_budget"]: raise PackageError('Shader loop budget exceeded')
    signals = data.get('signals', {})
    ordered = compile_signals_v2(signals) if profile == 2 else compile_signals(signals)
    uniforms = data.get('uniforms', {})
    if not isinstance(uniforms,dict) or len(uniforms)>LIMITS["uniforms"]: raise PackageError('At most 4800 custom uniforms')
    compiled = {}
    for name,spec in uniforms.items():
        if not re.fullmatch(r'u_[a-zA-Z][a-zA-Z0-9_]{0,47}',name) or name in reserved or (profile == 2 and name in ARRAYS) or name.startswith(('u_audio_', 'u_lightcfg_')):
            raise PackageError('Invalid or reserved uniform name: '+str(name))
        expected = None
        if isinstance(spec,dict):
            obj(spec,('type','source'),('type','source'))
            expected=spec['type']; spec=spec['source']
        values = spec if isinstance(spec,list) else [spec]
        if not 1 <= len(values) <= 4: raise PackageError('Uniform must be float/vec2/vec3/vec4')
        kind = 'float' if len(values)==1 else 'vec'+str(len(values))
        if expected is not None and expected != kind: raise PackageError('Uniform type/source mismatch')
        compiled[name] = (kind,tuple(Expression(v,signals,functions=V2_FUNCTIONS, audio_channels=AUDIO_V2, runtime_channels=RUNTIME_V2) if profile == 2 else Expression(v,signals) for v in values))
    declarations = re.findall(r'\buniform\s+(\w+)\s+(\w+)\s*(?:\[\s*(\d+)\s*\])?\s*;',clean)
    if len(declarations) != len(re.findall(r'\buniform\b',clean)):
        raise PackageError('Unsupported uniform declaration')
    declared = {}
    event_array_size = 8
    behavior_config = behavior(data, signals) if profile == 2 else None
    event_slots = sum(event['slots'] for event in behavior_config['events']) if behavior_config else 0
    for kind,name,count in declarations:
        if count:
            if profile == 2 and name == 'u_events' and kind == 'vec4' and 1 <= int(count) <= LIMITS['event_slots']:
                event_array_size = int(count)
                if event_slots > event_array_size:
                    raise PackageError('u_events array must cover the declared event slots')
            elif profile != 2 or ARRAYS.get(name) != (kind,int(count)):
                raise PackageError('Only reserved AURS v2 arrays are supported')
        else:
            expected = reserved.get(name) or (compiled[name][0] if name in compiled else None)
            if expected != kind: raise PackageError('Unknown or incorrectly typed uniform: '+name)
        if name in declared: raise PackageError('Duplicate uniform: '+name)
        declared[name]=kind
    if set(compiled)-set(declared): raise PackageError('A custom uniform is missing from the shader')
    if {t.name for t in texture_specs}-set(declared): raise PackageError('Texture sampler missing from shader')
    light_specs=()
    if profile == 2 and 'lights' in data:
        from .lights_config import compile_lights
        light_uniforms,light_glsl,light_specs=compile_lights(data['lights'],signals)
        if len(compiled)+len(light_uniforms)>LIMITS["uniforms"]:
            raise PackageError('Custom uniforms and generated light uniforms exceed 4800 entries')
        compiled.update(light_uniforms)
        lines=source.splitlines(keepends=True)
        insertion=next(i for i,line in enumerate(lines) if line.lstrip().startswith('#version'))+1
        lines.insert(insertion,'\n'+light_glsl)
        source=''.join(lines)
    return SceneDefinition(source, quality, ordered, compiled, behavior_config, libraries, texture_specs, light_specs, event_array_size)
