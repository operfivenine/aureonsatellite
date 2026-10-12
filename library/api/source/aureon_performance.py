"""Low-overhead rolling performance counters for the GL scene host.

OPT 01 contract:
- CPU timings use perf_counter_ns and rolling samples.
- GPU timing uses raw OpenGL timer-query ids and asynchronous polling.
  Results are consumed only after GL_QUERY_RESULT_AVAILABLE reports readiness.
  No glFinish and no same-frame wait are used.
- Query ids are context-owned and intentionally *not* deleted manually during
  QOpenGLWidget teardown/restyle. Destroying the context releases them. This
  avoids driver-sensitive QOpenGLTimerQuery.destroy() crashes on Windows.
- Missing timer-query support is reported as unavailable, never as 0 ms.
"""
from __future__ import annotations

from collections import deque
import ctypes
import math
import sys
import time


class RollingMetric:
    def __init__(self, maxlen=600):
        self.values = deque(maxlen=max(16, int(maxlen)))

    def add(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        if math.isfinite(value) and value >= 0.0:
            self.values.append(value)

    def clear(self):
        self.values.clear()

    def snapshot(self):
        if not self.values:
            return None
        values = tuple(self.values)
        ordered = sorted(values)
        index = min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))
        return {
            'current': values[-1],
            'average': sum(values) / len(values),
            'p95': ordered[index],
            'max': max(values),
            'samples': len(values),
        }


class ScenePerformanceStats:
    METRICS = ('cpu_behavior', 'uniform_prep', 'uniform_upload', 'gpu_scene', 'composition')

    def __init__(self, maxlen=600):
        self._metrics = {name: RollingMetric(maxlen) for name in self.METRICS}
        self.started_at = time.perf_counter()
        self.listener = None

    def add(self, name, value):
        metric = self._metrics.get(name)
        if metric is not None:
            metric.add(value)
            if self.listener is not None:
                self.listener(name, value)

    def reset(self):
        for metric in self._metrics.values():
            metric.clear()
        self.started_at = time.perf_counter()

    def snapshot(self):
        result = {name: metric.snapshot() for name, metric in self._metrics.items()}
        result['elapsed'] = max(0.0, time.perf_counter() - self.started_at)
        return result


