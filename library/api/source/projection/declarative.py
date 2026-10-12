"""Canvas renderer for validated AURP graphs on Aureon's native tray host."""
from aureon_packages.limits import LIMITS

import math
import time
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF, QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPolygonF, QRadialGradient, QLinearGradient, QImageReader, QImage
from .host import ProjectionHost
from .hologram import MusicalHologram
from aureon_packages.expressions import AUDIO_REACTIVE, PackageError


def decode_images(assets):
    images, pixels = {}, 0
    for name, raw in assets.items():
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'): raise PackageError('Only PNG image resources are supported')
        buffer = QBuffer()
        buffer.setData(QByteArray(raw))
        buffer.open(QIODevice.ReadOnly)
        reader = QImageReader(buffer, b'png')
        size = reader.size()
        if not size.isValid() or size.width() > LIMITS["image_axis"] or size.height() > LIMITS["image_axis"]:
            raise PackageError('Invalid or oversized image: '+name)
        pixels += size.width()*size.height()
        if pixels > LIMITS["projection_image_pixels"]: raise PackageError('Total decoded image limit exceeded')
        QImageReader.setAllocationLimit(max(QImageReader.allocationLimit(), LIMITS['projection_image_pixels']*4//(1024*1024)))
        image = reader.read()
        if image.isNull(): raise PackageError('Cannot decode image: '+name)
        images[name] = image
    return images


class DeclarativeProjectionWindow(ProjectionHost):
    failed = Signal(str)

    def __init__(self, frame_provider, definition, images):
        self.definition = definition
        self.images = images
        self._broken = False
        self._last_tick = None
        self._signals = {}
        self._holograms = {}
        super().__init__(frame_provider)
        self.setFixedSize(definition.width, definition.height)
        self.setWindowTitle('Aureon Projection')
        self._reset_signals()

    def _reset_signals(self):
        for hologram in self._holograms.values(): hologram.reset()
        self._signals = {name:(b if kind == 'integrator' else 0.0)
                         for name, kind, expr, a, b in self.definition.signals}
        self._last_tick = None

    def showEvent(self, event):
        self._reset_signals()
        super().showEvent(event)
        if self._broken: self._timer.stop()

    def _context(self):
        try: frame = self._frame_provider()
        except Exception: frame = None
        self._core.ingest(frame)
        self._core.tick()
        snapshot = self._core.snapshot()
        now = time.perf_counter()
        dt = min(.1, max(0., now-self._last_tick)) if self._last_tick is not None else 0.
        self._last_tick = now
        audio = {}
        for name in AUDIO_REACTIVE:
            value = float(getattr(snapshot, name, 0.))
            audio[name] = value if math.isfinite(value) else 0.
        zones = tuple(getattr(snapshot, 'zones', ()) or ())
        for index in range(8):
            value = float(zones[index]) if index < len(zones) else 0.0
            audio[f'zone{index}'] = value if math.isfinite(value) else 0.0
        context = {'time':now-self._start, 'dt':dt, 'pi':math.pi, 'audio':audio, 'signal':self._signals}
        for name, kind, expr, a, b in self.definition.signals:
            value = expr.value(context)
            if kind == 'integrator':
                value = (self._signals[name]+value*dt) % a
            elif kind == 'envelope':
                current = self._signals[name]
                tau = a if value > current else b
                value = current+(value-current)*(1-math.exp(-dt/tau))
            self._signals[name] = value
        return context

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), QColor(0,0,0,0))
            if self._broken: return
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setClipRect(self.rect())
            context = self._context()
            if self.definition.supersample > 1 or self.definition.bloom > 0:
                painter.drawImage(QRectF(self.rect()), self.render_image(context, self.devicePixelRatioF()))
            else:
                self._paint_nodes(painter, self.definition.nodes, context)
        except Exception as exc:
            self._broken = True
            self._timer.stop()
            reason = str(exc)[:240]
            QTimer.singleShot(0, lambda message=reason: self.failed.emit(message))
        finally:
            painter.end()

    def render_image(self, context, dpr=1.):
        """Render the same graph for the window and lossless visual QA."""
        # The high-quality floor already supplies enough pixels at 150/200%.
        # Multiplying by DPR again quadruples raster work without visible gain.
        scale = min(float(LIMITS["raster_scale"]), max(1., dpr, self.definition.supersample))
        w,h = round(self.width()*scale),round(self.height()*scale)
        if w < 1 or h < 1 or w*h > LIMITS['projection_image_pixels']:
            raise PackageError('Projection raster exceeds the expanded pixel budget')
        scene = QImage(w,h,QImage.Format_ARGB32_Premultiplied)
        if scene.isNull(): raise PackageError('Insufficient memory for the projection raster')
        scene.fill(Qt.transparent)
        p = QPainter(scene)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.scale(scale,scale)
            self._paint_nodes(p,self.definition.nodes,context)
        finally:
            p.end()
        if self.definition.bloom <= 0: return scene
        output = QImage(w,h,QImage.Format_ARGB32_Premultiplied)
        if output.isNull(): raise PackageError('Insufficient memory for the projection bloom raster')
        output.fill(Qt.transparent)
        p = QPainter(output)
        try:
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            # Soft light spreads; no black/opaque backing rectangle. Each pass
            # downsamples the real scene, so ribbons and particles emit light.
            for divisor,opacity in ((8,.75),(20,.46)):
                blur = scene.scaled(max(1,w//divisor),max(1,h//divisor),Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
                p.setOpacity(self.definition.bloom*opacity)
                p.drawImage(QRectF(0,0,w,h),blur)
            p.setOpacity(1.)
            p.drawImage(0,0,scene)
        finally:
            p.end()
        return output

    def _paint_nodes(self, p, nodes, context):
        def value(expr): return expr.value(context)
        def bounded(expr, lo=-409600., hi=409600.): return max(lo, min(hi, value(expr)))
        def point(pair): return QPointF(*(bounded(e) for e in pair))
        def brush(spec):
            if spec is None: return QBrush(Qt.NoBrush)
            if isinstance(spec, str): return QBrush(QColor(spec))
            if spec['type'] == 'linear':
                gradient = QLinearGradient(point(spec['start']), point(spec['end']))
            else:
                gradient = QRadialGradient(point(spec['center']), bounded(spec['radius'], .01, 102400))
            for position, color in spec['stops']: gradient.setColorAt(position,QColor(color))
            return QBrush(gradient)
        for node in nodes:
            p.save()
            try:
                p.setCompositionMode(QPainter.CompositionMode_Plus if node['blend']=='add' else QPainter.CompositionMode_SourceOver)
                p.setOpacity(p.opacity()*bounded(node['opacity'],0,1))
                p.translate(point(node['translate']))
                if 'center' in node: p.translate(point(node['center']))
                p.rotate(value(node['rotation']) % 360)
                p.scale(*(bounded(e,-4,4) for e in node['scale']))
                kind = node['type']
                if kind == 'group':
                    self._paint_nodes(p,node['nodes'],context)
                    continue
                if kind == 'hologram':
                    renderer = self._holograms.setdefault(id(node), None)
                    if renderer is None:
                        renderer = self._holograms[id(node)] = MusicalHologram()
                    renderer.paint(p,node,context)
                    continue
                if kind == 'image':
                    x,y,w,h = (bounded(e) for e in node['rect'])
                    if w>0 and h>0: p.drawImage(QRectF(x,y,min(w,102400),min(h,102400)),self.images[node['source']])
                    continue
                pen = QPen(QColor(node['color']))
                width = bounded(node['width'],0,32)
                pen.setWidthF(max(.01,width)); pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin)
                p.setPen(pen if width>0 else Qt.NoPen)
                p.setBrush(brush(node['fill']))
                if kind == 'line': p.drawLine(point(node['start']),point(node['end']))
                elif kind in ('polygon','polyline'):
                    polygon=QPolygonF([point(pair) for pair in node['points']])
                    if kind=='polygon': p.drawPolygon(polygon)
                    else: p.drawPolyline(polygon)
                elif kind == 'radial_glow':
                    r=bounded(node['radius'],.01,102400)
                    gradient=QRadialGradient(QPointF(0,0),r)
                    color=QColor(node['color'])
                    color.setAlphaF(color.alphaF()*bounded(node['strength'],0,1))
                    gradient.setColorAt(0,color)
                    outer=QColor(color); outer.setAlpha(0); gradient.setColorAt(1,outer)
                    p.setPen(Qt.NoPen); p.setBrush(QBrush(gradient))
                    p.drawEllipse(QRectF(-r,-r,2*r,2*r))
                else:
                    rx,ry=bounded(node['rx'],.01,102400),bounded(node['ry'],.01,102400)
                    rect=QRectF(-rx,-ry,rx*2,ry*2)
                    if kind == 'arc':
                        p.drawArc(rect,round((value(node['start_angle'])%360)*16),round(bounded(node['span_angle'],-360,360)*16))
                    else: p.drawEllipse(rect)
            finally:
                p.restore()
