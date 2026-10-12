"""Generic mesh runtime. Packages provide all geometry and scene parameters."""
import math
from dataclasses import asdict
import numpy as np
from PySide6.QtGui import QMatrix4x4,QVector3D
from .gl_audio_bridge import AudioBridge,AudioSignals,analyzer_signals
from .gl_camera import Camera
from .utils.gl_items import GeometryItem

class ViewState:
    def __init__(self,camera,environment):
        self.items=[];self.opts={'center':QVector3D(),'distance':100.,'elevation':0.,'azimuth':0.,'fov':camera['fov']}
        self.camera=camera;self.fog_density=environment['fog_density'];self.fog_color=environment['fog_color'];self.glow=1.;self.scene_time=0.
    def addItem(self,item):self.items.append(item)
    def removeItem(self,item):self.items.remove(item)
    def setCameraPosition(self,pos=None,**values):
        if pos is not None:self.opts['center']=pos
        self.opts.update(values)
    def viewMatrix(self):
        matrix=QMatrix4x4();matrix.translate(0.,0.,-self.opts['distance'])
        matrix.rotate(self.opts['elevation']-90,1,0,0);matrix.rotate(self.opts['azimuth']+90,0,0,-1)
        c=self.opts['center'];matrix.translate(-c.x(),-c.y(),-c.z());return matrix
    def projectionMatrix(self,width,height):
        near=self.camera['near'];right=near*math.tan(math.radians(self.opts['fov']*.5));top=right*height/width
        matrix=QMatrix4x4();matrix.frustum(-right,right,-top,top,near,self.camera['far']);return matrix

class MeshScene:
    min_distance=8.
    def __init__(self,definition,quality,view):
        self.view=view;self.items=[];self.data=definition.document;self.route=self.data['camera']
        self.eye=self.route['eyes'][0];self.target=self.route['targets'][0]
        self.route_times=np.asarray(self.route['times']);self.loop_seconds=self.route_times[-1]
        self.route_eyes=np.asarray(self.route['eyes']);self.route_targets=np.asarray(self.route['targets'])
        q=definition.quality[quality];array=np.frombuffer(definition.resources[q['mesh']],'<f4').reshape(-1,10)
        self.descriptors=q['batches'];self.animations=[]
        self.context={'time':0.,'dt':0.,'pi':math.pi,'audio':{},'runtime':{},'signal':{}}
        self.extension=definition.extensions;self.quality=quality
        for b in self.descriptors:
            part=array[b['offset']:b['offset']+b['count']]
            item=GeometryItem(part[:,:3],part[:,3:7],part[:,7:],mode=b['mode'],**{k:b[k] for k in ('lit','emission','fog','rim','style','point_size','point_pixels','blend')})
            item.model=QMatrix4x4(*b['model']);item.depth=b['depth'];item.surface_gain=b['surface_gain']
            item.blend_mode=b.get('blend_mode','additive')
            item.material=b.get('material');item.material_values={}
            self.items.append(item);view.addItem(item)
            if 'animation' in b:self.animations.append((item,b['animation'],item.pos.copy()))
        from .object_graph import ObjectGraph
        self.graph=ObjectGraph(definition.graph,self,quality) if definition.graph else None
        self.building_count=self.data['statistics']['buildings']
    @property
    def vertex_count(self):return sum(len(i.pos) for i in self.items)
    def _route(self,points,t):
        times=self.route_times;t=t%self.loop_seconds;i=min(len(times)-2,int(np.searchsorted(times,t,side='right')-1))
        count=len(points)-1;dt=times[i+1]-times[i];u=(t-times[i])/dt
        def tangent(j):
            if j==0 or j==count:return (points[1]-points[count-1])/(times[1]+self.loop_seconds-times[count-1])
            return (points[j+1]-points[j-1])/(times[j+1]-times[j-1])
        a=points[i];b=points[i+1];ma=tangent(i)*dt;mb=tangent(i+1)*dt
        return (2*u**3-3*u**2+1)*a+(u**3-2*u**2+u)*ma+(-2*u**3+3*u**2)*b+(u**3-u**2)*mb
    def camera_pose(self,t):return self._route(self.route_eyes,t),self._route(self.route_targets,t)
    def flyover(self,t):return self.camera_pose(t)
    def safe_eye(self,eye):return eye
    def update(self,t,dt,audio):
        self.view.scene_time=t;signals=np.array([audio.rms,audio.low,audio.mid,audio.high,audio.beat])
        self.context.update(time=t,dt=dt)
        for index,(item,b) in enumerate(zip(self.items,self.descriptors)):
            item.emission=b['emission']+float(np.dot(b['audio'],signals))
            item.surface_gain=b['surface_gain'];item.rim=b['rim']
            for key,e in self.extension.bindings.get((self.quality,index),{}).items():
                value=e.value(self.context)
                if key=='emission_add':item.emission+=max(0.,min(10.,value))
                else:setattr(item,key,max(0.,min(4. if key=='surface_gain' else 2.,value)))
            item.material_values={}
            for name,expressions in self.extension.materials.get(item.material,{}).items():
                value=tuple(e.value(self.context) for e in expressions)
                item.material_values[name]=value[0] if len(value)==1 else value
        for item,a,base in self.animations:
            if a['type']=='drift':
                pos=base.copy();speed=a['speed']
                pos[:,0]+=a['amplitude'][0]*np.sin(t*speed+base[:,1]*.013)
                pos[:,1]+=a['amplitude'][1]*np.sin(t*speed*.73+base[:,0]*.009)
                pos[:,2]+=a['amplitude'][2]*np.sin(t*speed*.5+base[:,1]*.021)
                item.set_data(pos)
            elif a['type']=='shuttle':
                origin=list(a['origin']);origin[a['axis']]+=((t*a['speed']+a['phase']*a['span'])%a['span'])-a['span']/2
                item.model=QMatrix4x4();item.translate(*origin)
            elif a['type']=='rotate':
                index=self.items.index(item)
                angle=self.extension.animations[(self.quality,index)].value(self.context)%360
                p=a['pivot'];item.model=QMatrix4x4();item.model.translate(*p);item.model.rotate(angle,*a['axis']);item.model.translate(*[-v for v in p])
                item.model=item.model*QMatrix4x4(*self.descriptors[index]['model'])
            elif a['type']=='path':
                u=(t/a['duration']+a['phase'])%1
                pos=self.path_pose(a['points'],u);direction=self.path_pose(a['points'],(u+.0001)%1)-pos
                item.model=QMatrix4x4();item.model.translate(*map(float,pos))
                if a['orient']:
                    item.model.rotate(math.degrees(math.atan2(-direction[0],direction[1])),0,0,1)
                    item.model.rotate(math.degrees(math.atan2(direction[2],np.linalg.norm(direction[:2]))),1,0,0)
                index=self.items.index(item);item.model=item.model*QMatrix4x4(*self.descriptors[index]['model'])
        if self.graph:self.graph.update(t)
    @staticmethod
    def path_pose(points,u):
        points=np.asarray(points[:-1],dtype=float);count=len(points);phase=(u%1)*count;i=int(phase);x=phase-i
        a,b,c,d=(points[(i+j)%count] for j in (-1,0,1,2))
        return .5*((2*b)+(-a+c)*x+(2*a-5*b+4*c-d)*x*x+(-a+3*b-3*c+d)*x*x*x)
    def dispose(self):
        for item in self.items:item.dispose();self.view.removeItem(item);item.deleteLater()
        self.items=[];self.animations=[];self.graph=None

