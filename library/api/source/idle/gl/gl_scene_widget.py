"""One fullscreen triangle in a private QOpenGLWidget; no video imports."""
from pathlib import Path
import logging
import time

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLShader, QOpenGLShaderProgram, QOpenGLVertexArrayObject, QOpenGLFramebufferObject
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from .quality import QUALITY
from idle.render_quality import background_size
from aureon_visual_quality import effect_defines
from .scene_textures import SceneTextures
from .antialiasing import SceneAntialiasing
from aureon_content import get_registry
from aureon_packages.scene_v2_runtime import UniformArray
from aureon_content.models import BuiltinSceneRuntime, SceneFrame
from aureon_performance import ScenePerformanceStats, AsyncGpuTimer
from aureon_gl_uniforms import CachedUniformUploader
from aureon_resource_probe import format_resource_snapshot
from aureon_developer import option_enabled
from aureon_benchmark_log import log_sample
from aureon_gl_diagnostics import stage as diagnostic_stage, widget_event



class GLSceneWidget(QOpenGLWidget):
    failed = Signal(str)

    # OPT 06.4: process-wide logical/Qt widget accounting.  These are diagnostic
    # counters only; they never participate in rendering or scene selection.
    _life_next_serial = 0
    _life_created = 0
    _life_disposed = 0
    _life_destroyed = 0
    _life_logical_live = set()
    _life_qt_live = set()

    @classmethod
    def _lifecycle_snapshot(cls):
        return (len(cls._life_logical_live), len(cls._life_qt_live),
                cls._life_created, cls._life_disposed, cls._life_destroyed)

    @classmethod
    def _qt_object_destroyed(cls, serial, scene):
        try:
            orphaned = serial in cls._life_logical_live
            cls._life_logical_live.discard(serial)
            cls._life_qt_live.discard(serial)
            cls._life_destroyed += 1
            logical, qt_live, created, disposed, destroyed = cls._lifecycle_snapshot()
            if option_enabled('lifecycle_diagnostics'):
                logging.getLogger('aureon').info(
                    '[AURS LIFE] scene.destroyed scene=%s serial=%d orphaned=%s logical_live=%d qt_live=%d created=%d disposed=%d destroyed=%d %s',
                    scene, serial, orphaned, logical, qt_live, created, disposed, destroyed,
                    format_resource_snapshot())
        except Exception:
            # QObject destruction must never be made unsafe by diagnostics.
            pass

    def __init__(self, parent, quality="medium", style="orbital_dawn_gl", *, entry=None):
        load_started = time.perf_counter()
        super().__init__()
        self._load_created_at = load_started
        self._first_frame_load_logged = False
        self._style = str(style)
        self._entry = entry if entry is not None else get_registry().resolve(self._style, 'scene')
        if self._entry is None or self._entry.renderer not in ('builtin.gl', 'scene.fullscreen_frag.v1', 'scene.fullscreen_frag.v2'):
            raise ValueError(f'Unknown GL scene style: {self._style}')
        self._reactive = self._style == self._entry.reactive_id
        self._base_style = self._entry.id
        self._fragment_shader = self._entry.fragment
        cls = type(self)
        cls._life_next_serial += 1
        self._life_serial = cls._life_next_serial
        self._life_disposed = False
        cls._life_created += 1
        cls._life_logical_live.add(self._life_serial)
        cls._life_qt_live.add(self._life_serial)
        self.destroyed.connect(
            lambda _obj=None, serial=self._life_serial, scene=self._base_style:
                GLSceneWidget._qt_object_destroyed(serial, scene))
        logical, qt_live, created, disposed, destroyed = cls._lifecycle_snapshot()
        if option_enabled('lifecycle_diagnostics'):
            logging.getLogger('aureon').info(
                '[AURS LIFE] scene.create scene=%s serial=%d logical_live=%d qt_live=%d created=%d disposed=%d destroyed=%d %s',
                self._base_style, self._life_serial, logical, qt_live, created, disposed, destroyed,
                format_resource_snapshot())
        runtime_started = time.perf_counter()
        if quality == 'extreme' and not self._entry.supports_extreme:
            quality = 'high'
        self._runtime = (self._entry.factory(quality, self._reactive) if self._entry.source == 'package'
                         else BuiltinSceneRuntime(self._entry, quality, self._reactive))
        if self._entry.camera_presets and hasattr(self._runtime,'set_camera_preset'):
            from aureon_camera_controls import camera_choice
            self._runtime.set_camera_preset(camera_choice(self._entry.id,self._entry.camera_presets))
        self._load_runtime_ms = (time.perf_counter()-runtime_started)*1000.0
        logging.getLogger('aureon').info(
            '[AURS LOAD] scene.runtime scene=%s source=%s quality=%s ms=%.3f',
            self._base_style, self._entry.source, getattr(self._runtime.scene, 'quality', quality), self._load_runtime_ms)
        fmt = QSurfaceFormat()
        fmt.setRenderableType(QSurfaceFormat.OpenGL)
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setDepthBufferSize(0)
        fmt.setStencilBufferSize(0)
        fmt.setSamples(0)
        fmt.setSwapInterval(0 if getattr(parent, '_benchmark_host', False) else 1)
        self.setFormat(fmt)
        # Compose into the owner's backing store instead of a separate native
        # GL child surface. PlayerWindow prepares this composition before show
        # so adding a scene does not recreate the native player window.
        self.setParent(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.NoFocus)
        self.scene = self._runtime.scene
        self._program = None
        self._vao = None
        self._failed = False
        self._disposed = False
        self.ready = False
        self.frame_count = 0
        self._last_frame = None
        self._perf = ScenePerformanceStats(maxlen=900)
        self._perf_generation = 0
        self._perf_last_swap = None
        self._perf_last_log = time.perf_counter()
        self._benchmark_last_log = time.perf_counter()
        self._gpu_timer = AsyncGpuTimer(sample_stride=4, query_count=4)
        self._uniform_uploader = CachedUniformUploader()
        self._textures = SceneTextures()
        self._antialiasing = SceneAntialiasing()
        # OPT01 GPU timing uses raw context-owned OpenGL query ids. Theme/QSS
        # restyling never destroys query objects explicitly; if Qt replaces the
        # context, the timer detects the new context lazily from paintGL.
        self._gpu_timer_restyle_suspended = False
        self._gpu_timer_reinit_pending = False
        self.frameSwapped.connect(self._on_frame_swapped)
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.setInterval(0 if getattr(parent, '_benchmark_host', False) else 16)
        self._timer.timeout.connect(self.update)
        self._watchdog = QTimer(self)
        self._watchdog.setSingleShot(True)
        self._watchdog.setInterval(2500)
        self._watchdog.timeout.connect(self._check_context)

    def _check_context(self):
        if not self._disposed and self.isVisible() and not self.ready:
            self._fail("OpenGL context did not initialize")

    def _fail(self, reason):
        if self._failed or self._disposed:
            return
        self._failed = True
        self._timer.stop()
        self._watchdog.stop()
        logging.getLogger("aureon").warning("%s fallback: %s", self._style, reason)
        widget_event(self,'failure',reason=str(reason))
        # Never destroy a GL widget from inside initializeGL/paintGL.
        QTimer.singleShot(0, lambda: self.failed.emit(str(reason)) if not self._disposed else None)

    def initializeGL(self):
        if self._disposed or self._failed:
            return
        init_started = time.perf_counter()
        vertex_ms = fragment_ms = link_ms = 0.0
        try:
            diagnostic_stage(self,'context')
            context = self.context()
            if not context or not context.isValid():
                raise RuntimeError("Invalid OpenGL context")
            from .device_info import context_device_info
            self.device_info = context_device_info(context)
            self.parentWidget().window()._gl_device_info = dict(self.device_info)
            context.aboutToBeDestroyed.connect(self.cleanup, Qt.DirectConnection)
            self._program = QOpenGLShaderProgram()
            root = Path(__file__).with_name("shaders")
            if self._entry.source == 'package':
                source = self._runtime.shader_source
            else:
                source = (root / self._fragment_shader).read_text(encoding="utf-8")
                profile = getattr(self.parentWidget(), 'advanced_profile', lambda: {})()
                steps, octaves, layers = QUALITY["high" if self.scene.quality == "extreme" else self.scene.quality]
                defines = f"#define GAS_STEPS {steps}\n#define OCTAVES {octaves}\n#define STAR_LAYERS {layers}\n"
                defines += effect_defines(profile)
                defines += f"#define AUR_STELLAR_OCTAVES {octaves if 'detail' in profile else 4}\n"
                if self._fragment_shader == 'lava_horizon.frag':
                    extreme = self.scene.quality == 'extreme'
                    defines += f"#define SAT_EXTREME_HIGHLIGHTS {int(profile.get('highlights', extreme))}\n"
                    defines += f"#define SAT_EXTREME_SHADOWS {int(profile.get('soft_shadows', extreme))}\n"
                    defines += f"#define SAT_WIRE_SEGMENTS {8 if extreme else 4}\n#define SAT_RIM_SEGMENTS {64 if extreme else 32}\n"
                source = source.replace("// QUALITY_DEFINES", defines)
            add_shader = self._program.addShaderFromSourceCode
            import hashlib
            self._gl_shader_fingerprint={'name':self._fragment_shader or self._entry.id,
                                         'sha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
                                         'lines':len(source.splitlines())}
            widget_event(self,'shader_source',**self._gl_shader_fingerprint)
            cacheable_api = False
            if self._entry.shader_cache:
                cacheable = getattr(self._program, "addCacheableShaderFromSourceCode", None)
                if callable(cacheable):
                    add_shader = cacheable
                    cacheable_api = True
            stage_started = time.perf_counter()
            diagnostic_stage(self,'vertex_shader')
            if not add_shader(QOpenGLShader.Vertex, (root / "fullscreen.vert").read_text(encoding="utf-8")):
                raise RuntimeError(self._program.log())
            vertex_ms = (time.perf_counter()-stage_started)*1000.0
            stage_started = time.perf_counter()
            diagnostic_stage(self,'fragment_shader')
            if not add_shader(QOpenGLShader.Fragment, source):
                raise RuntimeError(self._program.log())
            fragment_ms = (time.perf_counter()-stage_started)*1000.0
            stage_started = time.perf_counter()
            diagnostic_stage(self,'shader_link')
            if not self._program.link():
                raise RuntimeError(self._program.log())
            link_ms = (time.perf_counter()-stage_started)*1000.0
            diagnostic_stage(self,'resources')
            # OPT 02: locations belong to this linked program.  Resolve fixed
            # host uniforms now; scene-specific names are cached lazily on first use.
            self._uniform_uploader.reset()
            self._uniform_uploader.prewarm(
                self._program, ("u_resolution", "u_mouse", "u_zones0", "u_zones1")
            )
            definition = getattr(self._runtime, 'definition', None)
            self._textures.create(getattr(definition, 'textures', ()), self._program)
            self._vao = QOpenGLVertexArrayObject()
            if not self._vao.create():
                raise RuntimeError("Could not create fullscreen VAO")
            # A full-screen fragment scene has no polygon edges for MSAA to
            # smooth. Filter its color image, then draw the UI at native size.
            self._antialiasing.initialize()
            # OPT 01: optional asynchronous GPU timer queries. Failure is not
            # fatal; Info reports GPU timing as unavailable instead of 0 ms.
            # Do not create them while a global QSS/theme restyle is in flight.
            if self._gpu_timer_restyle_suspended:
                self._gpu_timer_reinit_pending = True
            else:
                self._gpu_timer.initialize()
                self._gpu_timer_reinit_pending = False
            self.ready = True
            self._gl_stage='ready'
            widget_event(self,'ready')
            self._watchdog.stop()
            try:
                program_id = int(self._program.programId()) if self._program is not None else 0
            except Exception:
                program_id = 0
            try:
                vao_id = int(self._vao.objectId()) if self._vao is not None else 0
            except Exception:
                vao_id = 0
            context_handle = int(getattr(self._gpu_timer, '_context_handle', 0) or 0)
            if option_enabled('lifecycle_diagnostics'):
                logging.getLogger('aureon').info(
                    '[AURS LIFE] scene.resources scene=%s serial=%d context=0x%x program=%d vao=%d queries=%d',
                    self._base_style, self._life_serial, context_handle, program_id, vao_id,
                    len(getattr(self._gpu_timer, '_ids', ()) or ()))
            logging.getLogger('aureon').info(
                '[AURS LOAD] scene.initialize scene=%s vertex_ms=%.3f fragment_ms=%.3f link_ms=%.3f total_ms=%.3f cacheable=%s cache_api=%s',
                self._base_style, vertex_ms, fragment_ms, link_ms, (time.perf_counter()-init_started)*1000.0,
                bool(self._entry.shader_cache), cacheable_api)
        except Exception as exc:
            self._fail(exc)

    def paintGL(self):
        if not self.ready or self._failed or self._disposed:
            return
        try:
            self._gl_stage='paint'
            if not self.frame_count:
                widget_event(self,'first_draw')
            # If initializeGL happened during a restyle, create raw query ids only
            # now, with the final widget context current. No native teardown needed.
            if self._gpu_timer_reinit_pending and not self._gpu_timer_restyle_suspended:
                self._gpu_timer.initialize()
                self._gpu_timer_reinit_pending = False

            # Consume only already-completed GPU queries. No glFinish and no
            # same-frame result wait are used by OPT 01.
            gpu_results = [] if self._gpu_timer_restyle_suspended else self._gpu_timer.poll()
            for token, gpu_ms in gpu_results:
                if token == self._perf_generation:
                    self._perf.add('gpu_scene', gpu_ms)

            now = time.perf_counter()
            dt = 0.0 if self._last_frame is None else now - self._last_frame
            self._last_frame = now
            host = self.parentWidget()
            player = getattr(host.window(), 'player', None)
            playing = player.playbackState().name == 'PlayingState' if player is not None else None
            frame = SceneFrame(host._current_audio_frame(), playing,
                               getattr(host, '_mode', None) == 'audio',
                               getattr(host.window(), 'audio_visualizer_style', 'off'))

            update_started = time.perf_counter_ns()
            self._runtime.update(dt, frame)
            benchmark_clock = getattr(host, '_benchmark_elapsed', None)
            if callable(benchmark_clock):
                self.scene.seconds = benchmark_clock()
            update_finished = time.perf_counter_ns()

            prep_started = time.perf_counter_ns()
            values, zones = self._runtime.uniforms()
            prep_finished = time.perf_counter_ns()

            timings = None
            performance_timings = getattr(self._runtime, 'performance_timings', None)
            if callable(performance_timings):
                try:
                    timings = performance_timings()
                except Exception:
                    timings = None
            if isinstance(timings, dict) and timings.get('cpu_behavior') is not None:
                self._perf.add('cpu_behavior', timings['cpu_behavior'])
            else:
                self._perf.add('cpu_behavior', (update_finished-update_started)/1_000_000.0)
            if isinstance(timings, dict) and timings.get('uniform_prep') is not None:
                self._perf.add('uniform_prep', timings['uniform_prep'])
            else:
                self._perf.add('uniform_prep', (prep_finished-prep_started)/1_000_000.0)

            funcs = self.context().functions()
            funcs.glDisable(0x0B71)  # GL_DEPTH_TEST
            funcs.glDisable(0x0BE2)  # GL_BLEND (QPainter may leave it enabled)
            funcs.glDisable(0x0C11)  # GL_SCISSOR_TEST
            width = max(1, round(self.width() * self.devicePixelRatioF()))
            height = max(1, round(self.height() * self.devicePixelRatioF()))
            display_width, display_height = width, height
            width, height = background_size(width, height, host.render_quality(),
                                            getattr(host, '_fixed_render_size', None),
                                            getattr(host, '_render_size_limit', None),
                                            getattr(host, 'advanced_profile', lambda: {})().get('resolution'))
            lowres = (width, height) != (display_width, display_height)
            self.render_size = (width, height)
            antialiasing = (getattr(host, 'advanced_profile', lambda: {})().get('antialiasing', True)
                            and self._antialiasing.begin(width, height))
            if not antialiasing:
                self._antialiasing.framebuffer = None
            if not antialiasing:
                funcs.glBindFramebuffer(0x8D40, self.defaultFramebufferObject())
            if lowres and not antialiasing:
                fbo = getattr(self, '_output_fbo', None)
                if fbo is None or fbo.size() != QSize(width, height):
                    self._output_fbo = QOpenGLFramebufferObject(width, height)
                if not self._output_fbo.isValid() or not self._output_fbo.bind():
                    raise RuntimeError('External scene framebuffer unavailable')
            funcs.glViewport(0, 0, width, height)
            if not self._program.bind():
                raise RuntimeError("Shader bind failed")
            self._vao.bind()

            upload_started = time.perf_counter_ns()
            self._textures.bind()
            uploader = self._uniform_uploader
            uploader.vector(funcs, self._program, "u_resolution", (width, height))
            uploader.vector(funcs, self._program, "u_mouse", (host._mouse_x - .5, .5 - host._mouse_y))
            for name, value in values.items():
                # OPT 02: location lookup happens once per linked program.  A cached
                # -1 skips uniforms optimized away by GLSL.  Arrays are uploaded in
                # one glUniform*fv call when the active Qt binding supports it.
                if isinstance(value, UniformArray):
                    uploader.array(funcs, self._program, name, value.values)
                elif isinstance(value, tuple):
                    uploader.vector(funcs, self._program, name, value)
                else:
                    uploader.scalar(funcs, self._program, name, value)
            uploader.vector(funcs, self._program, "u_zones0", zones[:4])
            uploader.vector(funcs, self._program, "u_zones1", zones[4:8])
            upload_finished = time.perf_counter_ns()
            self._perf.add('uniform_upload', (upload_finished-upload_started)/1_000_000.0)

            queried = False if self._gpu_timer_restyle_suspended else self._gpu_timer.begin(self._perf_generation)
            funcs.glDrawArrays(0x0004, 0, 3)  # GL_TRIANGLES
            self._textures.release()
            self._vao.release()
            self._program.release()

            if antialiasing:
                self._antialiasing.present(self.defaultFramebufferObject(), display_width, display_height)
            elif lowres:
                extra = self.context().extraFunctions()
                extra.glBindFramebuffer(0x8CA8, self._output_fbo.handle())  # READ_FRAMEBUFFER
                extra.glBindFramebuffer(0x8CA9, self.defaultFramebufferObject())  # DRAW_FRAMEBUFFER
                extra.glBlitFramebuffer(0, 0, width, height, 0, 0, display_width, display_height,
                                        0x4000, 0x2601)  # COLOR_BUFFER_BIT, LINEAR
                extra.glBindFramebuffer(0x8D40, self.defaultFramebufferObject())
                funcs.glViewport(0, 0, display_width, display_height)
            if queried:
                self._gpu_timer.end()

            # Existing content painter, within this FBO, keeps the background opaque
            # and requires no always-on-top/native window or extra overlay surface.
            painter = QPainter(self)
            try:
                painter.setRenderHint(QPainter.Antialiasing)
                theme = host._theme or {"text": "#e7e8ea", "muted": "#8b9098"}
                host._paint_content(painter, self.width(), self.height(), QColor(theme["text"]), QColor(theme["muted"]))
                chrome = getattr(host.window(), 'chrome_layout', None)
                if chrome is not None:
                    chrome.paint_gl_chrome(painter, self)
                if host._drag_active:
                    painter.setPen(QColor(145, 198, 235, 170))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRoundedRect(self.rect().adjusted(12, 12, -12, -12), 10, 10)
            finally:
                painter.end()
            self.frame_count += 1
            if not self._first_frame_load_logged:
                self._first_frame_load_logged = True
                widget_event(self,'first_frame')
                logging.getLogger('aureon').info(
                    '[AURS LOAD] scene.first_frame scene=%s since_widget_ms=%.3f runtime_ms=%.3f',
                    self._base_style, (time.perf_counter()-self._load_created_at)*1000.0, self._load_runtime_ms)
        except Exception as exc:
            self._fail(exc)

    def _on_frame_swapped(self):
        now = time.perf_counter()
        if self._perf_last_swap is not None:
            self._perf.add('composition', (now-self._perf_last_swap)*1000.0)
        self._perf_last_swap = now
        # One aggregate diagnostic line roughly every ten seconds. This is
        # intentionally much slower than the render loop.
        if now-self._perf_last_log >= 10.0:
            self._perf_last_log = now
            snap = self.performance_snapshot()
            comp = snap.get('composition') or {}
            if comp.get('samples', 0) >= 30:
                def avg(name):
                    metric = snap.get(name) or {}
                    value = metric.get('average')
                    return 'N/A' if value is None else f'{value:.3f}'
                logging.getLogger('aureon').info(
                    '[AURS PERF] %s | CPU %s ms | prep %s ms | upload %s ms | GPU %s ms | frame avg %s ms | p95 %.3f ms | max %.3f ms',
                    self._style, avg('cpu_behavior'), avg('uniform_prep'), avg('uniform_upload'),
                    avg('gpu_scene') if snap.get('gpu_available') else 'N/A', avg('composition'),
                    float(comp.get('p95', 0.0)), float(comp.get('max', 0.0)))

        if option_enabled('benchmark_mode') and now-self._benchmark_last_log >= 5.0:
            self._benchmark_last_log = now
            snap = self.performance_snapshot()
            comp = snap.get('composition') or {}
            def bench_avg(name):
                metric = snap.get(name) or {}
                value = metric.get('average')
                return 'N/A' if value is None else f'{float(value):.3f}'
            try:
                dpr = max(1.0, float(self.devicePixelRatioF()))
                render_size = f'{round(self.width()*dpr)}x{round(self.height()*dpr)}'
            except Exception:
                render_size = f'{self.width()}x{self.height()}'
            log_sample(
                f'scene={self._base_style} quality={getattr(self.scene, "quality", "?")} render={render_size} '
                f'CPU={bench_avg("cpu_behavior")}ms prep={bench_avg("uniform_prep")}ms '
                f'upload={bench_avg("uniform_upload")}ms GPU={bench_avg("gpu_scene") if snap.get("gpu_available") else "N/A"}ms '
                f'frame_avg={bench_avg("composition")}ms p95={float(comp.get("p95", 0.0)):.3f}ms '
                f'max={float(comp.get("max", 0.0)):.3f}ms samples={int(comp.get("samples", 0) or 0)}')

    def suspend_performance_queries_for_restyle(self):
        """Pause query issuance while a global QSS/theme restyle is applied.

        Important: do not destroy or otherwise touch native query resources here.
        Qt may preserve or replace the QOpenGLWidget context on Windows. Raw query
        ids are either still valid afterwards or reclaimed with the old context.
        """
        self._gpu_timer_restyle_suspended = True

    def resume_performance_queries_after_restyle(self):
        self._gpu_timer_restyle_suspended = False

    def reset_performance_stats(self):
        self._perf_generation += 1
        self._perf.reset()
        self._perf_last_swap = None
        self._perf_last_log = time.perf_counter()
        self._benchmark_last_log = time.perf_counter()

    def performance_snapshot(self):
        snap = self._perf.snapshot()
        snap.update({
            'textures': dict(self._textures.stats),
            'antialiasing': 'FXAA' if self._antialiasing.enabled else 'unavailable',
            'antialiasing_reason': self._antialiasing.reason,
            'scene': self._style,
            'gpu_available': bool(self._gpu_timer.supported),
            'gpu_reason': self._gpu_timer.reason,
            'gpu_sample_stride': self._gpu_timer.sample_stride,
        })
        return snap

    def showEvent(self, event):
        super().showEvent(event)
        self._last_frame = None
        self._perf_last_swap = None
        if not self._failed and not self._disposed:
            self._timer.start()
            if not self.ready:
                self._watchdog.start()

    def hideEvent(self, event):
        self._timer.stop()
        self._watchdog.stop()
        self._last_frame = None
        self._perf_last_swap = None
        super().hideEvent(event)

    def cleanup(self):
        self._gl_stage='cleanup'
        widget_event(self,'context_cleanup')
        cleanup_started = time.perf_counter()
        had_resources = self._vao is not None or self._program is not None or bool(self._textures.items)
        try:
            program_id = int(self._program.programId()) if self._program is not None else 0
        except Exception:
            program_id = 0
        try:
            vao_id = int(self._vao.objectId()) if self._vao is not None else 0
        except Exception:
            vao_id = 0
        query_count = len(getattr(self._gpu_timer, '_ids', ()) or ())
        context_handle = int(getattr(self._gpu_timer, '_context_handle', 0) or 0)
        self.ready = False
        self._last_frame = None
        context = self.context()
        context_valid = bool(context and context.isValid())
        if context_valid:
            self.makeCurrent()
            self._output_fbo = None
            self._antialiasing.destroy()
            self._textures.destroy()
            if self._vao is not None:
                self._vao.destroy()
            if self._program is not None:
                self._program.removeAllShaders()
            self._gpu_timer.destroy()
            self._vao = None
            self._program = None
            self.doneCurrent()
        else:
            self._output_fbo = None
            self._antialiasing.destroy()
            self._textures.destroy()
            self._gpu_timer.destroy()
            self._vao = None
            self._program = None
        if had_resources:
            cleared = (not self._textures.items and self._vao is None and self._program is None and
                       not getattr(self._gpu_timer, '_ids', ()) and
                       not getattr(self._gpu_timer, '_pending', ()))
            elapsed_ms = (time.perf_counter()-cleanup_started)*1000.0
            logging.getLogger('aureon').info(
                '[AURS LOAD] scene.cleanup scene=%s ms=%.3f context_valid=%s',
                self._base_style, elapsed_ms, context_valid)
            if option_enabled('lifecycle_diagnostics'):
                logging.getLogger('aureon').info(
                    '[AURS LIFE] scene.cleanup scene=%s serial=%d context=0x%x program=%d vao=%d queries=%d cleared=%s %s',
                    self._base_style, self._life_serial, context_handle, program_id, vao_id,
                    query_count, cleared, format_resource_snapshot())
        if not self._disposed and not self._failed and self.isVisible():
            self._watchdog.start()

    def dispose(self):
        if self._disposed:
            return
        widget_event(self,'stop')
        self._disposed = True
        self._timer.stop()
        self._watchdog.stop()
        self.hide()
        self.cleanup()
        if not self._life_disposed:
            self._life_disposed = True
            cls = type(self)
            cls._life_logical_live.discard(self._life_serial)
            cls._life_disposed += 1
            logical, qt_live, created, disposed, destroyed = cls._lifecycle_snapshot()
            if option_enabled('lifecycle_diagnostics'):
                logging.getLogger('aureon').info(
                    '[AURS LIFE] scene.dispose scene=%s serial=%d logical_live=%d qt_live=%d created=%d disposed=%d destroyed=%d %s',
                    self._base_style, self._life_serial, logical, qt_live, created, disposed, destroyed,
                    format_resource_snapshot())
        self.deleteLater()

