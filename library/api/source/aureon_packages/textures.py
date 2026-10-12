"""TEX01 experimental bounded PNG/JPEG resources; no GL during preparation."""
from .limits import LIMITS

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import re
import time
import logging
from .expressions import PackageError
from .schema import obj

@dataclass(frozen=True)
class TextureResource:
    name: str
    path: str
    color_space: str
    wrap: str
    filter: str
    mipmaps: bool
    width: int
    height: int
    pixels: bytes
    decode_ms: float

    @property
    def estimated_bytes(self):
        w,h=self.width,self.height
        total=w*h*4
        if self.mipmaps:
            while w>1 or h>1:
                w,h=max(1,w//2),max(1,h//2)
                total+=w*h*4
        return total

def _decode(raw, path):
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtGui import QImageReader, QImage
    started=time.perf_counter()
    buffer=QBuffer()
    buffer.setData(QByteArray(raw)); buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader=QImageReader(buffer)
    reader.setDecideFormatFromContent(True)
    fmt=bytes(reader.format()).decode('ascii','ignore').lower()
    expected='png' if path.endswith('.png') else 'jpeg'
    if fmt!=expected: raise PackageError('Texture encoding does not match extension: '+path)
    size=reader.size()
    if not (1<=size.width()<=LIMITS["image_axis"] and 1<=size.height()<=LIMITS["image_axis"]):
        raise PackageError('TEX01 texture size must be 1..204800 on each axis: '+path)
    if size.width()*size.height()*4 > LIMITS['texture_bytes']:
        raise PackageError('Decoded texture exceeds the 3200 MiB budget: '+path)
    reader.setAutoTransform(False)
    image=reader.read()
    if image.isNull(): raise PackageError('Cannot decode texture: '+path)
    if image.size()!=size: raise PackageError('Texture dimensions changed during decoding')
    # Package UV origin is bottom-left; stored image row zero is top-left.
    image=image.convertToFormat(QImage.Format.Format_RGBA8888).mirrored(False,True)
    return size.width(),size.height(),bytes(image.constBits()),(time.perf_counter()-started)*1000.0

def textures(data,resources):
    if not isinstance(data,dict) or len(data)>LIMITS["textures"]:
        raise PackageError('TEX01 allows at most 400 textures')
    result=[]; used=set(); budget=0
    # Local worker avoids GUI image decoding; caller still waits for validation.
    with ThreadPoolExecutor(max_workers=1,thread_name_prefix='AursTextureDecode') as worker:
        for name,spec in data.items():
            if not re.fullmatch(r'u_tex_[a-zA-Z][a-zA-Z0-9_]{0,39}',name):
                raise PackageError('Texture sampler must use u_tex_ prefix')
            obj(spec,('source','color_space','wrap','filter','mipmaps'),('source','color_space'))
            path=spec['source']
            if not isinstance(path,str) or not re.fullmatch(r'textures/[A-Za-z0-9_-]+\.(png|jpg|jpeg)',path) or path not in resources:
                raise PackageError('Missing or invalid texture resource')
            if path in used: raise PackageError('Declare a texture file only once')
            used.add(path)
            color=spec['color_space']; wrap=spec.get('wrap','repeat'); filt=spec.get('filter','linear'); mip=spec.get('mipmaps',True)
            if color not in ('srgb','linear') or wrap not in ('repeat','clamp') or filt not in ('linear','nearest') or type(mip) is not bool:
                raise PackageError('Invalid texture settings')
            # Check the aggregate mip budget BEFORE allocating decoded pixels.
            from PySide6.QtCore import QBuffer, QByteArray, QIODevice
            from PySide6.QtGui import QImageReader
            buffer=QBuffer(); buffer.setData(QByteArray(resources[path])); buffer.open(QIODevice.ReadOnly)
            reader=QImageReader(buffer); size=reader.size()
            w,h=size.width(),size.height()
            if not (1<=w<=LIMITS['image_axis'] and 1<=h<=LIMITS['image_axis']):
                raise PackageError('TEX01 texture size must be 1..204800 on each axis: '+path)
            estimate=TextureResource(name,path,color,wrap,filt,mip,w,h,b'',0.).estimated_bytes
            if budget+estimate>LIMITS['texture_bytes']:
                raise PackageError('TEX01 decoded texture budget including mipmaps exceeds 3200 MiB')
            # Explicitly raise Qt's reader ceiling as well, without disabling it.
            QImageReader.setAllocationLimit(max(QImageReader.allocationLimit(), LIMITS['texture_bytes']//(1024*1024)))
            w,h,pixels,ms=worker.submit(_decode,resources[path],path).result()
            texture=TextureResource(name,path,color,wrap,filt,mip,w,h,pixels,ms)
            budget+=texture.estimated_bytes
            if budget>LIMITS["texture_bytes"]: raise PackageError('TEX01 decoded texture budget including mipmaps exceeds 3200 MiB')
            result.append(texture)
            logging.getLogger('aureon').info('[AURS TEX] decode name=%s size=%dx%d ms=%.3f estimated_bytes=%d',name,w,h,ms,texture.estimated_bytes)
    if {p for p in resources if p.startswith('textures/')}!=used:
        raise PackageError('Unreferenced texture resources')
    return tuple(result)
