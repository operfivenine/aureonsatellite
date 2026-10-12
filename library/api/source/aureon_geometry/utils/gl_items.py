"""Scene item adapter: preserve SHOWCASE geometry/transforms; GPU owned by host.

This replaces only GLGraphicsItem's presentation API. The original scene,
meshes, material parameters and audio animation are unchanged.
"""
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QMatrix4x4


class GeometryItem(QObject):
    def __init__(self, pos, colors, normals=None, mode='triangles', lit=True,
                 emission=0., fog=1., point_size=2., blend=False, rim=0.,
                 style=0., point_pixels=0.):
        super().__init__()
        self.mode={'triangles':0x0004,'lines':0x0001,'points':0x0000}[mode]
        self.lit=float(lit);self.emission=emission;self.fog=fog
        self.point_size=point_size;self.blend=blend;self.rim=rim
        self.style=style;self.point_pixels=point_pixels
        self.depth=20 if blend else 0
        self.model=QMatrix4x4();self.revision=0
        self.set_data(pos,colors,normals)

    def set_data(self,pos,colors=None,normals=None):
        self.pos=np.ascontiguousarray(pos,np.float32).reshape(-1,3)
        if colors is not None:self.colors=np.ascontiguousarray(np.broadcast_to(colors,(len(self.pos),4)),np.float32)
        if normals is not None:self.normals=np.ascontiguousarray(normals,np.float32)
        elif not hasattr(self,'normals') or len(self.normals)!=len(self.pos):self.normals=np.zeros_like(self.pos)
        self.revision+=1

    def translate(self,dx,dy,dz,local=False):
        matrix=QMatrix4x4();matrix.translate(float(dx),float(dy),float(dz))
        self.model=self.model*matrix if local else matrix*self.model

    def rotate(self,angle,x,y,z,local=False):
        matrix=QMatrix4x4();matrix.rotate(angle,x,y,z)
        self.model=self.model*matrix if local else matrix*self.model

    def setDepthValue(self,value):self.depth=value
    def dispose(self):
        self.pos=np.empty((0,3),np.float32);self.normals=np.empty((0,3),np.float32);self.colors=np.empty((0,4),np.float32)
