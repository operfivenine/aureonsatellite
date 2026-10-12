"""Context-owned TEX01 textures. No persistent GL objects in package definitions."""
import ctypes
import logging
import time
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGL import QOpenGLTexture as T

def _upload_rgba(context, texture, spec):
    """Avoid PySide's ambiguous void* setData overload; retain Qt storage owner."""
    abi = getattr(ctypes, 'WINFUNCTYPE', ctypes.CFUNCTYPE)
    def proc(name, result, *arguments):
        address = int(context.getProcAddress(name.encode('ascii')) or 0)
        if address in (0, 1, 2, 3, -1, ctypes.c_void_p(-1).value):
            raise RuntimeError('Missing OpenGL texture upload function: '+name)
        return abi(result, *arguments)(address)
    uint, integer, pointer = ctypes.c_uint, ctypes.c_int, ctypes.c_void_p
    get = proc('glGetIntegerv', None, uint, ctypes.POINTER(integer))
    pixel_store = proc('glPixelStorei', None, uint, integer)
    bind_buffer = proc('glBindBuffer', None, uint, uint)
    bind_texture = proc('glBindTexture', None, uint, uint)
    upload = proc('glTexSubImage2D', None, uint, integer, integer, integer,
                  integer, integer, uint, uint, pointer)
    def read(enum):
        value=integer(); get(enum,ctypes.byref(value)); return value.value
    # Explicit client memory: an inherited pixel-unpack buffer would reinterpret
    # the pointer as an offset. Restore all state even if a Python call fails.
    previous_buffer=read(0x88EF)  # GL_PIXEL_UNPACK_BUFFER_BINDING
    previous_texture=read(0x8069) # GL_TEXTURE_BINDING_2D, current texture unit
    state={enum:read(enum) for enum in (0x0CF5,0x0CF2,0x0CF3,0x0CF4,0x0CF0)}
    # Borrow immutable bytes during the synchronous upload; copying a 4K/8K
    # texture into create_string_buffer needlessly doubles CPU pixel storage.
    if len(spec.pixels) != spec.width*spec.height*4:
        raise RuntimeError('Invalid RGBA texture byte count: '+spec.name)
    pixels=ctypes.c_char_p(spec.pixels)
    try:
        bind_buffer(0x88EC,0)
        pixel_store(0x0CF5,1)
        for enum in (0x0CF2,0x0CF3,0x0CF4,0x0CF0): pixel_store(enum,0)
        bind_texture(0x0DE1,int(texture.textureId()))
        upload(0x0DE1,0,0,0,spec.width,spec.height,0x1908,0x1401,
               ctypes.cast(pixels,pointer))
    finally:
        bind_texture(0x0DE1,previous_texture)
        for enum,value in state.items(): pixel_store(enum,value)
        bind_buffer(0x88EC,previous_buffer)


def _assign_sampler(context, program, name, unit):
    """Sampler uniforms require signed integer upload, never float overloads."""
    abi = getattr(ctypes, 'WINFUNCTYPE', ctypes.CFUNCTYPE)
    def proc(name, result, *args):
        address = int(context.getProcAddress(name.encode('ascii')) or 0)
        if address in (0, 1, 2, 3, -1, ctypes.c_void_p(-1).value):
            raise RuntimeError('Missing OpenGL sampler function: '+name)
        return abi(result, *args)(address)
    location = program.uniformLocation(name)
    if location < 0:
        logging.getLogger('aureon').info('[AURS TEX] sampler %s optimized out',name)
        return
    upload = proc('glUniform1i', None, ctypes.c_int, ctypes.c_int)
    read = proc('glGetUniformiv', None, ctypes.c_uint, ctypes.c_int,
                ctypes.POINTER(ctypes.c_int))
    upload(location, unit)
    actual = ctypes.c_int(-1)
    read(int(program.programId()), location, ctypes.byref(actual))
    if actual.value != unit:
        raise RuntimeError(f'Sampler binding failed: {name}: expected {unit}, got {actual.value}')
    logging.getLogger('aureon').info('[AURS TEX] sampler %s location=%d unit=%d',name,location,actual.value)

