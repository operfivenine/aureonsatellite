"""Aureon viewport host for the full Orbital City SHOWCASE01 scene.

Meshes, Z-up camera, material formulas and audio adapter come from GL Lab.
Only the GL submission interface is adapted to Qt's existing core-profile host.
"""
from pathlib import Path
import logging,os,time
from collections import deque
import numpy as np
from PySide6.QtCore import Qt,QTimer,Signal,QSize
from PySide6.QtGui import QSurfaceFormat,QPainter,QColor,QVector3D,QMatrix4x4
from PySide6.QtOpenGL import QOpenGLShader,QOpenGLShaderProgram,QOpenGLBuffer,QOpenGLVertexArrayObject,QOpenGLFramebufferObject,QOpenGLFramebufferObjectFormat
from idle.render_quality import background_size
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from aureon_content import get_registry
from aureon_content.models import SceneFrame
from aureon_camera_controls import camera_choice
from aureon_performance import ScenePerformanceStats,AsyncGpuTimer
from aureon_gl_uniforms import CachedUniformUploader
from aureon_gl_diagnostics import stage as diagnostic_stage, widget_event


class MeshWidget(QOpenGLWidget):
    failed=Signal(str)
    def __init__(self,parent,quality,style):
        super().__init__()
        self._style=style;self._entry=get_registry().resolve(style,'scene')
        self._base_style=self._entry.id
        self._runtime=self._entry.factory(quality,style==self._entry.reactive_id);self.scene=self._runtime.scene
        self._runtime.set_camera_preset(camera_choice(self._entry.id,self._entry.camera_presets))
        fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setDepthBufferSize(24);fmt.setSamples({'low':0,'medium':2,'high':4}.get(quality,2));fmt.setSwapInterval(0 if getattr(parent,"_benchmark_host",False) else 1)
        self.setFormat(fmt);self.setParent(parent);self.setAttribute(Qt.WA_TransparentForMouseEvents);self.setFocusPolicy(Qt.NoFocus)
        self.ready=False;self._failed=False;self._disposed=False;self.frame_count=0;self._last_frame=None
        self.reflections=None
        self._output_fbo=None
        self._scene_target=0
        from .antialiasing import GeometryAntialiasing
        self._antialiasing=GeometryAntialiasing()
        self._reflection_aa=GeometryAntialiasing()
        self._msaa_samples=0
        self._msaa_active=False
        if self._runtime.definition.reflections:
            from .reflections import PlanarReflections
            self.reflections=PlanarReflections(self._runtime.definition.reflections,quality)
        self.instancing=None;self.program=None;self.meshes=[];self.uploader=CachedUniformUploader()
        self.hybrid_program=None;self.hybrid_vao=None;self.hybrid_upload=CachedUniformUploader()
        from idle.gl.scene_textures import SceneTextures
        self.textures=SceneTextures()
        self._perf=ScenePerformanceStats();self._gpu_timer=AsyncGpuTimer();self._generation=0;self._suspended=False
        self._swap_time=None;self.draw_cpu=deque(maxlen=240)
        self._timer=QTimer(self);self._timer.setTimerType(Qt.PreciseTimer);self._timer.setInterval(0 if getattr(parent,"_benchmark_host",False) else 16);self._timer.timeout.connect(self.update)
        self._watchdog=QTimer(self);self._watchdog.setSingleShot(True);self._watchdog.setInterval(6000)
        self._watchdog.timeout.connect(lambda:self._fail('Orbital City GL context did not initialize'))
        self.frameSwapped.connect(self._swapped)
    def _fail(self,error):
        if self._failed or self._disposed:return
        self._failed=True;self._timer.stop();self._watchdog.stop()
        self._failure_reason=str(error)
        widget_event(self,'failure',reason=str(error))
        logging.getLogger('aureon').warning('Orbital City GL fallback: %s',error)
        QTimer.singleShot(0,lambda:self.failed.emit(str(error)) if not self._disposed else None)
    @staticmethod
    def _packed(item):return np.ascontiguousarray(np.column_stack((item.pos,item.colors,item.normals)),np.float32)
    def initializeGL(self):
        if self._failed or self._disposed:return
        diagnostic_stage(self,'geometry_initialize')
        try:
            if os.environ.get('AUREON_GEOMETRY_FORCE_GL_FAIL')=='1':raise RuntimeError('Requested Orbital City initialization failure test')
            from idle.gl.device_info import context_device_info
            self.device_info=context_device_info(self.context());self.parentWidget().window()._gl_device_info=dict(self.device_info)
            self.context().aboutToBeDestroyed.connect(self.cleanup,Qt.DirectConnection)
            self.program=QOpenGLShaderProgram()
            for kind,name in ((QOpenGLShader.Vertex,'material.vert'),(QOpenGLShader.Fragment,'material.frag')):
                diagnostic_stage(self,name)
                source=self._runtime.definition.sources[name]
                if self._runtime.definition.background and kind==QOpenGLShader.Fragment:
                    from aureon_packages.standard_library import library_source
                    first,body=source.split('\n',1)
                    tier={'low':0,'medium':1,'high':2}[self._runtime.quality]
                    source=first+f'\n#define AUR_QUALITY_TIER {tier}\n#define AUR_QUALITY_LEVEL {float(tier):.1f}\n'+library_source(tuple(self._runtime.definition.background.libraries)+(('experimental.scene_lights',) if self.scene.graph else ()))+body
                if not self.program.addShaderFromSourceCode(kind,source):raise RuntimeError(self.program.log())
            diagnostic_stage(self,'geometry_link')
            if not self.program.link():raise RuntimeError(self.program.log())
            self.uploader.reset()
            self.textures.create(self._runtime.definition.extensions.textures,self.program)
            if self.reflections:
                from idle.gl.scene_textures import _assign_sampler
                self.program.bind()
                for slot in range(2):_assign_sampler(self.context(),self.program,f'u_reflection{slot}',len(self.textures.items)+slot)
                self.program.release()
            if self._runtime.shader_controller:
                if os.environ.get('AUREON_HYBRID_FORCE_BACKGROUND_FAIL')=='1':raise RuntimeError('Requested hybrid shader failure test')
                from aureon_paths import resource_path
                self.hybrid_program=QOpenGLShaderProgram()
                for kind,source in ((QOpenGLShader.Vertex,resource_path('idle','gl','shaders','fullscreen.vert').read_text(encoding='utf-8')),
                                    (QOpenGLShader.Fragment,self._runtime.shader_controller.shader_source)):
                    diagnostic_stage(self,'hybrid_vertex' if kind==QOpenGLShader.Vertex else 'hybrid_fragment')
                    if not self.hybrid_program.addShaderFromSourceCode(kind,source):raise RuntimeError(self.hybrid_program.log())
                diagnostic_stage(self,'hybrid_link')
                if not self.hybrid_program.link():raise RuntimeError(self.hybrid_program.log())
                self.hybrid_vao=QOpenGLVertexArrayObject()
                if not self.hybrid_vao.create():raise RuntimeError('Hybrid fullscreen VAO allocation failed')
                self.hybrid_upload.reset()
            if self.scene.graph:
                from .instancing import Instancing
                self.instancing=Instancing(self.context())
            self.program.bind()
            diagnostic_stage(self,'geometry_buffers')
            for index,item in enumerate(self.scene.items):
                vao=QOpenGLVertexArrayObject();buffer=QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
                if not vao.create() or not buffer.create():raise RuntimeError('Orbital City VBO allocation failed')
                vao.bind();buffer.bind();packed=self._packed(item);raw=packed.tobytes();buffer.allocate(raw,len(raw))
                for location,width,offset in ((0,3,0),(1,4,12),(2,3,28)):
                    self.program.enableAttributeArray(location);self.program.setAttributeBuffer(location,0x1406,offset,width,40)
                buffer.release();instance=None
                if self.scene.graph and index in self.scene.graph.groups:
                    instance=QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
                    if not instance.create():raise RuntimeError('Instance buffer allocation failed')
                    instance.setUsagePattern(QOpenGLBuffer.DynamicDraw);instance.bind()
                    capacity=len(self.scene.graph.groups[index])*80;instance.allocate(capacity)
                    for location,offset in ((3,0),(4,16),(5,32),(6,48),(7,64)):
                        self.program.enableAttributeArray(location);self.program.setAttributeBuffer(location,0x1406,offset,4,80);self.instancing.divisor(location,1)
                    instance.release()
                vao.release()
                center=(item.pos.min(axis=0)+item.pos.max(axis=0))*.5
                self.meshes.append(dict(index=index,instance=instance,item=item,vao=vao,buffer=buffer,revision=item.revision,bytes=len(raw),center=QVector3D(*map(float,center))))
            self.program.release();self._gpu_timer.initialize()
            self._antialiasing.initialize()
            if self.reflections:self._reflection_aa.initialize()
            # The widget format may report zero even when Qt's own FBO is
            # multisampled. Query that FBO, not the shared window context.
            import ctypes
            abi=getattr(ctypes,'WINFUNCTYPE',ctypes.CFUNCTYPE)
            address=int(self.context().getProcAddress(b'glGetIntegerv') or 0)
            self._get_integer=abi(None,ctypes.c_uint,ctypes.POINTER(ctypes.c_int))(address) if address else None
            self.ready=True;self._watchdog.stop()
            self._gl_stage='ready';widget_event(self,'ready')
        except Exception as exc:self._fail(exc)
    def paintGL(self):
        if not self.ready or self._failed or self._disposed:return
        self._gl_stage='paint'
        if not self.frame_count:widget_event(self,'first_draw')
        queried=False
        try:
            start=time.perf_counter_ns();now=time.perf_counter();dt=0. if self._last_frame is None else now-self._last_frame;self._last_frame=now
            host=self.parentWidget();player=getattr(host.window(),'player',None)
            playing=player.playbackState().name=='PlayingState' if player is not None else None
            frame=SceneFrame(host._current_audio_frame(),playing,getattr(host,'_mode',None)=='audio',getattr(host.window(),'audio_visualizer_style','off'))
            self._runtime.update(dt,frame);self._perf.add('cpu_behavior',(time.perf_counter_ns()-start)/1e6)
            funcs=self.context().functions()
            display_width=max(1,round(self.width()*self.devicePixelRatioF()))
            display_height=max(1,round(self.height()*self.devicePixelRatioF()))
            advanced=getattr(host,'advanced_profile',lambda:{})()
            width,height=(background_size(display_width,display_height,host.render_quality(),
                                          getattr(host,'_fixed_render_size',None),getattr(host,'_render_size_limit',None),advanced.get('resolution'))
                          if host.render_quality()=='lowest' or 'resolution' in advanced or getattr(host,'_fixed_render_size',None) else (display_width,display_height))
            self.render_size=(width,height)
            self._scene_target=self.defaultFramebufferObject()
            lowres=(width,height)!=(display_width,display_height)
            if lowres:
                if self._output_fbo is None or self._output_fbo.size()!=QSize(width,height):
                    fmt=QOpenGLFramebufferObjectFormat()
                    fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
                    self._output_fbo=QOpenGLFramebufferObject(width,height,fmt)
                if not self._output_fbo.isValid():raise RuntimeError('Geometry scene framebuffer unavailable')
                self._scene_target=self._output_fbo.handle()
            funcs.glBindFramebuffer(0x8D40,self._scene_target)
            # QPainter changes GL state at the end of every frame. Restore
            # multisample rasterization explicitly before drawing geometry.
            if os.environ.get('AUREON_GEOMETRY_AA_OFF')=='1' or not advanced.get('antialiasing',True):funcs.glDisable(0x809D)
            else:funcs.glEnable(0x809D)
            if self._get_integer:
                import ctypes
                samples=ctypes.c_int();self._get_integer(0x80A9,ctypes.byref(samples));self._msaa_samples=samples.value
            self._msaa_active=self._msaa_samples>0 and bool(funcs.glIsEnabled(0x809D))
            funcs.glDisable(0x0C11);funcs.glDisable(0x0B44);funcs.glEnable(0x0B71);funcs.glDepthFunc(0x0203)
            funcs.glDepthMask(True);funcs.glDisable(0x0BE2);funcs.glEnable(0x8642)
            funcs.glViewport(0,0,width,height);funcs.glClearColor(3/255,5/255,11/255,1);funcs.glClear(0x4000|0x0100)
            if not self._suspended:
                for token,gpu in self._gpu_timer.poll():
                    if token==self._generation:self._perf.add('gpu_scene',gpu)
            started=time.perf_counter_ns();queried=False if self._suspended else self._gpu_timer.begin(self._generation)
            view=self._runtime.view;matrix=view.viewMatrix();projection=view.projectionMatrix(width,height)
            instance_data={};lights=[]
            if self.scene.graph:instance_data,lights=self.scene.graph.prepare(matrix,projection)
            if self.reflections:
                self._render_reflections(funcs,matrix,projection,width,height,lights)
                funcs.glBindFramebuffer(0x8D40,self._scene_target);funcs.glViewport(0,0,width,height)
                funcs.glDepthMask(True);funcs.glDisable(0x0BE2);funcs.glEnable(0x0B71);funcs.glDepthFunc(0x0203)
                if os.environ.get('AUREON_GEOMETRY_AA_OFF')=='1' or not advanced.get('antialiasing',True):funcs.glDisable(0x809D)
                else:funcs.glEnable(0x809D)
            if self.hybrid_program:self._draw_background(funcs,matrix,width,height)
            self._draw_meshes(funcs,matrix,projection,instance_data,lights)
            if advanced.get('antialiasing',True):
                self._antialiasing.apply(self._scene_target,width,height)
            else:
                self._antialiasing.framebuffer=None
            if lowres:
                extra=self.context().extraFunctions()
                extra.glBindFramebuffer(0x8CA8,self._scene_target)
                extra.glBindFramebuffer(0x8CA9,self.defaultFramebufferObject())
                extra.glBlitFramebuffer(0,0,width,height,0,0,display_width,display_height,0x4000,0x2601)
                extra.glBindFramebuffer(0x8D40,self.defaultFramebufferObject())
                funcs.glViewport(0,0,display_width,display_height)
            if queried:self._gpu_timer.end();queried=False
            self.draw_cpu.append((time.perf_counter_ns()-started)/1e6)
            funcs.glDepthMask(True);funcs.glDisable(0x0B71);funcs.glDisable(0x0BE2);funcs.glDisable(0x8642)
            painter=QPainter(self)
            try:
                theme=host._theme or {'text':'#e7e8ea','muted':'#8b9098'}
                host._paint_content(painter,self.width(),self.height(),QColor(theme['text']),QColor(theme['muted']))
                chrome=getattr(host.window(),'chrome_layout',None)
                if chrome:chrome.paint_gl_chrome(painter,self)
            finally:painter.end()
            self.frame_count+=1
            if self.frame_count==1:widget_event(self,'first_frame')
        except Exception as exc:self._fail(exc)
        finally:
            if queried:self._gpu_timer.end()
    def _draw_meshes(self,funcs,matrix,projection,instance_data,lights,reflected=False,plane=(0.,0.,1.,0.)):
        view=self._runtime.view
        light=matrix.mapVector(QVector3D(-.4,-.5,.8));p=self.program;u=self.uploader
        if not p.bind():raise RuntimeError('Orbital City material bind failed')
        self.textures.bind()
        if self.hybrid_program:
            from aureon_packages.scene_v2_runtime import UniformArray
            for name,value in self._shared_values.items():
                if isinstance(value,UniformArray):u.array(funcs,p,name,value.values)
                elif isinstance(value,(tuple,list)):u.vector(funcs,p,name,value)
                else:u.scalar(funcs,p,name,value)
        p.setUniformValue('projection',projection)
        inverse,ok=matrix.inverted();p.setUniformValue('u_inverse_view',inverse)
        u.scalar(funcs,p,'u_reflection_pass',float(reflected))
        u.vector(funcs,p,'u_reflection_plane',plane)
        if self.reflections:self._bind_reflections(funcs,p,u,reflected)
        u.vector(funcs,p,'keyLight',(light.x(),light.y(),light.z()));u.vector(funcs,p,'fogColor',view.fog_color)
        u.scalar(funcs,p,'sceneTime',view.scene_time)
        u.scalar(funcs,p,'qualityLevel',{'low':0.,'medium':1.,'high':2.}[self._runtime.quality])
        u.scalar(funcs,p,'musicPulse',self._runtime.response.low)
        u.scalar(funcs,p,'ambientLight',self._runtime.params['ambient'])
        u.scalar(funcs,p,'planetFill',self._runtime.params['planet_fill'])
        fill=matrix.mapVector(QVector3D(*self._runtime.definition.document['environment']['fill_origin']).normalized())
        u.vector(funcs,p,'fillLight',(fill.x(),fill.y(),fill.z()))
        u.scalar(funcs,p,'u_mesh_light_count',len(lights))
        for index in range(4):
            pos,color,radius,gain=lights[index] if index<len(lights) else ((0.,0.,0.),(0.,0.,0.),1.,0.)
            u.vector(funcs,p,f'u_mesh_light{index}_pos',pos);u.vector(funcs,p,f'u_mesh_light{index}_color',color)
            u.scalar(funcs,p,f'u_mesh_light{index}_radius',radius);u.scalar(funcs,p,f'u_mesh_light{index}_gain',gain)
        meshes=sorted(self.meshes,key=lambda m:m['item'].depth)
        alpha=[m for m in meshes if m['item'].blend and getattr(m['item'],'blend_mode','additive')=='alpha']
        if alpha:
            # Opt-in glass: existing opaque/additive order is unchanged. Glass
            # never writes depth and follows opaque geometry, furthest first.
            opaque=[m for m in meshes if m not in alpha]
            alpha.sort(key=lambda m:(matrix*m['item'].model).map(m['center']).z())
            meshes=opaque+alpha
        for mesh in meshes:
            if reflected and mesh['item'].material_values.get('u_mat_reflector',0)>0:continue
            instances=instance_data.get(mesh['index'])
            if mesh['instance'] is not None and instances is None:continue
            u.scalar(funcs,p,'u_mesh_instanced',float(instances is not None))
            item=mesh['item'];count=getattr(item,'draw_count',len(item.pos))
            if item.revision!=mesh['revision']:
                mesh['buffer'].bind();raw=self._packed(item).tobytes()
                if len(raw)==mesh['bytes']:mesh['buffer'].write(0,raw,len(raw))
                else:mesh['buffer'].allocate(raw,len(raw));mesh['bytes']=len(raw)
                mesh['buffer'].release();mesh['revision']=item.revision
            modelview=matrix if instances is not None else matrix*item.model;p.setUniformValue('modelView',modelview);p.setUniformValue('normalMatrix',modelview.normalMatrix())
            p.setUniformValue('u_mesh_model',QMatrix4x4() if instances is not None else item.model)
            for name,kind in self._runtime.definition.extensions.uniform_types.items():
                value=item.material_values.get(name,0. if kind=='float' else (0.,)*int(kind[-1]))
                if kind=='float':u.scalar(funcs,p,name,value)
                else:u.vector(funcs,p,name,value)
            for key,value in dict(fogDensity=view.fog_density*item.fog,lit=item.lit,emission=item.emission*view.glow,
                rim=item.rim*view.glow,points=float(item.mode==0),pointSize=item.point_size,pointPixels=item.point_pixels,materialStyle=item.style,
                surfaceGain=getattr(item,'surface_gain',1.)).items():u.scalar(funcs,p,key,value)
            funcs.glDepthMask(not item.blend)
            if item.blend:
                funcs.glEnable(0x0BE2)
                if getattr(item,'blend_mode','additive')=='alpha':
                    # RGB is straight-alpha; preserve an opaque destination's
                    # alpha so Qt composition/grab does not unpremultiply it.
                    funcs.glBlendFuncSeparate(0x0302,0x0303,1,0x0303)
                else:funcs.glBlendFunc(0x0302,1)
            else:funcs.glDisable(0x0BE2)
            mesh['vao'].bind()
            if instances is not None:
                raw=instances.tobytes();mesh['instance'].bind();mesh['instance'].write(0,raw,len(raw));mesh['instance'].release()
                self.instancing.draw(item.mode,0,count,len(instances))
            else:funcs.glDrawArrays(item.mode,0,count)
            mesh['vao'].release()
        if self.reflections:
            for unit in (len(self.textures.items),len(self.textures.items)+1):
                funcs.glActiveTexture(0x84C0+unit);funcs.glBindTexture(0x0DE1,0)
        self.textures.release();p.release()
    def _render_reflections(self,funcs,matrix,projection,width,height,lights):
        r=self.reflections;start=time.perf_counter_ns();r.records=[]
        r.stats.update(enabled=not r.disabled and not r.force_off,passes=0)
        selected=r.select(matrix)
        if not selected:return
        from .reflections import mirror_matrix
        try:
            if os.environ.get('AUREON_REFLECTION_FORCE_FAIL')=='1':raise RuntimeError('Requested reflection failure test')
            r.ensure(width,height);inverse,ok=matrix.inverted()
            for slot,index in enumerate(selected):
                plane=r.config['planes'][index]['equation'];reflected=matrix*mirror_matrix(plane)
                fbo=r.targets[slot]
                if not fbo.bind():raise RuntimeError('Reflection target bind failed')
                funcs.glViewport(0,0,fbo.width(),fbo.height());funcs.glDepthMask(True);funcs.glEnable(0x0B71)
                funcs.glDisable(0x0BE2);funcs.glClearColor(.003,.005,.011,1.);funcs.glClear(0x4000|0x0100)
                if self.hybrid_program:self._draw_background(funcs,reflected,fbo.width(),fbo.height())
                instances={}
                if self.scene.graph:instances,_=self.scene.graph.prepare(reflected,projection,geometry_only=True)
                transform=reflected*inverse;reflected_lights=[]
                for pos,color,radius,gain in lights:
                    p=transform.map(QVector3D(*pos));reflected_lights.append(((p.x(),p.y(),p.z()),color,radius,gain))
                funcs.glEnable(0x3000)
                self._draw_meshes(funcs,reflected,projection,instances,reflected_lights,True,plane)
                funcs.glDisable(0x3000)
                if getattr(self.parentWidget(),'advanced_profile',lambda:{})().get('antialiasing',True):
                    self._reflection_aa.apply(fbo.handle(),fbo.width(),fbo.height())
                else:
                    self._reflection_aa.framebuffer=None
                r.records.append((index+1,fbo.texture(),projection*reflected))
            r.stats.update(passes=len(r.records),cpu_ms=(time.perf_counter_ns()-start)/1e6)
        except Exception as exc:r.fail(exc)
        finally:
            funcs.glDisable(0x3000);funcs.glBindFramebuffer(0x8D40,self._scene_target);funcs.glViewport(0,0,width,height)
    def _bind_reflections(self,funcs,p,u,reflected):
        records=[] if reflected else self.reflections.records
        for slot in range(2):
            unit=len(self.textures.items)+slot
            funcs.glActiveTexture(0x84C0+unit)
            index,texture,matrix=records[slot] if slot<len(records) else (0,0,QMatrix4x4())
            funcs.glBindTexture(0x0DE1,texture)
            if texture:
                for key,value in ((0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F)):funcs.glTexParameteri(0x0DE1,key,value)
            u.scalar(funcs,p,f'u_reflection{slot}_id',index)
            p.setUniformValue(f'u_reflection{slot}_matrix',matrix)
        funcs.glActiveTexture(0x84C0)
    def _swapped(self):
        now=time.perf_counter()
        if self._swap_time:self._perf.add('composition',(now-self._swap_time)*1000)
        self._swap_time=now
    def _draw_background(self,funcs,matrix,width,height):
        from aureon_packages.scene_v2_runtime import UniformArray
        inverse,ok=matrix.inverted()
        if not ok:raise RuntimeError('Hybrid camera matrix is singular')
        def xyz(v):return (v.x(),v.y(),v.z())
        view=self._runtime.view
        values=dict(self._runtime.shader_controller.values)
        values.update(u_resolution=(width,height),u_camera_pos=xyz(inverse.map(QVector3D())),
            u_camera_target=xyz(view.opts['center']),u_camera_fov=view.opts['fov'],
            u_hyb_right=xyz(inverse.mapVector(QVector3D(1,0,0))),
            u_hyb_up=xyz(inverse.mapVector(QVector3D(0,1,0))),
            u_hyb_forward=xyz(inverse.mapVector(QVector3D(0,0,-1))),
            u_hyb_clip=(view.camera['near'],view.camera['far']))
        program=self.hybrid_program;upload=self.hybrid_upload
        self._shared_values=values
        if not program.bind():raise RuntimeError('Hybrid background bind failed')
        for name,value in values.items():
            if isinstance(value,UniformArray):upload.array(funcs,program,name,value.values)
            elif isinstance(value,(tuple,list)):upload.vector(funcs,program,name,value)
            else:upload.scalar(funcs,program,name,value)
        funcs.glDisable(0x0BE2);funcs.glDepthMask(True);funcs.glDepthFunc(0x0207)
        self.hybrid_vao.bind();funcs.glDrawArrays(0x0004,0,3);self.hybrid_vao.release();program.release()
        funcs.glDepthFunc(0x0203)
    def performance_snapshot(self):
        data=self._perf.snapshot();data.update(scene=self._style,gpu_available=self._gpu_timer.supported,gpu_reason=self._gpu_timer.reason,
            gpu_sample_stride=self._gpu_timer.sample_stride,
            antialiasing=(f'MSAA {self._msaa_samples}x + FXAA' if self._msaa_active else 'FXAA') if self._antialiasing.snapshot()['enabled'] else (f'MSAA {self._msaa_samples}x' if self._msaa_active else 'off'),
            antialiasing_details=dict(msaa_samples=self._msaa_samples,msaa_active=self._msaa_active,scene=self._antialiasing.snapshot(),reflection=self._reflection_aa.snapshot()),textures=dict(self.textures.stats),
            hybrid=dict(enabled=bool(self.hybrid_program),shared_depth=True,shared_clock=True,shared_audio=True,standard_library=bool(self._runtime.definition.background)),
            geometry=dict(batches=len(self.meshes),buildings=self.scene.building_count,vertices=self.scene.vertex_count,
                live_buffers=len(self.meshes),cpu_draw_ms=sum(self.draw_cpu)/len(self.draw_cpu) if self.draw_cpu else None,
                audio_packets=self._runtime.bridge.packets,audio_peak=self._runtime.bridge.peak_input,synthetic_demo=self._runtime.bridge.demo))
        if self.scene.graph:
            g=self.scene.graph;data['geometry']['objects']=dict(nodes=len(g.world),templates=len(g.groups),visible=g.visible,culled=g.culled,instance_draw_calls=g.draw_calls,submitted_instance_vertices=g.submitted_vertices,authored_lights=len(g.light_values),max_active_lights=(1,2,4)[g.tier],instance_buffer_bytes=sum(len(indices)*80 for indices in g.groups.values()))
            if g.light_slots:data['geometry']['lighting']=dict(g.light_stats)
        if self.reflections:data['geometry']['reflections']=dict(self.reflections.stats)
        return data
    def reset_performance_stats(self):self._generation+=1;self._perf.reset();self._swap_time=None;self.draw_cpu.clear()
    def suspend_performance_queries_for_restyle(self):self._suspended=True
    def resume_performance_queries_after_restyle(self):self._suspended=False
    def showEvent(self,event):
        super().showEvent(event);self._last_frame=None
        if not self._failed and not self._disposed:
            self._timer.start()
            if not self.ready:self._watchdog.start()
    def hideEvent(self,event):self._timer.stop();self._watchdog.stop();self._last_frame=None;super().hideEvent(event)
    def cleanup(self):
        self._gl_stage='cleanup';widget_event(self,'context_cleanup')
        self.ready=False
        if self.context() and self.context().isValid():
            self.makeCurrent()
            for mesh in self.meshes:
                if mesh['instance'] is not None:mesh['instance'].destroy()
                mesh['buffer'].destroy();mesh['vao'].destroy()
            if self.reflections:self.reflections.destroy()
            self._antialiasing.destroy();self._reflection_aa.destroy()
            self._output_fbo=None
            self.textures.destroy()
            if self.program:self.program.removeAllShaders()
            if self.hybrid_program:self.hybrid_program.removeAllShaders()
            if self.hybrid_vao:self.hybrid_vao.destroy()
            self._gpu_timer.destroy();self.doneCurrent()
        self._output_fbo=None;self._scene_target=0
        self.meshes=[];self.program=None;self.hybrid_program=None;self.hybrid_vao=None;self.instancing=None
    def dispose(self):
        if self._disposed:return
        widget_event(self,'stop')
        self._disposed=True;self._timer.stop();self._watchdog.stop();self.hide();self.cleanup();self._runtime.dispose();self.deleteLater()
