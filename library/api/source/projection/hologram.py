"""Bounded, trusted musical hologram primitives for declarative AURP packages.

Geometry is generated here, never executed from package input. Layered projected
3D curves and emissive surfaces share the host's transparent, non-activating window.
"""
import math
from functools import lru_cache
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen, QBrush, QRadialGradient, QLinearGradient, QPolygonF, QImage, QPainter

TAU = math.tau


def _color(rgb, alpha=1.):
    color = QColor(rgb)
    color.setAlphaF(max(0., min(1., alpha)))
    return color


def _pen(rgb, width, alpha):
    pen = QPen(_color(rgb, alpha), width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _curve(points):
    path = QPainterPath(QPointF(*points[0]))
    for point in points[1:]:
        path.lineTo(*point)
    return path


@lru_cache(maxsize=32)
def _glow_texture(rgb):
    # Small reusable radial light sprites avoid evaluating dozens of raster
    # gradients at full supersampled resolution every frame. Bounded cache.
    image=QImage(64,64,QImage.Format_ARGB32_Premultiplied);image.fill(Qt.transparent)
    painter=QPainter(image)
    g = QRadialGradient(QPointF(32,32),32)
    g.setColorAt(0, _color(rgb, 1))
    g.setColorAt(.28, _color(rgb, .55))
    g.setColorAt(.7, _color(rgb, .12))
    g.setColorAt(1, _color(rgb, 0))
    painter.fillRect(image.rect(),g);painter.end()
    return image


def _glow(p, x, y, rx, ry, rgb, alpha):
    p.save()
    p.setOpacity(p.opacity()*max(0.,min(1.,alpha)))
    p.drawImage(QRectF(x-rx,y-ry,2*rx,2*ry),_glow_texture(rgb))
    p.restore()


class MusicalHologram:
    def __init__(self):
        self.phase = 0.
        self.waves = []
        self.last_impact = 0.
        self.cooldown = 0.
        self.last_time = None
        self._rotation = None
        # Deterministic positions. No frame-by-frame random jitter or allocations
        # of a particle simulation whose size can grow with playback duration.
        self.sphere_points = tuple((1-2*(i+.5)/176, i*2.3999632297) for i in range(176))
        self.particles = tuple(((i*.61803398875)%1, (i*.38196601125)%1, (i*.754877666)%1) for i in range(84))

    def reset(self):
        self.phase = 0.; self.waves.clear(); self.last_impact = 0.
        self.cooldown = 0.; self.last_time = None

    def paint(self, p, node, context):
        sat = lambda value: max(0., min(1., value))
        controls = {key:sat(node[key].value(context)) for key in ('bass','mid','treble','energy','impact')}
        stamp = context['time']
        dt = min(.06, max(0., stamp-self.last_time)) if self.last_time is not None else 0.
        self.last_time = stamp
        self.phase += dt * (.22 + 1.05*controls['energy'] + .5*controls['mid'])
        self.cooldown = max(0., self.cooldown-dt)
        impact = controls['impact']
        if self.cooldown == 0 and impact > .18 and impact-self.last_impact > .06:
            self.waves.append([0., impact])
            self.waves[:] = self.waves[-5:]
            self.cooldown = .18
        self.last_impact = impact
        self.waves = [[age+dt, strength] for age,strength in self.waves if age+dt < 1.35]
        zones = [sat(context['audio'].get(f'zone{i}',0)) for i in range(8)]
        r = max(12., min(100., node['radius'].value(context)))
        primary, secondary = node['primary'], node['secondary']
        p.save()
        if node['model'] == 'planet':
            self._planet(p,r,primary,secondary,controls,zones)
        else:
            self._spectral(p,r,primary,secondary,controls,zones)
        p.restore()

    def _project(self, x, y, z, r, yaw=0., tilt=-.25):
        if self._rotation != (yaw,tilt):
            self._rotation = (yaw,tilt)
            self._trig = math.cos(yaw),math.sin(yaw),math.cos(tilt),math.sin(tilt)
        cy,sy,ct,st = self._trig
        x,z = x*cy+z*sy, z*cy-x*sy
        y,z = y*ct-z*st, z*ct+y*st
        perspective = 1/(1-.13*z)
        return x*r*perspective, y*r*perspective, z

    def _portal(self,p,cx,cy,r,primary,secondary,energy,impact,phase,detail=40):
        _glow(p,cx,cy,r*1.4,r*.4,primary,.16+.16*energy)
        for rr,alpha,width in [(1.07,.18,3.),(1.,.8,1.05),(.89,.22,1.4),(.70,.38,.65),(.62,.85,1.05)]:
            p.setPen(_pen(primary if rr>.75 else secondary,width,alpha*(.65+.35*energy)))
            p.setBrush(Qt.NoBrush)
            ry=r*.235
            p.drawEllipse(QRectF(cx-r*rr,cy-ry*rr,2*r*rr,2*ry*rr))
        for i in range(detail):
            a=i*TAU/detail+phase*.23
            b=a+TAU/detail*.64
            rr=r*(.77+.05*(i%3))
            pts=[(cx+rr*math.cos(a),cy+rr*.235*math.sin(a)),
                 (cx+(rr+4)*math.cos(a),cy+(rr+4)*.235*math.sin(a)),
                 (cx+(rr+4)*math.cos(b),cy+(rr+4)*.235*math.sin(b)),
                 (cx+rr*math.cos(b),cy+rr*.235*math.sin(b))]
            alpha=.16+.22*((i*7)%11)/10+.24*energy
            p.setPen(_pen(secondary,.45,alpha));p.setBrush(_color(primary,alpha*.28))
            p.drawPolygon(QPolygonF([QPointF(*v) for v in pts]))
        for i in range(3):
            p.setPen(_pen('#e9fcff',1.0,.55+.3*impact));p.setBrush(Qt.NoBrush)
            rr=r*(.96-i*.16)
            p.drawArc(QRectF(cx-rr,cy-rr*.235,2*rr,2*rr*.235),int((phase*45+i*117)*16),int((34+16*energy)*16))

    def _planet(self,p,r,primary,secondary,a,zones):
        bass,mid,high,energy,impact=(a[k] for k in ('bass','mid','treble','energy','impact'))
        phase=self.phase
        radius=r*(1+.055*bass+.033*impact)
        by=r*1.95
        # Projector cone: translucent light volume, filament transport, emitter.
        gradient=QLinearGradient(0,by,0,r*.8)
        gradient.setColorAt(0,_color(primary,.16+.13*energy))
        gradient.setColorAt(.32,_color(primary,.035+.06*energy))
        gradient.setColorAt(1,_color(primary,0))
        p.setPen(Qt.NoPen);p.setBrush(gradient)
        p.drawPolygon(QPolygonF([QPointF(-5,by),QPointF(-r*.78,r*.68),QPointF(r*.78,r*.68),QPointF(5,by)]))
        _glow(p,0,by-9,r*.29,r*.75,primary,.14+.19*energy)
        for i in range(18):
            u=(phase*.46+i/18)%1
            y=by-u*(by-r*.55)
            x=math.sin(i*2.399+phase)*r*.30*u
            p.setPen(_pen(primary,.45,.09+.18*energy))
            p.drawLine(QPointF(x,y),QPointF(x*.93,y+4+high*5))
        self._portal(p,0,by,r*.58,primary,secondary,energy,impact,phase,32)
        _glow(p,0,0,r*1.40,r*1.32,secondary,.075+.08*energy)
        _glow(p,-r*.07,-r*.02,r*.79,r*.83,primary,.10+.10*energy)
        # Visible translucent body and a bright, uneven atmospheric rim.
        shell=QRadialGradient(QPointF(-r*.22,-r*.25),r*1.24)
        shell.setColorAt(0,_color(primary,.045+.045*energy))
        shell.setColorAt(.67,_color(secondary,.028))
        shell.setColorAt(.88,_color(primary,.055+.035*energy))
        shell.setColorAt(1,_color(primary,0))
        p.setPen(Qt.NoPen);p.setBrush(shell)
        p.drawEllipse(QRectF(-radius,-radius,2*radius,2*radius))
        for start,span,color,alpha in [(12,100,primary,.75),(124,65,secondary,.58),(225,93,primary,.72),(322,35,'#e6f7ff',.88)]:
            p.setPen(_pen(color,.8+.55*impact,alpha));p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(-radius,-radius,2*radius,2*radius),int((start+phase*5)*16),span*16)
        # Moving clouds of light give the shell an interior rather than a mesh.
        for i in range(9):
            theta=phase*(.27+i*.018)+i*2.399
            x,y,z=self._project(math.cos(theta)*.47,math.sin(theta*1.31+i)*.40,
                                math.sin(theta)*.48,radius,phase*.30)
            band=zones[i%8]
            _glow(p,x,y,r*(.17+.09*band),r*(.24+.07*mid),
                  secondary if i%3==0 else primary,(.045+.13*mid+.10*band)*(.7+.3*z))
        # Latitude guides exist behind the flowing matter, rather than defining
        # the whole object as a wireframe icon.
        for j in range(-3,4):
            lat=j*.21
            horizontal=math.sqrt(1-lat*lat)
            points=[self._project(horizontal*math.cos(k*TAU/84),lat,horizontal*math.sin(k*TAU/84),radius,phase*.25)[:2] for k in range(85)]
            p.setPen(_pen(primary,.38,.055));p.drawPath(_curve(points))
        # Independently tilted electric ribbons wrap the surface in depth.
        layers={}
        for ribbon in range(7):
            points=[]
            tilt=ribbon*.47+phase*.12
            for k in range(97):
                theta=k*TAU/96
                lat=.70*math.sin(theta*.5+ribbon*.91)+.025*mid*math.sin(theta*8+phase*2+ribbon)
                rad=math.sqrt(1-lat*lat)*(1+.028*math.sin(theta*5+phase*2)*mid)
                x,z=rad*math.cos(theta*1.7+ribbon),rad*math.sin(theta*1.7+ribbon)
                y=lat
                y,z=y*math.cos(tilt)-z*math.sin(tilt),z*math.cos(tilt)+y*math.sin(tilt)
                points.append(self._project(x,y,z,radius,phase*.26+ribbon*.2))
            for k in range(0,96,4):
                chunk=points[k:k+5];depth=sum(v[2] for v in chunk)/len(chunk)
                bucket=max(-1,min(4,int(depth*4) if depth>0 else -1))
                key=(bucket,ribbon)
                if key not in layers: layers[key]=QPainterPath()
                layers[key].addPath(_curve([v[:2] for v in chunk]))
        for (bucket,j),path in sorted(layers.items()):
            depth=-.5 if bucket<0 else (bucket+.5)/4
            alpha=(.07 if depth<0 else .24+.34*depth)+.12*energy
            color=secondary if j%3==0 else primary
            if depth>.45:
                p.setPen(_pen(color,2.3+.7*mid,alpha*.085));p.setBrush(Qt.NoBrush);p.drawPath(path)
            p.setPen(_pen(color,.55+.5*mid,alpha));p.setBrush(Qt.NoBrush);p.drawPath(path)
            if depth>.3 and j%2==0:
                p.setPen(_pen('#e8f9ff',.28+.22*high,alpha*.65));p.drawPath(path)
        # Fine spiral filaments fill the sphere with light and react to melody.
        for i in range(20):
            points=[]
            for j in range(36):
                u=j/35
                angle=i*2.399+u*(5.7+mid*3)+phase*(.45+(i%3)*.10)
                rad=u**.65*(.54+.26*math.sin(i*3.71)**2)
                lat=math.sin(i*1.42+u*(4+mid*1.8)+phase*.4)*.63
                x,y,_=self._project(math.cos(angle)*rad,lat*u,math.sin(angle)*rad,radius,phase*.3)
                points.append((x,y))
            path=_curve(points)
            p.setPen(_pen(secondary if i%4==0 else primary,.45,.16+.24*mid));p.drawPath(path)
            if i%4==0:
                p.setPen(_pen(primary,2.5,.018+.026*mid));p.drawPath(path)
        projected=[]
        for i,(y,theta) in enumerate(self.sphere_points):
            rr=math.sqrt(1-y*y)
            wav=1+.02*zones[i%8]*math.sin(theta*3+phase*2)
            x,yy,z=self._project(rr*math.cos(theta),y,rr*math.sin(theta),radius*wav,phase*.30)
            projected.append((z,x,yy,i))
        for z,x,y,i in sorted(projected):
            alpha=(.075 if z<0 else .16+.34*z)+high*zones[i%8]*.30
            size=.38+.36*max(0,z)+.30*high
            p.setPen(Qt.NoPen);p.setBrush(_color(primary if i%5 else secondary,alpha))
            p.drawEllipse(QRectF(x-size,y-size,size*2,size*2))
            if z>.4 and i%17==0:
                _glow(p,x,y,3+5*high,3+5*high,primary,.16+.34*high)
                p.setPen(_pen('#eaffff',.5,.38+.4*high));p.drawLine(QPointF(x-1.5,y),QPointF(x+1.5,y))
        _glow(p,-r*.05,r*.025,r*.32,r*.32,primary,.20+.35*energy+.18*impact)
        _glow(p,-r*.05,r*.025,r*.10,r*.10,'#ecf8ff',.28+.35*impact)
        for age,strength in self.waves:
            rr=radius*(.30+age*.68)
            fade=max(0,1-age/1.35)*strength
            p.setPen(_pen(primary,.7,fade*.44));p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(-rr,-rr*.94,2*rr,2*rr*.94))

    def _spectral(self,p,r,primary,secondary,a,zones):
        bass,mid,high,energy,impact=(a[k] for k in ('bass','mid','treble','energy','impact'))
        phase=self.phase
        top,bottom=-r*1.08,r*1.14
        cr=r*.55*(1+.06*bass)
        _glow(p,0,9,r*.98,r*1.7,secondary,.055+.075*energy)
        _glow(p,0,9,r*.42,r*1.45,primary,.13+.22*energy)
        # Curved translucent sides: lit edges and rear hex cells establish volume.
        gradient=QLinearGradient(-cr,0,cr,0)
        for pos,alpha in [(0,.10),(.08,.035),(.5,.012),(.92,.035),(1,.10)]:
            gradient.setColorAt(pos,_color(secondary,alpha*(.6+energy)))
        p.setPen(Qt.NoPen);p.setBrush(gradient)
        p.drawRoundedRect(QRectF(-cr,top,2*cr,bottom-top),8,8)
        for layer in (-1,1):
            for i in range(20):
                theta=i*TAU/20+phase*.18
                z=math.sin(theta)
                if (z>0)!=(layer>0):continue
                x=cr*math.cos(theta)
                depth=.14 if z<0 else .40+.35*z
                band=zones[i%8]
                for j in range(13):
                    cy=top+(j+.5)*(bottom-top)/13
                    active=max(0.,1-abs((12-j)/12-band)*2.3)
                    alpha=(.035+.13*active+.06*energy)*depth
                    w=max(1.6,3.4*abs(z));h=4.2
                    points=[(x-w,cy),(x-w*.5,cy-h),(x+w*.5,cy-h),(x+w,cy),(x+w*.5,cy+h),(x-w*.5,cy+h)]
                    p.setPen(_pen(secondary,.4,alpha*1.5));p.setBrush(_color(primary,alpha*.45))
                    p.drawPolygon(QPolygonF([QPointF(*pt) for pt in points]))
        for side in (-1,1):
            p.setPen(_pen(primary,.55,.23+.25*energy));p.setBrush(Qt.NoBrush)
            points=[(side*cr*(1+.025*math.sin(j*.3+phase)),top+j*(bottom-top)/40) for j in range(41)]
            p.drawPath(_curve(points))
        # Uneven plasma strands. Bass spreads them, mids alter winding,
        # high bands sharpen their hot spine instead of merely changing opacity.
        for i in range(4):
            points=[]
            for j in range(73):
                u=j/72
                y=bottom-u*(bottom-top)
                angle=u*(TAU*(1.25+mid*.7+i*.12))-phase*(1.1+mid+i*.17)+i*TAU/4
                envelope=math.sin(u*math.pi)**.7
                x=(math.sin(angle)+.19*math.sin(angle*2.4+i))*cr*(.16+.36*bass)*envelope
                x+=math.sin(u*41+phase*4+i)*(.45+1.6*high)*envelope
                points.append((x,y))
            path=_curve(points)
            p.setBrush(Qt.NoBrush)
            p.setPen(_pen(primary,4.2+.9*bass,.055+.10*energy));p.drawPath(path)
            p.setPen(_pen(secondary if i%2 else primary,1.2+.4*mid,.22+.34*energy));p.drawPath(path)
            p.setPen(_pen('#e6ffff',.33+.33*high,.24+.40*energy));p.drawPath(path)
        # 3D helix wraps around the cylinder and fades on the back side.
        for i in range(84):
            u=i/83;v=(i+1)/83
            theta=u*TAU*3.2-phase*1.1
            angle2=v*TAU*3.2-phase*1.1
            x=cr*.96*math.cos(theta);xx=cr*.96*math.cos(angle2)
            y=bottom-u*(bottom-top);yy=bottom-v*(bottom-top)
            alpha=.08+.24*max(0,math.sin(theta))+.12*mid
            p.setPen(_pen(primary,.55,alpha));p.drawLine(QPointF(x,y),QPointF(xx,yy))
        for i,(offset,spread,seed) in enumerate(self.particles):
            u=(phase*(.26+.1*seed)+offset)%1
            y=bottom-u*(bottom-top)
            x=(spread-.5)*cr*1.8+math.sin(u*8+phase+seed*7)*3
            band=zones[i%8]
            alpha=(.09+.42*high+.20*band)*(.25+.75*math.sin(u*math.pi))
            length=1.3+4.2*high+band*2
            p.setPen(_pen(primary if i%3 else '#c5a2ff',.5+.3*high,alpha))
            p.drawLine(QPointF(x,y),QPointF(x,y+length))
            if i%13==0:
                _glow(p,x,y,2.7+2*high,2.7+2*high,primary,alpha*.5)
        for age,strength in self.waves:
            u=min(1,age/1.12)
            y=bottom-u*(bottom-top)
            rr=cr*(.82+.38*math.sin(u*math.pi))
            p.setPen(_pen('#e3ffff',1.0,max(0,1-age/1.35)*strength*.65));p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(-rr,y-rr*.16,2*rr,2*rr*.16))
        self._portal(p,0,top,r*.84,primary,secondary,energy,impact,-phase,48)
        self._portal(p,0,bottom,r*.95,primary,secondary,energy,impact,phase,48)
        # Vertical emitter light is shaped by the actual musical envelope.
        _glow(p,0,bottom-7,cr*.38,r*.55,primary,.16+.31*energy)
        _glow(p,0,top+5,cr*.32,r*.28,'#c4eaff',.07+.18*energy+.2*impact)
