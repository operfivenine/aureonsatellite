"""GPU RGBA surface presented through the existing native alpha tray window."""
from pathlib import Path
import math,os,time
import numpy as np
from PySide6.QtCore import Qt,QSize,QRectF,QPointF,Signal
from PySide6.QtGui import (QOpenGLContext,QOffscreenSurface,QSurfaceFormat,QMatrix4x4,
    QVector3D,QColor,QPainter,QPen,QPolygonF,QImage)
from PySide6.QtOpenGL import (QOpenGLShader,QOpenGLShaderProgram,QOpenGLBuffer,
    QOpenGLVertexArrayObject,QOpenGLFramebufferObject,QOpenGLFramebufferObjectFormat)
from aureon_gl_uniforms import CachedUniformUploader
from aureon_gl_diagnostics import record
from .host import ProjectionHost
from .surface_audio import SurfaceAudio

def matrix(definition):
    if definition.model=='gyro_rings':
        from .gyro import camera
        return camera(definition)
    tilt=math.radians(definition.tilt);yaw=math.radians(definition.yaw)
    m=QMatrix4x4();m.perspective(36,definition.width/definition.height,.1,20.)
    v=QMatrix4x4();distance=4.9
    v.lookAt(QVector3D(distance*math.cos(tilt)*math.sin(yaw),distance*math.sin(tilt),
                     distance*math.cos(tilt)*math.cos(yaw)),QVector3D(0,.25,0),QVector3D(0,1,0))
    return m*v

