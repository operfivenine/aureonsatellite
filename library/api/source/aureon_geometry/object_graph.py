"""Optional bounded mesh tree. Data only; shared geometry, no package code."""
import math,re,time
from dataclasses import dataclass
import numpy as np
from PySide6.QtGui import QMatrix4x4,QVector3D
from aureon_packages.schema import obj,number
from aureon_packages.expressions import PackageError
from .extensions import expr

FEATURE='scene.mesh_objects.experimental.v1'

@dataclass(frozen=True)
class GraphDefinition:
    templates:dict
    nodes:tuple
    lights:tuple
    order:tuple
    expressions:dict
    lighting:dict|None=None

def compile_graph(data,features):
    from .schema import vector,integer
    raw=data.get('object_graph')
    templates_in_batches=any(b.get('template',False) for q in data['quality'].values() for b in q['batches'])
    if raw is None:
        if templates_in_batches:raise PackageError('Templates require object_graph')
        return None
    if FEATURE not in features:raise PackageError('Missing mesh objects feature')
    obj(raw,('templates','nodes','lights','lighting'),('templates','nodes','lights'))
    from .light_selection import compile_lighting,FEATURE as LIGHT_FEATURE
    lighting=compile_lighting(raw.get('lighting'),features)
    templates=raw['templates'];nodes=raw['nodes'];lights=raw['lights'];expressions={}
    def identifier(v):
        if not isinstance(v,str) or not re.fullmatch('[a-z][a-z0-9_]{0,47}',v):raise PackageError('Invalid object ID')
    if not isinstance(templates,dict) or not 1<=len(templates)<=24:raise PackageError('1..24 mesh templates required')
    refs={q:set() for q in data['quality']}
    for name,indices in templates.items():
        identifier(name);obj(indices,('low','medium','high'),('low','medium','high'))
        for quality,index in indices.items():
            batches=data['quality'][quality]['batches'];integer(index,0,len(batches)-1);b=batches[index]
            if index in refs[quality] or not b.get('template',False) or 'animation' in b or b['mode']!='triangles' or b['blend']:
                raise PackageError('Templates require unique opaque static triangle batches')
            if b['model']!=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]:raise PackageError('Template model must be identity')
            refs[quality].add(index)
    for quality,q in data['quality'].items():
        if refs[quality]!={i for i,b in enumerate(q['batches']) if b.get('template',False)}:raise PackageError('Unused template batch')
    if not isinstance(nodes,list) or not 1<=len(nodes)<=2048:raise PackageError('1..2048 object nodes required')
    lookup={}
    for i,n in enumerate(nodes):
        obj(n,('id','parent','mesh','position','rotation','scale','tint','gain','distance','animation'),('id','position','rotation','scale','tint','gain','distance'))
        identifier(n['id'])
        if n['id'] in lookup:raise PackageError('Duplicate object ID')
        lookup[n['id']]=i
        if 'parent' in n:identifier(n['parent'])
        if 'mesh' in n:
            identifier(n['mesh'])
            if n['mesh'] not in templates:raise PackageError('Unknown mesh template')
        vector(n['position']);vector(n['rotation'],lo=-360,hi=360);number(n['scale'],.01,100)
        vector(n['tint'],lo=0,hi=2);vector(n['distance'],lo=1,hi=30000)
        if n['distance']!=sorted(n['distance']):raise PackageError('Distances must increase with quality')
        expressions[(i,'gain')]=expr(n['gain'],data.get('signals',{}))
        a=n.get('animation')
        if 'animation' in n:
            obj(a,('type','axis','angle','points','duration','phase','orient'),('type',))
            if a.get('type')=='rotate':
                obj(a,('type','axis','angle'),('type','axis','angle'));vector(a['axis'],lo=-1,hi=1)
                if sum(v*v for v in a['axis'])<1e-6:raise PackageError('Zero object rotation axis')
                expressions[(i,'angle')]=expr(a['angle'],data.get('signals',{}))
            elif a.get('type')=='path':
                obj(a,('type','points','duration','phase','orient'),('type','points','duration','phase','orient'))
                p=a['points']
                if not isinstance(p,list) or not 5<=len(p)<=33 or p[0]!=p[-1]:raise PackageError('Object path must close with 4..32 points')
                for v in p:vector(v)
                if any(sum((x-y)**2 for x,y in zip(v,w))<1 for v,w in zip(p,p[1:])):raise PackageError('Coincident object path points')
                number(a['duration'],10,600);number(a['phase'],0,1)
                if type(a['orient']) is not bool:raise PackageError('Path orient must be boolean')
            else:raise PackageError('Unknown object animation')
    order=[];visiting=set();done=set()
    def visit(i,depth):
        if depth>8 or i in visiting:raise PackageError('Object cycle or depth >8')
        if i in done:return
        visiting.add(i);parent=nodes[i].get('parent')
        if parent is not None:
            if parent not in lookup:raise PackageError('Unknown object parent')
            visit(lookup[parent],depth+1)
        visiting.remove(i);done.add(i);order.append(i)
    for i in range(len(nodes)):visit(i,0)
    # Validate actual ancestry even when a parent has already been sorted.
    for n in nodes:
        depth=0;p=n
        while 'parent' in p:
            depth+=1
            if depth>8:raise PackageError('Object depth >8')
            p=nodes[lookup[p['parent']]]
    # Bound composed transforms as well as individual fields. Uniform positive
    # scale keeps instanced normal transforms valid without an inverse per vertex.
    composed={};expanded=0;world_radius={};world_scale={}
    for i in order:
        n=nodes[i];m=QMatrix4x4();m.translate(*n['position'])
        for angle,axis in zip(n['rotation'],((1,0,0),(0,1,0),(0,0,1))):m.rotate(angle,*axis)
        m.scale(n['scale'])
        if 'parent' in n:m=composed[lookup[n['parent']]]*m
        a=np.array(m.data()).reshape(4,4).T
        if not np.isfinite(a).all() or not .0001<=np.linalg.norm(a[:3,0])<=1000 or np.max(abs(a[:3,3]))>30000:
            raise PackageError('Composed transform exceeds world budget')
        parent=lookup.get(n.get('parent'));local_radius=float(np.linalg.norm(n['position']))
        animation=n.get('animation',{})
        if animation.get('type')=='path':
            # Catmull-Rom can overshoot its control hull; 2x is conservative
            # for the sum of the absolute cubic basis coefficients.
            local_radius+=2*max(np.linalg.norm(p) for p in animation['points'])
        world_radius[i]=local_radius*(world_scale.get(parent,1))+world_radius.get(parent,0)
        world_scale[i]=n['scale']*world_scale.get(parent,1)
        if world_radius[i]>30000:raise PackageError('Animated hierarchy exceeds world budget')
        composed[i]=m
        if 'mesh' in n:
            expanded+=max(data['quality'][q]['batches'][index]['count'] for q,index in templates[n['mesh']].items())
    if expanded>2_000_000:raise PackageError('Expanded instances exceed 2 million vertices')
    if not isinstance(lights,list) or len(lights)>64:raise PackageError('At most 64 authored object lights')
    used=set()
    for i,l in enumerate(lights):
        obj(l,('id','parent','position','color','radius','gain','priority'),('id','parent','position','color','radius','gain'))
        identifier(l['id']);identifier(l['parent'])
        if l['id'] in used or l['parent'] not in lookup:raise PackageError('Duplicate light or unknown light parent')
        used.add(l['id']);vector(l['position']);vector(l['color'],lo=0,hi=2);number(l['radius'],1,400)
        if 'priority' in l:
            if lighting is None:raise PackageError('Light priority requires smooth lighting config')
            number(l['priority'],.1,4)
        expressions[(i,'light_gain')]=expr(l['gain'],data.get('signals',{}))
    used_meshes={n.get('mesh') for n in nodes}
    if not set(templates)<=used_meshes:raise PackageError('Unused mesh template')
    return GraphDefinition(templates,tuple(nodes),tuple(lights),tuple(order),expressions,lighting)