class SceneTextures:
    def __init__(self):
        self.items=[]
        self.context=None
        self.stats={'count':0,'estimated_bytes':0,'decode_ms':0.0,'upload_ms':0.0,'sizes':''}

    def create(self, specs, program):
        self.destroy()
        if not specs: return
        self.context=QOpenGLContext.currentContext()
        if self.context is None: raise RuntimeError('Texture upload requires current GL context')
        # Expanded package limits do not imply expanded GPU hardware limits.
        abi=getattr(ctypes,'WINFUNCTYPE',ctypes.CFUNCTYPE)
        address=int(self.context.getProcAddress(b'glGetIntegerv') or 0)
        if address in (0,1,2,3,-1,ctypes.c_void_p(-1).value):
            raise RuntimeError('Cannot query GPU texture limits')
        query=abi(None,ctypes.c_uint,ctypes.POINTER(ctypes.c_int))(address)
        max_size,max_units=ctypes.c_int(),ctypes.c_int()
        query(0x0D33,ctypes.byref(max_size))  # GL_MAX_TEXTURE_SIZE
        query(0x8872,ctypes.byref(max_units)) # GL_MAX_TEXTURE_IMAGE_UNITS
        if len(specs)>max_units.value:
            raise RuntimeError(f'GPU supports {max_units.value} fragment textures; package requests {len(specs)}')
        for spec in specs:
            if spec.width>max_size.value or spec.height>max_size.value:
                raise RuntimeError(f'GPU texture size limit is {max_size.value}; requested {spec.width}x{spec.height}')
        started=time.perf_counter()
        try:
            if not program.bind(): raise RuntimeError('Cannot bind texture program')
            for unit,spec in enumerate(specs):
                texture=T(T.Target.Target2D)
                self.items.append((unit,texture))
                if not texture.create(): raise RuntimeError('Cannot create texture: '+spec.name)
                texture.setSize(spec.width,spec.height)
                texture.setFormat(T.TextureFormat.SRGB8_Alpha8 if spec.color_space=='srgb' else T.TextureFormat.RGBA8_UNorm)
                levels=max(spec.width,spec.height).bit_length() if spec.mipmaps else 1
                texture.setMipLevels(levels)
                texture.setAutoMipMapGenerationEnabled(False)
                texture.allocateStorage(T.PixelFormat.RGBA,T.PixelType.UInt8)
                if not texture.isStorageAllocated(): raise RuntimeError('Texture allocation failed: '+spec.name)
                _upload_rgba(self.context,texture,spec)
                if spec.mipmaps: texture.generateMipMaps()
                nearest=spec.filter=='nearest'
                texture.setMagnificationFilter(T.Filter.Nearest if nearest else T.Filter.Linear)
                texture.setMinificationFilter((T.Filter.NearestMipMapNearest if nearest else T.Filter.LinearMipMapLinear) if spec.mipmaps else (T.Filter.Nearest if nearest else T.Filter.Linear))
                texture.setWrapMode(T.WrapMode.Repeat if spec.wrap=='repeat' else T.WrapMode.ClampToEdge)
                _assign_sampler(self.context,program,spec.name,unit)
            self.stats={'count':len(specs),'estimated_bytes':sum(s.estimated_bytes for s in specs),
                        'decode_ms':sum(s.decode_ms for s in specs),'upload_ms':(time.perf_counter()-started)*1000.0,
                        'sizes':', '.join(f'{s.width}x{s.height}' for s in specs)}
            logging.getLogger('aureon').info('[AURS TEX] upload %s',self.stats)
        except Exception:
            self.destroy()
            raise
        finally:
            program.release()

    def bind(self):
        if self.items and QOpenGLContext.currentContext()!=self.context:
            raise RuntimeError('Texture context mismatch')
        for unit,texture in self.items: texture.bind(unit)

    def release(self):
        for unit,texture in self.items: texture.release(unit)
        if self.items: self.context.functions().glActiveTexture(0x84C0)

    def destroy(self):
        count=len(self.items)
        current=QOpenGLContext.currentContext()
        if current is not None and current==self.context:
            for _,texture in self.items: texture.destroy()
        # With a lost context Qt handles texture teardown through its shared-resource guard.
        self.items.clear()
        self.context=None
        self.stats={'count':0,'estimated_bytes':0,'decode_ms':0.0,'upload_ms':0.0,'sizes':''}
        if count: logging.getLogger('aureon').info('[AURS TEX] cleanup count=%d',count)
