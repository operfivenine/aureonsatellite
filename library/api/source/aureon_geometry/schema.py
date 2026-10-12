"""Closed mesh data contract: binary floats, declarative animation, no Python."""
from dataclasses import dataclass
import re
import numpy as np
from aureon_packages.schema import obj,number,text
from aureon_packages.expressions import PackageError
from . import enabled,LIBRARY

MAX_VERTICES=2_000_000

def vector(v,n=3,lo=-30000,hi=30000):
    if not isinstance(v,list) or len(v)!=n: raise PackageError('Invalid vector length')
    return [number(x,lo,hi) for x in v]

def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi: raise PackageError('Invalid integer')
    return v

def shader(raw,samplers=()):
    if len(raw)>128*1024: raise PackageError('Mesh shader exceeds 128 KiB')
    source=raw.decode('utf-8-sig').replace('\r\n','\n')
    clean=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
    directives=re.findall(r'^\s*#([^\n]*)',clean,re.M)
    if directives!=['version 330 core'] or not re.match(r'\s*#version 330 core\s*\n',source):
        raise PackageError('Only GLSL 330 core is supported')
    if '\x00' in source or '\\' in source or re.search(r'\b(while|do|buffer|shared|atomic\w*|image\w*)\b',clean):
        raise PackageError('Unsupported mesh shader operation')
    declared=re.findall(r'\buniform\s+(sampler\w*)\s+(\w+)\s*;',clean)
    if any(kind!='sampler2D' or name not in samplers for kind,name in declared) or len(declared)!=len(re.findall(r'\bsampler\w*\b',clean)):
        raise PackageError('Only declared material sampler2D textures are supported')
    if set(samplers)!={name for _,name in declared}:raise PackageError('Material samplers must match texture resources')
    if not re.search(r'\bvoid\s+main\s*\(',clean): raise PackageError('Shader main missing')
    for loop in re.findall(r'for\s*\(([^)]*)\)',clean):
        if not re.fullmatch(r'\s*int\s+(\w+)\s*=\s*0\s*;\s*\1\s*<\s*(?:[1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])\s*;\s*(?:\1\+\+|\+\+\1)\s*',loop):
            raise PackageError('Shader loops must have a constant bound <=256')
    return source

@dataclass(frozen=True)
class MeshDefinition:
    document:dict
    quality:dict
    behavior:dict
    resources:dict
    sources:dict
    background:object=None
    extensions:object=None
    graph:object=None
    reflections:object=None