class AsyncGpuTimer:
    """Asynchronous GL_TIME_ELAPSED ring without Qt timer-query wrappers.

    On Windows QOpenGLTimerQuery.destroy() proved unsafe during QOpenGLWidget
    scene/theme teardown on the target machine (native access violation).  This
    class therefore owns only integer GLuint ids.  It never calls glDeleteQueries
    from widget cleanup; ids belong to the current GL context and are reclaimed
    when that context is destroyed.  If Qt replaces the context, the next GL
    call detects the new HGLRC and creates a fresh ring.
    """

    GL_TIME_ELAPSED = 0x88BF
    GL_QUERY_RESULT = 0x8866
    GL_QUERY_RESULT_AVAILABLE = 0x8867
    _GL_LIB = None
    _GL_TRIED = False

    def __init__(self, sample_stride=4, query_count=4):
        self.sample_stride = max(1, int(sample_stride))
        self.query_count = max(2, int(query_count))
        self.supported = False
        self.reason = 'Not initialized'
        self._ids = []
        self._free = deque()
        self._pending = deque()
        self._active = None
        self._active_token = 0
        self._frame = 0
        self._context_handle = 0
        self._api = None

    @staticmethod
    def _invalid_proc(value):
        try:
            ivalue = int(value or 0)
        except Exception:
            return True
        return ivalue in (0, 1, 2, 3, -1, 0xFFFFFFFFFFFFFFFF)

    @classmethod
    def _windows_gl(cls):
        if sys.platform != 'win32':
            return None
        if cls._GL_TRIED:
            return cls._GL_LIB
        cls._GL_TRIED = True
        try:
            gl = ctypes.WinDLL('opengl32.dll')
            gl.wglGetCurrentContext.restype = ctypes.c_void_p
            gl.wglGetCurrentContext.argtypes = []
            gl.wglGetProcAddress.restype = ctypes.c_void_p
            gl.wglGetProcAddress.argtypes = [ctypes.c_char_p]
            cls._GL_LIB = gl
        except Exception:
            cls._GL_LIB = None
        return cls._GL_LIB

    @classmethod
    def _load_proc(cls, gl, name, restype, *argtypes):
        ptr = gl.wglGetProcAddress(name.encode('ascii'))
        if cls._invalid_proc(ptr):
            # A few drivers export selected entry points directly from opengl32.
            try:
                func = getattr(gl, name)
                func.restype = restype
                func.argtypes = list(argtypes)
                return func
            except Exception:
                return None
        prototype = ctypes.WINFUNCTYPE(restype, *argtypes)
        return prototype(ptr)

    @classmethod
    def _load_api(cls):
        gl = cls._windows_gl()
        if gl is None:
            return None, 0
        context = int(gl.wglGetCurrentContext() or 0)
        if not context:
            return None, 0
        GLuint = ctypes.c_uint
        GLenum = ctypes.c_uint
        GLsizei = ctypes.c_int
        GLint = ctypes.c_int
        GLuint64 = ctypes.c_uint64
        api = {
            'gen': cls._load_proc(gl, 'glGenQueries', None, GLsizei, ctypes.POINTER(GLuint)),
            'begin': cls._load_proc(gl, 'glBeginQuery', None, GLenum, GLuint),
            'end': cls._load_proc(gl, 'glEndQuery', None, GLenum),
            'get_i': cls._load_proc(gl, 'glGetQueryObjectiv', None, GLuint, GLenum, ctypes.POINTER(GLint)),
            'get_u64': cls._load_proc(gl, 'glGetQueryObjectui64v', None, GLuint, GLenum, ctypes.POINTER(GLuint64)),
        }
        if any(func is None for func in api.values()):
            return None, context
        return api, context

    @staticmethod
    def _current_context_handle():
        gl = AsyncGpuTimer._windows_gl()
        if gl is None:
            return 0
        try:
            return int(gl.wglGetCurrentContext() or 0)
        except Exception:
            return 0

    def abandon(self, reason='Not initialized'):
        """Drop Python-side query state without issuing any native GL teardown."""
        self._ids = []
        self._free.clear()
        self._pending.clear()
        self._active = None
        self._active_token = 0
        self._context_handle = 0
        self._api = None
        self.supported = False
        self.reason = reason

    def destroy(self):
        # Compatibility name for existing host cleanup. Deliberately no GL call.
        self.abandon('Not initialized')

    def initialize(self):
        self.abandon('Not initialized')
        api, context = self._load_api()
        if not context:
            self.reason = 'No current OpenGL context'
            return False
        if api is None:
            self.reason = 'OpenGL timer query unavailable'
            return False
        ids_array = (ctypes.c_uint * self.query_count)()
        try:
            api['gen'](self.query_count, ids_array)
            ids = [int(value) for value in ids_array if int(value) != 0]
            if len(ids) != self.query_count:
                raise RuntimeError('timer query allocation failed')
        except Exception as exc:
            self.reason = str(exc) or 'Timer query unavailable'
            return False
        self._api = api
        self._context_handle = context
        self._ids = ids
        self._free = deque(ids)
        self.supported = True
        self.reason = ''
        return True

    def _ensure_context(self):
        current = self._current_context_handle()
        if not current:
            self.abandon('No current OpenGL context')
            return False
        if self.supported and current == self._context_handle:
            return True
        # Old ids belong to the old context. Never touch them from the new one.
        return self.initialize()

    def poll(self):
        if not self._ensure_context():
            return []
        ready = []
        while self._pending:
            query_id, token = self._pending[0]
            available = ctypes.c_int(0)
            try:
                self._api['get_i'](query_id, self.GL_QUERY_RESULT_AVAILABLE, ctypes.byref(available))
                if not available.value:
                    break
                self._pending.popleft()
                nanoseconds = ctypes.c_uint64(0)
                self._api['get_u64'](query_id, self.GL_QUERY_RESULT, ctypes.byref(nanoseconds))
                ready.append((token, float(nanoseconds.value) / 1_000_000.0))
                self._free.append(query_id)
            except Exception as exc:
                self.abandon(str(exc) or 'Timer query failed')
                break
        return ready

    def begin(self, token=0):
        self._frame += 1
        if self._active is not None:
            return False
        if self._frame % self.sample_stride:
            return False
        if not self._ensure_context() or not self._free:
            return False
        query_id = self._free.popleft()
        try:
            self._api['begin'](self.GL_TIME_ELAPSED, query_id)
            self._active = query_id
            self._active_token = int(token)
            return True
        except Exception as exc:
            self._free.appendleft(query_id)
            self.abandon(str(exc) or 'Timer query begin failed')
            return False

    def end(self):
        query_id = self._active
        token = self._active_token
        self._active = None
        self._active_token = 0
        if query_id is None or not self.supported:
            return
        try:
            self._api['end'](self.GL_TIME_ELAPSED)
            self._pending.append((query_id, token))
        except Exception as exc:
            self.abandon(str(exc) or 'Timer query end failed')
