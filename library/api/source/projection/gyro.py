"""Trusted bounded gyroscope geometry; package data never supplies shaders."""
import math
import numpy as np
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QMatrix4x4,QVector3D,QImage,QPainter,QColor,QPen,QPolygonF

RINGS=((1.34,.065),(1.12,.060),(.90,.055),(1.53,.014),(.23,.025),(.18,.018))

def mesh(detail):
    vertices=[];segments=detail*4
    for ring in range(len(RINGS)):
        for i in range(segments):
            a=i*math.tau/segments;b=(i+1)*math.tau/segments
            # Four faces of a shallow machined ring, with real depth.
            faces=(((-1,1),(1,1)),((1,1),(1,-1)),((1,-1),(-1,-1)),((-1,-1),(-1,1)))
            for (r0,z0),(r1,z1) in faces:
                v=((a,r0,z0,ring),(b,r0,z0,ring),(b,r1,z1,ring),(a,r1,z1,ring))
                vertices.extend((v[0],v[1],v[2],v[0],v[2],v[3]))
    return np.asarray(vertices,dtype=np.float32)

def camera(d):
    m=QMatrix4x4();m.perspective(34,d.width/d.height,.1,20)
    view=QMatrix4x4();view.lookAt(QVector3D(.15,1.0,5.9),QVector3D(0,0,0),QVector3D(0,1,0))
    view.rotate(d.yaw,0,1,0);view.rotate(d.tilt-48,1,0,0)
    return m*view

def rotations(state):
    t=state.seconds;boost=state.orbit_phase
    settings=((64+9*math.sin(t*.23),14+t*4+boost*20,t*14+boost*52),
              (-32+13*math.sin(t*.19),54+t*-5-boost*28,-t*19-boost*67),
              (28+11*math.sin(t*.21),-58+t*6+boost*24,t*24+boost*78),
              (72,0,-t*7-boost*12),(25,t*24,t*50),(68,-t*32,-t*36))
    result=[]
    for x,y,z in settings:
        m=QMatrix4x4();m.rotate(y,0,1,0);m.rotate(x,1,0,0);m.rotate(z,0,0,1);result.append(m)
    return result

def audio_values(state):
    bass=float(np.mean(state.bands[:16]));beat=max((power*math.exp(-age*9) for age,power,_ in state.waves),default=0.)
    return bass,beat

def fallback(d,state,scale):
    """Depth-sorted ring panels retaining the same poses and musical expansion."""
    im=QImage(round(d.width*scale),round(d.height*scale),QImage.Format_ARGB32_Premultiplied);im.fill(Qt.transparent)
    p=QPainter(im);p.setRenderHint(QPainter.Antialiasing);p.scale(scale,scale)
    poses=rotations(state);mvp=camera(d);bass,beat=audio_values(state);panels=[]
    for ring,(radius,width) in enumerate(RINGS):
        expanded=radius*(1+d.amplitude*(bass*.055+beat*.035))
        for i in range(160):
            a=math.tau*i/160;b=math.tau*(i+1)/160
            phase=((a/math.tau*(12 if ring<3 else 8)+ring*.27)%1)
            if ring<4 and phase>.82:continue
            points=[];depth=0
            for angle,lane in ((a,-1),(b,-1),(b,1),(a,1)):
                r=expanded+width*lane;v=poses[ring].map(QVector3D(r*math.cos(angle),r*math.sin(angle),0))
                depth+=v.z();screen=mvp.map(v)
                points.append(QPointF((screen.x()+1)*d.width/2,(1-screen.y())*d.height/2))
            panels.append((depth/4,ring,i,points))
    try:
        for depth,ring,i,points in sorted(panels):
            color=QColor(d.secondary if ring==1 else d.primary)
            if i%13==0:color=QColor(d.accent)
            color.setAlphaF(min(.95,(.35+.25*(depth+1.6)/3.2+beat*.2)*d.intensity))
            p.setBrush(color);p.setPen(QPen(color,.45));p.drawPolygon(QPolygonF(points))
        c=QColor(d.primary);c.setAlphaF(.85);p.setPen(QPen(c,.7));p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(d.width/2,d.height/2),2+beat*2,2+beat*2)
    finally:p.end()
    return im
