"""Read GL identity only while initializeGL owns a current context."""
import sys


def context_device_info(context):
    def read(token):
        try:
            value = context.functions().glGetString(token)
            if isinstance(value, bytes):
                return value.decode('utf-8', 'replace')
            if isinstance(value, str):
                return value
        except Exception:
            pass
        if sys.platform == 'win32':
            try:
                import ctypes
                gl = ctypes.WinDLL('opengl32.dll')
                func = gl.glGetString
                func.argtypes = [ctypes.c_uint]
                func.restype = ctypes.c_char_p
                value = func(token)
                return value.decode('utf-8', 'replace') if value else ''
            except Exception:
                pass
        return ''
    info={'renderer': read(0x1F01), 'vendor': read(0x1F00), 'version': read(0x1F02), 'glsl_version':read(0x8B8C)}
    try:
        fmt=context.format()
        info['context']={'version':[fmt.majorVersion(),fmt.minorVersion()],
                         'profile':fmt.profile().name,'gles':context.isOpenGLES()}
    except (RuntimeError,AttributeError):pass
    if sys.platform == 'win32':
        try:
            if context.hasExtension(b'GL_NVX_gpu_memory_info'):
                import ctypes
                func = ctypes.WinDLL('opengl32.dll').glGetIntegerv
                func.argtypes = (ctypes.c_uint, ctypes.POINTER(ctypes.c_int))
                memory = ctypes.c_int()
                func(0x9047, ctypes.byref(memory))  # DEDICATED_VIDMEM_NVX, KB
                if memory.value > 0:
                    info['dedicated_memory_mb'] = memory.value / 1024
        except (RuntimeError, AttributeError, OSError, TypeError):
            pass
    return info
