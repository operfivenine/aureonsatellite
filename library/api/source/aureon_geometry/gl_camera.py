"""Z-up camera routes. Pure math; no state shared with Aureon's cameras."""
import math
import numpy as np
from PySide6.QtGui import QVector3D as Vector

MODES=('Static','Slow orbit','Flyover','Dolly','Scripted flyby','Manual')

def catmull_loop(points, phase):
    count=len(points);phase=phase%count;i=int(phase);u=phase-i
    a,b,c,d=[np.asarray(points[j%count],float) for j in (i-1,i,i+1,i+2)]
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)

class Camera:
    def __init__(self, view):
        self.view=view;self.mode='Slow orbit';self.speed=1.;self.yaw=0.;self.pitch=0.;self.distance=1.;self.phase=0.
        self.micro_motion=1.

    def reset(self):
        self.phase=0.;self.yaw=0.;self.pitch=0.;self.distance=1.

    def update(self,dt,scene,audio):
        if self.mode=='Manual':return
        self.phase+=dt*self.speed;t=self.phase
        target=np.array(scene.target,float);eye=np.array(scene.eye,float)
        delta=eye-target;distance=np.linalg.norm(delta)*self.distance
        azimuth=math.atan2(delta[1],delta[0]);elevation=math.asin(delta[2]/np.linalg.norm(delta))
        if self.mode=='Slow orbit':azimuth+=math.sin(t*.075)*.55
        elif self.mode=='Flyover':
            eye,target=scene.flyover(t);eye=np.array(eye);target=np.array(target)
            delta=eye-target;distance=np.linalg.norm(delta)*self.distance
            azimuth=math.atan2(delta[1],delta[0]);elevation=math.asin(delta[2]/np.linalg.norm(delta))
        elif self.mode=='Dolly':distance*=.80+.20*math.cos(t*.22)
        elif self.mode=='Scripted flyby':
            if hasattr(scene,'camera_pose'):
                eye,target=scene.camera_pose(t)
                eye=np.asarray(eye,float);target=np.asarray(target,float)
            else:eye=catmull_loop(scene.path,t/9.)
            delta=eye-target;distance=np.linalg.norm(delta)*self.distance
            azimuth=math.atan2(delta[1],delta[0]);elevation=math.asin(delta[2]/np.linalg.norm(delta))
        azimuth+=math.radians(self.yaw);elevation+=math.radians(self.pitch)
        elevation=max(-.55,min(1.25,elevation));distance=max(scene.min_distance,distance)
        eye=target+distance*np.array([math.cos(elevation)*math.cos(azimuth),math.cos(elevation)*math.sin(azimuth),math.sin(elevation)])
        eye=scene.safe_eye(eye)
        delta=eye-target;distance=np.linalg.norm(delta)
        # Restrained micro-motion, added only to the Lab camera.
        target[2]+=.08*self.micro_motion*audio.beat*math.sin(t*11.)
        self.view.setCameraPosition(pos=Vector(*target),distance=float(distance),
            elevation=math.degrees(math.asin(delta[2]/distance)),azimuth=math.degrees(math.atan2(delta[1],delta[0])))