class ObjectGraph:
    def __init__(self,definition,scene,quality):
        self.definition=definition;self.scene=scene;self.quality=quality;self.tier=('low','medium','high').index(quality)
        self.lookup={n['id']:i for i,n in enumerate(definition.nodes)};self.world=[QMatrix4x4() for n in definition.nodes]
        self.base=[];self.gains=np.ones(len(self.world));self.groups={};self.light_values=[]
        self.visible=0;self.culled=0;self.draw_calls=0;self.submitted_vertices=0
        for i,n in enumerate(definition.nodes):
            m=QMatrix4x4();m.translate(*n['position'])
            for angle,axis in zip(n['rotation'],((1,0,0),(0,1,0),(0,0,1))):m.rotate(angle,*axis)
            m.scale(n['scale']);self.base.append(m)
            if 'mesh' in n:self.groups.setdefault(definition.templates[n['mesh']][quality],[]).append(i)
        self.radii={index:float(np.linalg.norm(scene.items[index].pos,axis=1).max()) for index in self.groups}
        from .light_selection import LightSlots
        self.light_slots=LightSlots(definition.lighting,quality) if definition.lighting else None
        self.light_stats={};self.scene_clock=0.
        self.dynamic=set()
        for i in definition.order:
            n=definition.nodes[i];parent=self.lookup.get(n.get('parent'))
            if 'animation' in n or parent in self.dynamic:self.dynamic.add(i)
            self.world[i]=self.base[i] if parent is None else self.world[parent]*self.base[i]
    def update(self,t):
        from .runtime import MeshScene
        self.scene_clock=t
        d=self.definition;c=self.scene.context
        for i in d.order:
            n=d.nodes[i];parent=self.lookup.get(n.get('parent'))
            self.gains[i]=max(0,min(4,d.expressions[(i,'gain')].value(c)*(1 if parent is None else self.gains[parent])))
            if i not in self.dynamic:continue
            local=QMatrix4x4();a=n.get('animation')
            if a and a['type']=='rotate':local.rotate(d.expressions[(i,'angle')].value(c)%360,*a['axis'])
            elif a:
                u=(t/a['duration']+a['phase'])%1;p=MeshScene.path_pose(a['points'],u);v=MeshScene.path_pose(a['points'],u+.0001)-p
                local.translate(*map(float,p))
                if a['orient']:
                    local.rotate(math.degrees(math.atan2(-v[0],v[1])),0,0,1)
                    local.rotate(math.degrees(math.atan2(v[2],np.linalg.norm(v[:2]))),1,0,0)
            local=self.base[i]*local if a and a['type']=='rotate' else local*self.base[i];self.world[i]=local if parent is None else self.world[parent]*local
        self.matrices=np.array([list(m.data()) for m in self.world],np.float32).reshape(-1,4,4).transpose(0,2,1)
        self.centers=self.matrices[:,:3,3];self.scales=np.linalg.norm(self.matrices[:,:3,0],axis=1)
        self.light_values=[]
        for i,l in enumerate(d.lights):
            idx=self.lookup[l['parent']];p=self.world[idx].map(QVector3D(*l['position']))
            gain=max(0,min(10,d.expressions[(i,'light_gain')].value(c)))
            self.light_values.append((np.array([p.x(),p.y(),p.z()]),l['color'],l['radius'],gain))
    def prepare(self,view,projection,geometry_only=False):
        inverse,ok=view.inverted();eye=inverse.map(QVector3D());eye=np.array([eye.x(),eye.y(),eye.z()])
        distances=np.linalg.norm(self.centers-eye,axis=1)
        clip=np.array(list((projection*view).data()),float).reshape(4,4).T
        planes=np.array([clip[3]+clip[0],clip[3]-clip[0],clip[3]+clip[1],clip[3]-clip[1],clip[3]+clip[2],clip[3]-clip[2]])
        planes/=np.linalg.norm(planes[:,:3],axis=1)[:,None]
        previous_stats=(self.visible,self.culled,self.draw_calls,self.submitted_vertices)
        self.visible=0;self.culled=0;self.draw_calls=0;self.submitted_vertices=0;packed={}
        for batch,indices in self.groups.items():
            idx=np.array(indices);radius=self.radii[batch]*self.scales[idx]
            limits=np.array([self.definition.nodes[i]['distance'][self.tier] for i in idx])
            visible=(distances[idx]-radius<limits)&np.all(self.centers[idx]@planes[:,:3].T+planes[:,3]>=-radius[:,None],axis=1)
            selected=idx[visible];self.visible+=len(selected);self.culled+=len(idx)-len(selected)
            if not len(selected):continue
            gain=np.array([self.definition.nodes[i]['tint']+[float(self.gains[i])] for i in selected],np.float32)
            packed[batch]=np.ascontiguousarray(np.column_stack((self.matrices[selected].transpose(0,2,1).reshape(-1,16),gain)),np.float32)
            self.draw_calls+=1;self.submitted_vertices+=len(selected)*len(self.scene.items[batch].pos)
        if geometry_only:
            self.visible,self.culled,self.draw_calls,self.submitted_vertices=previous_stats
            return packed,[]
        if self.light_slots:
            started=time.perf_counter_ns();reach=self.light_slots.reach;scores={};edge={}
            forward=inverse.mapVector(QVector3D(0,0,-1));focus=eye+np.array([forward.x(),forward.y(),forward.z()])*min(90,reach*.5)
            for i,(p,color,radius,gain) in enumerate(self.light_values):
                distance=np.linalg.norm(p-eye);range_end=radius+reach
                # Sphere intersects the camera frustum and its near field.
                if gain>0 and distance<range_end and np.all(planes[:,:3]@p+planes[:,3]>=-radius):
                    priority=self.definition.lights[i].get('priority',1)
                    score=priority/(1+(np.linalg.norm(p-focus)/radius)**2)
                    x=np.clip((range_end-distance)/max(20,reach*.3),0,1)
                    edge[i]=float(x*x*(3-2*x));scores[i]=float(score*edge[i])
            selected=self.light_slots.select(scores,self.scene_clock);lights=[]
            for i,weight in selected:
                if i is None:lights.append(((0.,0.,0.),(0.,0.,0.),1.,0.));continue
                p,color,radius,gain=self.light_values[i];q=view.map(QVector3D(*map(float,p)))
                # Retiring sources remain attached and continue their last
                # selection fade. Range fade itself is continuous at the boundary.
                distance=np.linalg.norm(p-eye);x=float(np.clip((radius+reach-distance)/max(20,reach*.3),0,1))
                gain*=weight*x*x*(3-2*x)
                lights.append(((q.x(),q.y(),q.z()),color,radius,gain))
            self.light_stats=dict(budget=self.light_slots.budget,candidates=len(scores),active=sum(l[3]>1e-5 for l in lights),
                ids=[self.definition.lights[i]['id'] if i is not None else None for i,_ in selected],weights=[w for _,w in selected],
                switches=self.light_slots.switches,selection_cpu_ms=(time.perf_counter_ns()-started)/1e6)
            return packed,lights
        candidates=[]
        for p,color,radius,gain in self.light_values:
            distance=np.linalg.norm(p-eye)
            if distance<radius+250 and gain>0:candidates.append((distance/max(1,radius),p,color,radius,gain))
        chosen=sorted(candidates,key=lambda a:a[0])[:(1,2,4)[self.tier]]
        lights=[]
        for _,p,color,radius,gain in chosen:
            q=view.map(QVector3D(*map(float,p)));lights.append(((q.x(),q.y(),q.z()),color,radius,gain))
        return packed,lights