class SurfaceGPU:
    def __init__(self,definition):
        self.definition=definition;self.context=None;self.surface=None
        self.program=None;self.post=None;self.vao=None;self.post_vao=None;self.buffer=None
        self.scene=None;self.output=None;self.count=0;self.upload=CachedUniformUploader()
        self.device={};self._initialize()

    def _initialize(self):
        if os.environ.get('AUREON_AURP_FORCE_GPU_FAIL')=='1':raise RuntimeError('Requested AURP GPU failure test')
        previous=QOpenGLContext.currentContext();previous_surface=previous.surface() if previous else None
        try:
            fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.CoreProfile)
            fmt.setAlphaBufferSize(8);fmt.setDepthBufferSize(24)
            self.context=QOpenGLContext();self.context.setFormat(fmt)
            if not self.context.create():raise RuntimeError('AURP OpenGL 3.3 context creation failed')
            self.surface=QOffscreenSurface();self.surface.setFormat(self.context.format());self.surface.create()
            if not self.surface.isValid() or not self.context.makeCurrent(self.surface):raise RuntimeError('AURP offscreen surface unavailable')
            from idle.gl.device_info import context_device_info
            self.device=context_device_info(self.context)
            root=Path(__file__).parent
            def program(vert,frag):
                p=QOpenGLShaderProgram()
                for kind,name in ((QOpenGLShader.Vertex,vert),(QOpenGLShader.Fragment,frag)):
                    if not p.addShaderFromSourceCode(kind,(root/name).read_text(encoding='utf-8')):
                        raise RuntimeError(f'{name}: {p.log()}')
                if not p.link():raise RuntimeError(p.log())
                return p
            gyro=self.definition.model=='gyro_rings'
            self.program=program('gyro.vert','gyro.frag') if gyro else program('surface.vert','surface.frag')
            self.post=program('surface_post.vert','surface_post.frag')
            self.vao=QOpenGLVertexArrayObject();self.post_vao=QOpenGLVertexArrayObject()
            if not self.vao.create() or not self.post_vao.create():raise RuntimeError('AURP VAO allocation failed')
            detail=self.definition.detail;rows=max(12,round(detail*.68))
            vertices=[]
            for j in range(rows):
                z0=-1.05+2.1*j/rows;z1=-1.05+2.1*(j+1)/rows
                for i in range(detail):
                    x0=-1.55+3.1*i/detail;x1=-1.55+3.1*(i+1)/detail
                    vertices.extend(((x0,z0),(x1,z0),(x1,z1),(x0,z0),(x1,z1),(x0,z1)))
            if gyro:
                from .gyro import mesh
                vertices=mesh(detail)
            self.count=len(vertices);raw=np.asarray(vertices,dtype=np.float32).tobytes()
            self.buffer=QOpenGLBuffer();self.buffer.create();self.vao.bind();self.buffer.bind()
            self.buffer.allocate(raw,len(raw));self.program.bind()
            self.program.enableAttributeArray(0);self.program.setAttributeBuffer(0,0x1406,0,4 if gyro else 2,16 if gyro else 8)
            self.vao.release();self.buffer.release();self.program.release()
            record('aurp_gpu_ready',renderer='projection.surface.experimental.v2',device=self.device,
                   vertices=self.count,canvas=[self.definition.width,self.definition.height])
        except Exception:
            self.destroy();raise
        finally:
            if self.context:self.context.doneCurrent()
            if previous and previous_surface:previous.makeCurrent(previous_surface)

    def render(self,state,scale):
        previous=QOpenGLContext.currentContext();previous_surface=previous.surface() if previous else None
        if not self.context or not self.context.makeCurrent(self.surface):raise RuntimeError('AURP GPU context lost')
        try:
            d=self.definition;f=self.context.functions()
            size=QSize(round(d.width*scale),round(d.height*scale))
            if self.scene is None or self.scene.size()!=size:
                self.scene=None;self.output=None
                fmt=QOpenGLFramebufferObjectFormat();fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
                fmt.setInternalTextureFormat(0x8058)
                self.scene=QOpenGLFramebufferObject(size,fmt);self.output=QOpenGLFramebufferObject(size)
                if not self.scene.isValid() or not self.output.isValid():raise RuntimeError('AURP RGBA framebuffer unavailable')
                f.glBindTexture(0x0DE1,self.scene.texture())
                for parameter,value in ((0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F)):
                    f.glTexParameteri(0x0DE1,parameter,value)
                f.glBindTexture(0x0DE1,0)
            if not self.scene.bind():raise RuntimeError('AURP scene framebuffer bind failed')
            f.glViewport(0,0,size.width(),size.height());f.glClearColor(0.,0.,0.,0.)
            f.glEnable(0x0B71);f.glDepthMask(True);f.glDisable(0x0BE2)
            f.glClear(0x4000|0x0100)
            p=self.program;p.bind();self.vao.bind()
            p.setUniformValue('u_mvp',matrix(d))
            u=self.upload
            if d.model=='gyro_rings':
                from .gyro import rotations,audio_values
                for i,rotation in enumerate(rotations(state)):
                    p.setUniformValue(f'u_rotations[{i}]',rotation)
                bass,beat=audio_values(state)
                u.scalar(f,p,'u_bass',bass);u.scalar(f,p,'u_beat',beat)
            u.array(f,p,'u_bands',state.bands)
            waves=[(*w,0.) for w in state.waves]
            if waves:u.array(f,p,'u_waves',waves)
            f.glUniform1i(u.location(p,'u_wave_count'),len(waves))
            for name,value in (('u_time',state.seconds),('u_amplitude',d.amplitude),
                               ('u_intensity',d.intensity),('u_treble',state.treble)):
                u.scalar(f,p,name,value)
            u.vector(f,p,'u_grid',(24,16))
            for name,color in (('u_primary',d.primary),('u_secondary',d.secondary),('u_accent',d.accent)):
                c=QColor(color);u.vector(f,p,name,(c.redF(),c.greenF(),c.blueF()))
            f.glDrawArrays(0x0004,0,self.count);self.vao.release();p.release()
            if not self.output.bind():raise RuntimeError('AURP bloom framebuffer bind failed')
            f.glDisable(0x0B71);f.glDepthMask(False);f.glClear(0x4000)
            self.post.bind();self.post_vao.bind()
            f.glActiveTexture(0x84C0);f.glBindTexture(0x0DE1,self.scene.texture())
            f.glUniform1i(self.post.uniformLocation('u_scene'),0)
            f.glUniform2f(self.post.uniformLocation('u_texel'),1/size.width(),1/size.height())
            f.glUniform1f(self.post.uniformLocation('u_glow'),d.glow)
            f.glDrawArrays(0x0004,0,3)
            self.post_vao.release();self.post.release();f.glBindTexture(0x0DE1,0)
            if f.glGetError():raise RuntimeError('AURP OpenGL render error')
            image=self.output.toImage()
            if image.isNull():raise RuntimeError('AURP RGBA readback failed')
            # Shaders write premultiplied RGBA. Qt FBO images may be labelled as
            # straight ARGB32/RGBA8888; relabel before converting, never multiply twice.
            if image.format()==QImage.Format_ARGB32:image.reinterpretAsFormat(QImage.Format_ARGB32_Premultiplied)
            elif image.format()==QImage.Format_RGBA8888:image.reinterpretAsFormat(QImage.Format_RGBA8888_Premultiplied)
            return image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
        finally:
            self.context.doneCurrent()
            if previous and previous_surface:previous.makeCurrent(previous_surface)

    def destroy(self):
        previous=QOpenGLContext.currentContext()
        previous_surface=previous.surface() if previous else None
        own=self.context
        if self.context and self.surface and self.context.makeCurrent(self.surface):
            self.scene=None;self.output=None
            for v in (self.vao,self.post_vao,self.buffer):
                if v:v.destroy()
            for p in (self.program,self.post):
                if p:p.removeAllShaders()
            self.context.doneCurrent()
        self.scene=None;self.output=None;self.vao=None;self.post_vao=None;self.buffer=None
        self.program=None;self.post=None;self.context=None
        if self.surface:self.surface.destroy()
        self.surface=None
        if previous and previous!=own and previous_surface:previous.makeCurrent(previous_surface)