def compile_scene(data,resources,hybrid=False,features=()):
    if not enabled(): raise PackageError('Geometry AURS module is disabled')
    fields=('libraries','environment','quality','camera','statistics')
    obj(data,fields+(('hybrid','textures','materials','signals','object_graph','reflections') if hybrid else ()),fields+(('hybrid',) if hybrid else ()))
    if data['libraries']!=([LIBRARY,'aurs.standard'] if hybrid else [LIBRARY]): raise PackageError('Invalid mesh/hybrid libraries')
    env=obj(data['environment'],('fog_color','fog_density','ambient','planet_fill','fill_origin'),('fog_color','fog_density','ambient','planet_fill','fill_origin'))
    vector(env['fog_color'],lo=0,hi=1);vector(env['fill_origin'])
    number(env['fog_density'],0,.1);number(env['ambient'],0,1);number(env['planet_fill'],0,1)
    stats=obj(data['statistics'],('buildings','objects'),('buildings','objects'))
    integer(stats['buildings'],0,100000);integer(stats['objects'],0,1000000)
    camera=obj(data['camera'],('times','eyes','targets','fov','near','far','presets','micro_motion'),('times','eyes','targets','fov','near','far','presets'))
    if 'micro_motion' in camera:
        if not hybrid or 'scene.mesh_camera_settings.experimental.v1' not in features:
            raise PackageError('Camera micro motion requires scene.mesh_camera_settings.experimental.v1')
        number(camera['micro_motion'],0,1)
    times=camera['times']
    if not isinstance(times,list) or not 4<=len(times)<=128: raise PackageError('Invalid route')
    for value in times:number(value,0,3600)
    if times[0]!=0 or any(b-a<.05 for a,b in zip(times,times[1:])): raise PackageError('Invalid route times')
    for field in ('eyes','targets'):
        values=camera[field]
        if not isinstance(values,list) or len(values)!=len(times):raise PackageError('Invalid route vector count')
        for v in values:vector(v)
        if values[0]!=values[-1]:raise PackageError('Camera route must close')
    for eye,target in zip(camera['eyes'],camera['targets']):
        if sum((a-b)**2 for a,b in zip(eye,target))<1:raise PackageError('Camera eye and target must differ')
    number(camera['fov'],30,110);number(camera['near'],.05,5);number(camera['far'],100,40000)
    presets=camera['presets'];seen=set()
    if not isinstance(presets,list) or len(presets)>12:raise PackageError('Invalid camera presets')
    for p in presets:
        if not isinstance(p,list) or len(p)!=4:raise PackageError('Invalid camera preset')
        key=text(p[0],32);text(p[1],64);text(p[2],64);number(p[3],0,times[-1])
        if not re.fullmatch('[a-z][a-z0-9_]*',key) or key in seen or key=='auto':raise PackageError('Invalid camera preset ID')
        seen.add(key)
    quality=obj(data['quality'],('low','medium','high'),('low','medium','high'))
    required={'manifest.json','scene.json','preview.png','shaders/main.vert','shaders/main.frag'}
    for name,q in quality.items():
        obj(q,('mesh','batches'),('mesh','batches'))
        if q['mesh']!='meshes/'+name+'.bin':raise PackageError('Invalid mesh resource')
        required.add(q['mesh'])
        if q['mesh'] not in resources:raise PackageError('Missing mesh resource')
        raw=resources[q['mesh']]
        if len(raw)%40 or len(raw)>MAX_VERTICES*40:raise PackageError('Invalid mesh byte length/budget')
        arr=np.frombuffer(raw,dtype='<f4').reshape(-1,10)
        if not len(arr) or not np.isfinite(arr).all() or np.max(np.abs(arr[:,:3]))>30000 or np.max(np.abs(arr[:,7:]))>2:
            raise PackageError('Invalid mesh positions/normals')
        if arr[:,3:7].min()<0 or arr[:,3:7].max()>2:raise PackageError('Invalid vertex colors')
        batches=q['batches']
        if not isinstance(batches,list) or not 1<=len(batches)<=128:raise PackageError('Invalid batch count')
        cursor=0
        for b in batches:
            obj(b,('offset','count','mode','model','lit','emission','fog','rim','style','point_size','point_pixels','blend','blend_mode','depth','surface_gain','audio','animation','material','bindings','template'),
                ('offset','count','mode','model','lit','emission','fog','rim','style','point_size','point_pixels','blend','depth','surface_gain','audio'))
            if integer(b['offset'],0,MAX_VERTICES)!=cursor:raise PackageError('Mesh batches must exactly partition data')
            count=integer(b['count'],1,MAX_VERTICES);cursor+=count
            if b['mode'] not in ('triangles','lines','points') or (b['mode']=='triangles' and count%3) or (b['mode']=='lines' and count%2):raise PackageError('Invalid mesh primitive count')
            vector(b['model'],16,-30000,30000)
            if b['model'][12:16]!=[0,0,0,1]:raise PackageError('Model must be an affine matrix')
            for key,hi in (('lit',1),('emission',10),('fog',5),('rim',2),('style',7),('point_size',16),('point_pixels',16),('surface_gain',4)):
                number(b[key],0,hi)
            number(b['depth'],-1000,1000);vector(b['audio'],5,0,10)
            if type(b['blend']) is not bool:raise PackageError('Blend must be boolean')
            if 'blend_mode' in b:
                if not hybrid or 'scene.mesh_transparency.experimental.v1' not in features:
                    raise PackageError('Explicit blend mode requires scene.mesh_transparency.experimental.v1')
                if b['blend_mode'] not in ('alpha','additive') or not b['blend']:
                    raise PackageError('Explicit blend mode requires a blended batch and alpha/additive mode')
            if 'template' in b and type(b['template']) is not bool:raise PackageError('Template must be boolean')
            if 'animation' in b:
                a=obj(b['animation'],('type','speed','amplitude','axis','span','origin','phase','pivot','angle','points','duration','orient'),('type',))
                if a['type']=='drift':
                    obj(a,('type','speed','amplitude'),('type','speed','amplitude'))
                    number(a['speed'],.001,2);vector(a['amplitude'],lo=0,hi=40)
                    if b['mode']!='points' or count>10000:raise PackageError('Drift requires <=10000 points')
                elif a['type']=='shuttle':
                    obj(a,('type','speed','axis','span','origin','phase'),('type','speed','axis','span','origin','phase'))
                    number(a['speed'],.1,200);integer(a['axis'],0,2);number(a['span'],10,10000);vector(a['origin']);number(a['phase'],0,1)
                elif a['type'] not in ('rotate','path'):raise PackageError('Unknown animation type')
        if cursor!=len(arr):raise PackageError('Mesh batch length mismatch')
    from .extensions import compile_extensions
    extensions=compile_extensions(data,resources,hybrid,features)
    from .object_graph import compile_graph
    graph=compile_graph(data,features)
    from .reflections import compile_reflections,SAMPLERS
    reflections=compile_reflections(data.get('reflections'),features)
    required.update(t.path for t in extensions.textures)
    background=None
    if hybrid:
        config=obj(data['hybrid'],('background',),('background',))
        bg=obj(config['background'],('shader','libraries','quality','uniforms'),('shader','libraries','quality','uniforms'))
        if bg['shader']!='shaders/background.frag' or bg['libraries']!=['aurs.standard']:raise PackageError('Hybrid requires a standard-library background shader')
        required.add(bg['shader'])
        if bg['shader'] not in resources or len(resources[bg['shader']])>128*1024:raise PackageError('Missing/oversized hybrid shader')
        from aureon_packages.scene_schema import scene
        document=dict(bg,shader='shaders/main.frag')
        if extensions.signals:document['signals']=extensions.signals
        background=scene(document,{'shaders/main.frag':resources[bg['shader']].replace(b'\r\n',b'\n')},2)
        if not re.search(r'\bgl_FragDepth\s*=',background.source):raise PackageError('Hybrid background must explicitly write world depth')
        for name,kind in {'u_hyb_right':'vec3','u_hyb_up':'vec3','u_hyb_forward':'vec3','u_hyb_clip':'vec2'}.items():
            if name not in background.uniforms or background.uniforms[name][0]!=kind:raise PackageError('Hybrid camera contract requires '+name)
        if background.textures or background.behavior['camera']:raise PackageError('Hybrid uses the common camera/clock; separate camera and textures in the background are not supported')
    if set(resources)!=required:raise PackageError('Unsupported or unused mesh package resource')
    sources={'material.vert':shader(resources['shaders/main.vert']),'material.frag':shader(resources['shaders/main.frag'],tuple(t.name for t in extensions.textures)+(SAMPLERS if reflections else ())) }
    declared=dict((name,kind) for kind,name in re.findall(r'\buniform\s+(float|vec[234])\s+(u_mat_\w+)\s*;',sources['material.frag']))
    if declared!=extensions.uniform_types:raise PackageError('Material uniform declarations must match the material contract')
    if graph:
        for pattern in (r'layout\s*\(location\s*=\s*3\)\s*in\s+mat4\s+instanceModel',r'layout\s*\(location\s*=\s*7\)\s*in\s+vec4\s+instanceGain'):
            if not re.search(pattern,sources['material.vert']):raise PackageError('Missing instanced vertex attributes')
    if reflections:
        for name in ('u_reflection0_matrix','u_reflection1_matrix','u_inverse_view'):
            if not re.search(r'\buniform\s+mat4\s+'+name+r'\s*;',sources['material.frag']):raise PackageError('Missing reflection shader matrix '+name)
        for name in ('u_reflection_pass','u_reflection_plane','u_mesh_model'):
            if name not in sources['material.vert']:raise PackageError('Missing reflection vertex contract '+name)
    behavior={'camera':{'presets':tuple(tuple(p[:3])+ (index,) for index,p in enumerate(presets))}}
    return MeshDefinition(data,quality,behavior,{q['mesh']:resources[q['mesh']] for q in quality.values()},sources,background,extensions,graph,reflections)