class MeshRuntime:
    def __init__(self,definition,quality,reactive):
        self.definition=definition;self.quality=quality if quality in definition.quality else 'medium'
        self.reactive=reactive;self.params=dict(ambient=definition.document['environment']['ambient'],planet_fill=definition.document['environment']['planet_fill'])
        self.signal_accumulator=0.
        self.shader_controller=None
        if definition.background:
            from aureon_packages.scene_v2_runtime import PackageSceneRuntimeV2
            self.shader_controller=PackageSceneRuntimeV2(definition.background,self.quality,reactive)
        self.view=ViewState(definition.document['camera'],definition.document['environment'])
        self.scene=MeshScene(definition,self.quality,self.view)
        if self.shader_controller:self.scene.context=self.shader_controller._eval_context
        self.bridge=AudioBridge();self.bridge.enabled=reactive;self.bridge.demo=False;self.bridge.attack_rate=1/.06;self.bridge.release_rate=1/.3
        self.camera=Camera(self.view);self.seconds=0.;self.audio_accumulator=0.;self.preset='auto';self.fixed_time=None;self.response=AudioSignals()
        self.camera.micro_motion=definition.document['camera'].get('micro_motion',1.)
        self.set_camera_preset('auto');self.scene.update(0,0,self.response)
    def set_camera_preset(self,preset):
        presets={p[0]:p[3] for p in self.definition.document['camera']['presets']}
        if preset!='auto' and preset not in presets:return False
        if self.scene.graph and self.scene.graph.light_slots:self.scene.graph.light_slots.reset()
        self.preset=preset;self.camera.reset();self.fixed_time=None
        modes={'orbit':'Slow orbit','flyover':'Flyover','dolly':'Dolly'}
        self.camera.mode=modes.get(preset,'Scripted flyby')
        if preset!='auto' and preset not in modes:self.fixed_time=presets[preset];self.camera.phase=self.fixed_time
        self.camera.update(0,self.scene,self.bridge.values);return True
    def update(self,dt,frame):
        dt=min(.05,max(0.,dt));self.audio_accumulator+=dt
        if self.audio_accumulator>=1/30:
            self.audio_accumulator%=1/30
            signals=analyzer_signals(frame.audio) if frame.audio_mode and frame.playing is not False else AudioSignals()
            self.bridge.receive(asdict(signals))
        self.response=self.bridge.update(dt,self.seconds);self.seconds+=dt
        if self.shader_controller:
            # Reuse AURS v2 expressions/helpers. One shared clock and smoothed
            # audio packet; the shader controller never steps another analyzer.
            c=self.shader_controller;c.elapsed=self.seconds
            audio=c.audio_context.audio
            for key in audio:audio[key]=0.
            for key in ('low','mid','high','energy','beat'):audio[key]=getattr(self.response,key)
            audio['presence']=self.response.energy
            c.audio_context.playing=bool(frame.playing and frame.audio_mode)
            paused=bool(frame.audio_mode and frame.playing is False)
            active=bool(frame.audio_mode and frame.playing is not False and frame.audio is not None and self.reactive)
            c.audio_context.runtime.update(playing=float(frame.playing is True),audio_mode=float(bool(frame.audio_mode)),
                reactive=float(self.reactive),paused=float(paused),audio_active=float(active),
                ambient=float(not frame.audio_mode or (not self.reactive and not paused)))
            self.signal_accumulator+=dt
            while self.signal_accumulator+1e-9>=1/60:
                c._signals(1/60);self.signal_accumulator-=1/60
            c._publish()
        self.scene.update(self.seconds,dt,self.response)
        self.camera.update(0. if self.fixed_time is not None else dt,self.scene,self.response)
    def dispose(self):self.scene.dispose()
