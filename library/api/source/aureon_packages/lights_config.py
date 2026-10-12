"""Bounded declarative light config, lowered to existing expression uniforms."""
from .limits import LIMITS

from dataclasses import dataclass
import re
from .expressions import Expression, PackageError, V2_FUNCTIONS, AUDIO_V2, RUNTIME_V2
from .schema import obj

@dataclass(frozen=True)
class LightSpec:
    id: str
    kind: str
    space: str

def compile_lights(raw, signals):
    if not isinstance(raw,dict) or len(raw)>LIMITS["lights"]:
        raise PackageError('lights must be an object with at most 400 sources')
    uniforms={};glsl=[];specs=[]
    def vec(value,count,label):
        if not isinstance(value,list) or len(value)!=count:
            raise PackageError(label+' requires '+str(count)+' components')
        return value
    for name,s in raw.items():
        if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,23}',name):
            raise PackageError('Light id must be lowercase snake_case, max 24 chars')
        obj(s,('type','space','position','direction','color','intensity','radius','inner_angle','outer_angle','enabled'),('type',))
        kind=s['type'];space=s.get('space','world')
        if kind not in ('directional','point','spot') or space not in ('world','local'):
            raise PackageError('Invalid light type or space')
        enabled=s.get('enabled',1)
        if type(enabled) is bool:enabled=int(enabled)
        prefix='u_lightcfg_'+name
        values={
            prefix+'_p':vec(s.get('position',[0,0,0]),3,name+'.position')+[s.get('radius',1)],
            prefix+'_c':vec(s.get('color',[1,1,1]),3,name+'.color')+[s.get('intensity',1)],
            prefix+'_d':vec(s.get('direction',[0,-1,0]),3,name+'.direction')+[enabled],
            prefix+'_a':[s.get('inner_angle',20),s.get('outer_angle',35)]}
        for key,v in values.items():
            try:expressions=tuple(Expression(x,signals,functions=V2_FUNCTIONS,audio_channels=AUDIO_V2,runtime_channels=RUNTIME_V2) for x in v)
            except PackageError as exc:raise PackageError('Light '+name+': '+str(exc)) from exc
            typ='vec'+str(len(v));uniforms[key]=(typ,expressions)
            glsl.append('uniform '+typ+' '+key+';')
        p,c,d,a=(prefix+suffix for suffix in ('_p','_c','_d','_a'))
        if kind=='directional':ctor=f'aur_sceneDirectional({d}.xyz,{c}.xyz,{c}.w)'
        elif kind=='point':ctor=f'aur_scenePoint({p}.xyz,{c}.xyz,{c}.w,{p}.w)'
        else:ctor=f'aur_sceneSpot({p}.xyz,{d}.xyz,{c}.xyz,{c}.w,{p}.w,{a}.x,{a}.y)'
        signature='AurObjectPose pose' if space=='local' else ''
        body=f'AurSceneLight light={ctor}; light=aur_sceneLightGain(light,clamp({d}.w,0.0,1.0));'
        body+=' return aur_sceneLightAttach(light,pose);' if space=='local' else ' return light;'
        glsl.append(f'AurSceneLight aur_light_{name}({signature})'+'{'+body+'}')
        specs.append(LightSpec(name,kind,space))
    return uniforms,'\n'.join(glsl)+'\n',tuple(specs)