def fallback_image(definition,state,scale):
    """Lower-detail projected surface when GL is unavailable; same audio state."""
    if definition.model=='gyro_rings':
        from .gyro import fallback
        return fallback(definition,state,scale)
    d=definition;im=QImage(round(d.width*scale),round(d.height*scale),QImage.Format_ARGB32_Premultiplied)
    im.fill(Qt.transparent);p=QPainter(im);p.setRenderHint(QPainter.Antialiasing);p.scale(scale,scale)
    m=matrix(d);points=[];nx,ny=24,16
    for j in range(ny+1):
        row=[]
        for i in range(nx+1):
            x=-1.55+3.1*i/nx;z=-1.05+2.1*j/ny;edge=math.hypot(x/1.55,z/1.05)
            b=float(np.interp(i/nx*63,np.arange(64),state.bands))
            rim=max(0.,min(1.,(1.15-edge)/.5));rim=rim*rim*(3-2*rim)
            h=.025+.022*math.sin(x*3.5+z*4+state.seconds*.45)
            h+=b*(.28+.73*(.32+.68*(.5+.5*math.sin(x*4.8+z*1.4-state.seconds*.65))**2))*d.amplitude*rim
            for age,strength,source in state.waves:
                delta=math.hypot(x-source,z+.65)-age*2.5
                h+=strength*math.exp(-delta*delta*42)*math.exp(-age*2.1)*.22*rim
            v=m.map(QVector3D(x,h,z));row.append((QPointF((v.x()+1)*d.width/2,(1-v.y())*d.height/2),edge,h))
        points.append(row)
    try:
        for j in range(ny):
            for i in range(nx):
                a,b,c,e=points[j][i],points[j][i+1],points[j+1][i+1],points[j+1][i]
                if max(a[1],b[1],c[1],e[1])>1.02:continue
                color=QColor(d.accent if max(a[2],b[2],c[2],e[2])>.38 else d.primary if j>7 else d.secondary)
                color.setAlphaF(.07);p.setBrush(color);color=QColor(color);color.setAlphaF(.55)
                p.setPen(QPen(color,.6));p.drawPolygon(QPolygonF([a[0],b[0],c[0],e[0]]))
    finally:p.end()
    return im

class SurfaceProjectionWindow(ProjectionHost):
    failed=Signal(str)
    def __init__(self,frame_provider,definition):
        self.definition=definition;self.audio=SurfaceAudio();self.gpu=None;self._gpu_attempted=False
        self.backend='pending';self.reason='';self._last_tick=None;self._broken=False
        self.frame_count=0;self._sample_at=0.;self._costs=[]
        super().__init__(frame_provider);self.setFixedSize(definition.width,definition.height)
        self.setWindowTitle('Aureon Gyro Rings' if definition.model=='gyro_rings' else 'Aureon Spectral Landscape')

    def showEvent(self,event):
        self.audio.reset();self._last_tick=None
        super().showEvent(event)

    def render_state(self,state,scale=2):
        scale=max(1.,min(3.,float(scale)))
        if not self._gpu_attempted:
            self._gpu_attempted=True
            try:self.gpu=SurfaceGPU(self.definition);self.backend='gpu'
            except Exception as exc:self._fallback(exc)
        if self.gpu:
            try:return self.gpu.render(state,scale)
            except Exception as exc:self._fallback(exc)
        return fallback_image(self.definition,state,scale)

    def _fallback(self,exc):
        self.reason=str(exc)[:300];self.backend='raster_fallback'
        if self.gpu:self.gpu.destroy()
        self.gpu=None
        record('fallback',scene='aurp_surface',reason=self.reason,backend=self.backend)

    def paintEvent(self,event):
        if self._broken:return
        started=time.perf_counter();dt=0. if self._last_tick is None else started-self._last_tick
        self._last_tick=started
        try:
            try:frame=self._frame_provider()
            except Exception:frame=None
            state=self.audio.advance(dt,frame)
            image=self.render_state(state,max(2.,self.devicePixelRatioF()))
            p=QPainter(self)
            try:
                p.setCompositionMode(QPainter.CompositionMode_Source);p.fillRect(self.rect(),Qt.transparent)
                p.setRenderHint(QPainter.SmoothPixmapTransform);p.drawImage(QRectF(self.rect()),image)
            finally:p.end()
            self.frame_count+=1;self._costs.append((time.perf_counter()-started)*1000);self._costs=self._costs[-120:]
            if started-self._sample_at>=10:
                self._sample_at=started
                record('aurp_frames',backend=self.backend,frames=self.frame_count,frame_ms=round(sum(self._costs)/len(self._costs),3))
        except Exception as exc:
            self._broken=True;self._timer.stop()
            from PySide6.QtCore import QTimer
            reason=str(exc)[:240];QTimer.singleShot(0,lambda:self.failed.emit(reason))

    def hideEvent(self,event):
        self._last_tick=None
        # Hidden projections hold no private GL context/FBOs. Showing again
        # reinitializes instead of retaining stale driver-owned resources.
        if self.gpu:self.gpu.destroy()
        self.gpu=None;self._gpu_attempted=False
        super().hideEvent(event)

    def cleanup(self):
        if self.gpu:self.gpu.destroy()
        self.gpu=None;self._gpu_attempted=False
        super().cleanup()
