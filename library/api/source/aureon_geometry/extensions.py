"""MAB01 bounded materials, shared signals and declarative object animation."""
import ast,re
from dataclasses import dataclass
from aureon_packages.schema import obj,number
from aureon_packages.expressions import Expression,PackageError,V2_FUNCTIONS,RUNTIME_V2

MATERIAL_FEATURE='scene.mesh_materials.experimental.v1'
ANIMATION_FEATURE='scene.mesh_animation.experimental.v1'
BINDING_FEATURE='scene.mesh_bindings.experimental.v1'
FEATURES={'scene.mesh_reflection_resolution.experimental.v1','scene.mesh_camera_settings.experimental.v1','scene.mesh_transparency.experimental.v1','scene.mesh_reflections.experimental.v1','scene.mesh_light_selection.experimental.v1','scene.mesh_objects.experimental.v1',MATERIAL_FEATURE,ANIMATION_FEATURE,BINDING_FEATURE,'scene.textures2d.experimental.v1'}
CHANNELS={'low','mid','high','energy','beat','presence'}

def expr(value,names):
    return Expression(value,names,functions=V2_FUNCTIONS,audio_channels=CHANNELS,runtime_channels=RUNTIME_V2)

def _supported(expression):
    for node in ast.walk(expression.tree):
        if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='audio' and node.attr not in CHANNELS:
            raise PackageError('Hybrid does not supply audio.'+node.attr)

@dataclass(frozen=True)
class Extensions:
    textures:tuple
    materials:dict
    uniform_types:dict
    signals:dict
    bindings:dict
    animations:dict

def compile_extensions(data,resources,hybrid,features):
    from .schema import vector,integer
    requested=set(features)
    def require(feature):
        if not hybrid or feature not in requested:raise PackageError('Requires Hybrid feature '+feature)
    specs=data.get('textures',{});materials=data.get('materials',{});signals=data.get('signals',{})
    if specs or materials:require(MATERIAL_FEATURE)
    if specs:require('scene.textures2d.experimental.v1')
    if signals:require(BINDING_FEATURE)
    if not isinstance(signals,dict) or len(signals)>32:raise PackageError('Hybrid allows up to 32 shared signals')
    from aureon_packages.scene_v2_schema import compile_signals_v2
    for signal in compile_signals_v2(signals):
        if signal.kind not in ('expression','envelope','integrator','gate','spring'):raise PackageError('Unsupported Hybrid signal primitive')
        _supported(signal.expr)
    if not isinstance(specs,dict) or len(specs)>8:raise PackageError('Hybrid allows up to 8 textures')
    # Bound this prototype before invoking the unchanged standard decoder.
    from PySide6.QtCore import QBuffer,QByteArray,QIODevice
    from PySide6.QtGui import QImageReader
    budget=0
    for spec in specs.values():
        if not isinstance(spec,dict) or spec.get('source') not in resources:raise PackageError('Missing Hybrid texture')
        raw=resources[spec['source']]
        if len(raw)>8*1024*1024:raise PackageError('Hybrid texture file exceeds 8 MiB')
        buffer=QBuffer();buffer.setData(QByteArray(raw));buffer.open(QIODevice.ReadOnly)
        size=QImageReader(buffer).size();w,h=size.width(),size.height()
        if not 1<=w<=2048 or not 1<=h<=2048:raise PackageError('Hybrid texture axes must be 1..2048')
        budget+=w*h*4*(4/3 if spec.get('mipmaps',True) else 1)
        if budget>64*1024*1024:raise PackageError('Hybrid textures exceed 64 MiB including mipmaps')
    from aureon_packages.textures import textures
    tex=textures(specs,{k:v for k,v in resources.items() if k.startswith('textures/')}) if specs else ()
    if not isinstance(materials,dict) or len(materials)>24:raise PackageError('Hybrid allows up to 24 materials')
    compiled={};types={}
    for name,material in materials.items():
        if not re.fullmatch('[a-z][a-z0-9_]{0,31}',name):raise PackageError('Invalid material ID')
        obj(material,('uniforms',),('uniforms',));uniforms=material['uniforms']
        if not isinstance(uniforms,dict) or len(uniforms)>12:raise PackageError('At most 12 uniforms per material')
        entry={}
        for key,source in uniforms.items():
            if not re.fullmatch('u_mat_[a-zA-Z][a-zA-Z0-9_]{0,31}',key):raise PackageError('Material uniforms require u_mat_ prefix')
            values=source if isinstance(source,list) else [source]
            if not 1<=len(values)<=4:raise PackageError('Material uniform must be float/vec2/vec3/vec4')
            kind='float' if len(values)==1 else 'vec'+str(len(values))
            if key in types and types[key]!=kind:raise PackageError('Material uniform type mismatch')
            types[key]=kind;entry[key]=tuple(expr(v,signals) for v in values)
        compiled[name]=entry
    if len(types)>12:raise PackageError('Hybrid material program allows up to 12 distinct uniforms')
    bindings={};animations={}
    for quality,q in data['quality'].items():
        for index,b in enumerate(q['batches']):
            if 'material' in b and (not isinstance(b['material'],str) or b['material'] not in compiled):raise PackageError('Unknown material ID')
            key=(quality,index)
            if 'bindings' in b:
                require(BINDING_FEATURE);obj(b['bindings'],('emission_add','surface_gain','rim'))
                bindings[key]={name:expr(value,signals) for name,value in b['bindings'].items()}
            a=b.get('animation',{})
            if a.get('type')=='rotate':
                require(ANIMATION_FEATURE);obj(a,('type','axis','pivot','angle'),('type','axis','pivot','angle'))
                vector(a['axis'],lo=-1,hi=1);vector(a['pivot'])
                if sum(v*v for v in a['axis'])<.000001:raise PackageError('Rotation axis is zero')
                animations[key]=expr(a['angle'],signals)
            elif a.get('type')=='path':
                require(ANIMATION_FEATURE);obj(a,('type','points','duration','phase','orient'),('type','points','duration','phase','orient'))
                points=a['points']
                if not isinstance(points,list) or not 5<=len(points)<=33 or points[0]!=points[-1]:raise PackageError('Path must close and have 4..32 control points')
                for p in points:vector(p)
                for p,n in zip(points,points[1:]):
                    if sum((v-w)**2 for v,w in zip(p,n))<1:raise PackageError('Path contains coincident control points')
                number(a['duration'],10,600);number(a['phase'],0,1)
                if type(a['orient']) is not bool:raise PackageError('Path orient must be boolean')
    return Extensions(tex,compiled,types,signals,bindings,animations)
