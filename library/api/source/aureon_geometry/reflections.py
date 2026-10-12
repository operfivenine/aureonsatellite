"""Opt-in bounded planar reflection targets; no stable renderer dependencies."""
import math, logging
from PySide6.QtGui import QMatrix4x4, QVector3D
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
from aureon_packages.schema import obj, number
from aureon_packages.expressions import PackageError

FEATURE='scene.mesh_reflections.experimental.v1'
SAMPLERS=('u_reflection0','u_reflection1')

def compile_reflections(raw,features):
    if raw is None:return None
    if FEATURE not in features:raise PackageError('Missing planar reflection feature')
    from .schema import integer,vector
    obj(raw,('planes','quality'),('planes','quality'))
    planes=raw['planes']
    if not isinstance(planes,list) or not 1<=len(planes)<=3:raise PackageError('1..3 reflection planes required')
    for plane in planes:
        obj(plane,('equation','max_distance'),('equation','max_distance'))
        e=vector(plane['equation'],4);length=math.sqrt(sum(v*v for v in e[:3]))
        if abs(length-1)>1e-5:raise PackageError('Reflection plane normal must be unit length')
        number(plane['max_distance'],20,1500)
    q=obj(raw['quality'],('low','medium','high'),('low','medium','high'))
    previous=0
    for tier,limit in zip(('low','medium','high'),(0,1,2)):
        s=obj(q[tier],('passes','size'),('passes','size'))
        ceiling=4096 if 'scene.mesh_reflection_resolution.experimental.v1' in features else 1024
        integer(s['passes'],previous,limit);previous=s['passes'];integer(s['size'],128,ceiling)
        if s['size']%32:raise PackageError('Reflection size must be a multiple of 32')
    return raw

def mirror_matrix(e):
    n=e[:3];d=e[3]
    a=[[float(i==j)-2*n[i]*n[j] for j in range(3)]+[-2*d*n[i]] for i in range(3)]
    return QMatrix4x4(*(sum(a,[])+[0.,0.,0.,1.]))

class PlanarReflections:
    def __init__(self,config,quality):
        self.config=config;self.quality=quality;self.targets=[];self.records=[];self.disabled=False;self.force_off=False
        self.stats=dict(enabled=False,passes=0,targets=0,estimated_bytes=0,cpu_ms=0.,reason='')
    def select(self,view):
        if self.disabled or self.force_off:return []
        count=self.config['quality'][self.quality]['passes']
        inverse,ok=view.inverted()
        if not ok:return []
        eye=inverse.map(QVector3D());pos=(eye.x(),eye.y(),eye.z())
        forward=inverse.mapVector(QVector3D(0,0,-1));forward=(forward.x(),forward.y(),forward.z())
        choices=[]
        for i,p in enumerate(self.config['planes']):
            e=p['equation'];distance=sum(x*y for x,y in zip(pos,e[:3]))+e[3]
            facing=sum(x*y for x,y in zip(forward,e[:3]))
            if distance>.25 and distance<p['max_distance'] and facing<.15:
                choices.append((i,distance))
        # Ground is the first authored plane; prefer it when visible. Remaining
        # choices are deterministic, and never exceed the tier's pass budget.
        choices.sort(key=lambda p:(p[0]!=0,p[1],p[0]))
        return [i for i,_ in choices[:count]]
    def ensure(self,width,height):
        max_side=self.config['quality'][self.quality]['size']
        scale=min(1.,max_side/max(width,height));size=(max(1,round(width*scale)),max(1,round(height*scale)))
        count=self.config['quality'][self.quality]['passes']
        if self.targets and (self.targets[0].width(),self.targets[0].height())==size:return
        self.destroy();fmt=QOpenGLFramebufferObjectFormat();fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
        fmt.setInternalTextureFormat(0x8058);fmt.setSamples(0)
        for _ in range(count):
            fbo=QOpenGLFramebufferObject(*size,fmt)
            if not fbo.isValid():raise RuntimeError('Planar reflection framebuffer allocation failed')
            self.targets.append(fbo)
        self.stats.update(targets=len(self.targets),estimated_bytes=size[0]*size[1]*8*len(self.targets))
    def fail(self,error):
        self.disabled=True;self.destroy();self.stats.update(enabled=False,reason=str(error))
        logging.getLogger('aureon').warning('Planar reflection fallback to environment: %s',error)
    def destroy(self):
        self.records=[];self.targets.clear();self.stats.update(passes=0,targets=0,estimated_bytes=0)
