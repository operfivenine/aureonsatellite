from __future__ import annotations

import math
import sys
import time
from typing import Callable

try:
    import ctypes
except Exception:
    ctypes = None

from aureon_content import get_registry
from PySide6.QtCore import QObject, QTimer, Qt, Signal, QRect, QRectF, QPointF
from PySide6.QtGui import (
    QColor,
    QBrush,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QWidget

from audio.reactive import ReactiveAudioCore


from .host import ProjectionHost


class HolographicOrbitWindow(ProjectionHost):
    """Built-in Orbital Atlas renderer on the shared native projection host."""

    @staticmethod
    def _pen(color: QColor, width: float) -> QPen:
        pen = QPen(color)
        pen.setWidthF(width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen

    def _draw_glow_line(self, p: QPainter, a: QPointF, b: QPointF, color: QColor, strength: float, width: float):
        for mul, alpha in ((4.2, 16), (2.5, 28), (1.45, 54)):
            c = QColor(color)
            c.setAlpha(int(alpha * strength))
            p.setPen(self._pen(c, width * mul))
            p.drawLine(a, b)
        c = QColor(color)
        c.setAlpha(int(190 * strength))
        p.setPen(self._pen(c, width))
        p.drawLine(a, b)

    def _draw_projector_shaft(self, p: QPainter, emitter: QPointF, top_y: float, half_top: float, alpha_scale: float):
        # Layered fan beam that feels more like light from a tiny projector than a simple column.
        for idx, spread in enumerate((1.00, 0.76, 0.54)):
            half = half_top * spread
            poly = QPolygonF([
                QPointF(emitter.x() - (3.2 if idx == 0 else 2.0), emitter.y()),
                QPointF(emitter.x() - half, top_y),
                QPointF(emitter.x() + half, top_y),
                QPointF(emitter.x() + (3.2 if idx == 0 else 2.0), emitter.y()),
            ])
            grad = QLinearGradient(QPointF(emitter.x(), emitter.y()), QPointF(emitter.x(), top_y))
            base = int((32 - idx * 8) * alpha_scale)
            grad.setColorAt(0.0, QColor(120, 255, 245, base + 26))
            grad.setColorAt(0.20, QColor(60, 248, 232, base + 8))
            grad.setColorAt(0.65, QColor(24, 230, 220, max(0, base - 10)))
            grad.setColorAt(1.0, QColor(18, 215, 210, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.setOpacity(0.18 if idx == 0 else 0.13 if idx == 1 else 0.10)
            p.drawPolygon(poly)
        p.setOpacity(1.0)

    def _draw_projector_rays(self, p: QPainter, emitter: QPointF, apex_y: float, bass: float, flux: float):
        # Soft volumetric shafts around the main cone, inspired by projector spill light.
        color = QColor(88, 255, 241)
        shafts = (-44.0, -26.0, -12.0, 12.0, 26.0, 44.0)
        for i, dx in enumerate(shafts):
            end = QPointF(emitter.x() + dx, apex_y - (6.0 if abs(dx) > 30 else 0.0))
            strength = 0.16 + 0.05 * bass + (0.05 if i % 2 == 0 else 0.0) + 0.07 * flux
            self._draw_glow_line(p, QPointF(emitter.x(), emitter.y()-0.5), end, color, strength, 0.7)

    def _draw_wire_sphere(self, p: QPainter, center: QPointF, radius: float, t: float, mid: float, energy: float):
        cyan = QColor(28, 244, 224)
        glow = QColor(30, 210, 230)
        # Outer bloom/rim
        for w, a in ((7.0, 14), (4.0, 30), (1.55, 175)):
            c = QColor(cyan); c.setAlpha(int(a * (0.72 + energy * 0.45)))
            p.setPen(self._pen(c, w))
            p.drawEllipse(QRectF(center.x()-radius, center.y()-radius, radius*2, radius*2))
        # Latitude rings
        for i in (-2, -1, 0, 1, 2):
            y = center.y() + radius * i * 0.31
            rr = radius * math.sqrt(max(0.04, 1.0 - (i*0.31)**2))
            c = QColor(glow); c.setAlpha(105 if i else 145)
            p.setPen(self._pen(c, 0.9))
            p.drawEllipse(QRectF(center.x()-rr, y-rr*0.19, rr*2, rr*0.38))
        # Rotating longitudes
        phase = t * (0.55 + mid * 0.65)
        for i in range(6):
            a = phase + i * math.pi / 6.0
            sx = 0.12 + 0.88 * abs(math.cos(a))
            c = QColor(cyan); c.setAlpha(90 + int(35 * abs(math.sin(a))))
            p.setPen(self._pen(c, 0.9))
            p.drawEllipse(QRectF(center.x()-radius*sx, center.y()-radius, radius*2*sx, radius*2))
        # Scanline shimmer only inside the sphere
        p.save()
        clip = QPainterPath(); clip.addEllipse(QRectF(center.x()-radius, center.y()-radius, radius*2, radius*2))
        p.setClipPath(clip)
        for j in range(0, int(radius*2), 5):
            y = center.y()-radius+j+((t*22.0) % 5.0)
            c = QColor(40, 250, 226, 14 + int(16*energy))
            p.setPen(self._pen(c, 0.65))
            p.drawLine(QPointF(center.x()-radius, y), QPointF(center.x()+radius, y))
        p.restore()

    def paintEvent(self, event):
        try:
            frame = self._frame_provider() if callable(self._frame_provider) else None
        except Exception:
            frame = None
        self._core.ingest(frame)
        self._core.tick()
        s = self._core.snapshot()
        t = time.perf_counter() - self._start

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode_Plus)

        w = float(self.width()); h = float(self.height())
        emitter = QPointF(w * 0.5, h - 2.0)
        sphere_c = QPointF(w * 0.5, 61.0)
        sphere_r = 30.0 + 2.2 * s.low
        cyan = QColor(20, 246, 224)

        # Stronger projector base: compact bright source directly on top of the tray icon.
        rg = QRadialGradient(emitter, 38.0 + 10.0 * s.low)
        rg.setColorAt(0.0, QColor(220, 255, 250, 235))
        rg.setColorAt(0.10, QColor(70, 255, 238, 185))
        rg.setColorAt(0.26, QColor(28, 244, 224, 92))
        rg.setColorAt(0.52, QColor(10, 214, 205, 26))
        rg.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen); painter.setBrush(QBrush(rg))
        painter.drawEllipse(QRectF(emitter.x()-48, emitter.y()-34, 96, 68))

        # Lens/aperture shimmer at the source to sell the mini-projector idea.
        painter.setBrush(QColor(185, 255, 248, 220)); painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(emitter.x()-3.0, emitter.y()-3.0, 6.0, 6.0))
        painter.setBrush(QColor(20, 246, 224, 130))
        painter.drawEllipse(QRectF(emitter.x()-8.5, emitter.y()-4.2, 17.0, 8.4))

        top_y = sphere_c.y() + sphere_r * 0.66
        self._draw_projector_shaft(painter, emitter, top_y, 42.0 + 6.0*s.energy, 1.0 + 0.35*s.low)
        self._draw_projector_rays(painter, emitter, sphere_c.y() - sphere_r * 0.24, s.low, max(s.flux, s.beat))

        # Beam core visibly connects hologram to the icon.
        beam_top = QPointF(sphere_c.x(), sphere_c.y()+sphere_r*0.86)
        self._draw_glow_line(painter, emitter, beam_top, cyan, 0.92 + 0.32*s.energy, 1.15)

        # A small activation flash before the hologram body, reinforcing the projected feel.
        pulse = min(1.0, max(s.beat, s.flux*0.9))
        if pulse > 0.01:
            rr = 8.5 + 16.0 * (1.0-pulse)
            c = QColor(120,255,244,int(140*pulse))
            painter.setPen(self._pen(c, 1.15))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(emitter.x()-rr, emitter.y()-rr*0.26, rr*2, rr*0.52))

        # Hologram body.
        self._draw_wire_sphere(painter, sphere_c, sphere_r, t, s.mid, s.energy)

        # Orbit rings, a touch brighter than v2 so they read inside the new shaft.
        painter.save(); painter.translate(sphere_c); painter.rotate(-11.0)
        for scale, alpha in ((1.45, 126), (1.72, 62)):
            c = QColor(32, 245, 225, int(alpha*(0.74+0.30*s.mid)))
            painter.setPen(self._pen(c, 1.0))
            painter.drawEllipse(QRectF(-sphere_r*scale, -sphere_r*0.27, sphere_r*2*scale, sphere_r*0.54))
        painter.restore()

        # Sparse particles near the shaft and upper hologram.
        for i in range(28):
            seed = i * 12.9898
            fy = (math.sin(seed*1.7 + t*(0.10+0.16*s.high)) * 0.5 + 0.5)
            y = 12.0 + fy * 138.0
            cone_t = max(0.0, min(1.0, (emitter.y()-y) / max(1.0, emitter.y()-top_y)))
            spread = 14.0 + 40.0 * cone_t
            x = emitter.x() + math.sin(seed*2.31 + t*0.22) * spread
            r = 0.65 + 0.75*((i % 3)/2.0)
            a = int((24 + 84*s.high) * (0.42 + 0.58*((i*7)%11)/10.0))
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(90,255,239,a))
            painter.drawEllipse(QRectF(x-r,y-r,r*2,r*2))

        painter.end()

class ReactorCoreWindow(HolographicOrbitWindow):
    """Compact music-reactive reactor projection using the proven alpha tray surface."""

    def _draw_ring(self, p: QPainter, center: QPointF, rx: float, ry: float, angle: float,
                   color: QColor, strength: float, width: float = 1.0):
        p.save()
        p.translate(center)
        p.rotate(angle)
        rect = QRectF(-rx, -ry, rx * 2.0, ry * 2.0)
        for mul, alpha in ((4.0, 14), (2.3, 30), (1.0, 150)):
            c = QColor(color)
            c.setAlpha(max(0, min(255, int(alpha * strength))))
            p.setPen(self._pen(c, width * mul))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(rect)
        p.restore()

    def paintEvent(self, event):
        try:
            frame = self._frame_provider() if callable(self._frame_provider) else None
        except Exception:
            frame = None
        self._core.ingest(frame)
        self._core.tick()
        s = self._core.snapshot()
        t = time.perf_counter() - self._start

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode_Plus)

        w = float(self.width()); h = float(self.height())
        emitter = QPointF(w * 0.5, h - 2.0)
        core_c = QPointF(w * 0.5, 65.0)
        cyan = QColor(42, 246, 230)
        pale = QColor(185, 255, 249)
        blue = QColor(54, 195, 255)

        # Beamless projection language — Projector-base language: the tray edge itself becomes the source.
        # No emitter dot and no hard beam. A wide, low-alpha holographic field
        # rises from the bottom edge and dissolves before it reaches the core.
        field_energy = 0.34 + 0.48 * max(s.low, s.energy)

        # Broad glow footprint sitting on the tray edge.
        base_glow = QRadialGradient(QPointF(emitter.x(), h - 1.0), 54.0 + 8.0 * s.low)
        base_glow.setColorAt(0.0, QColor(132, 255, 246, int(82 * field_energy)))
        base_glow.setColorAt(0.24, QColor(48, 247, 232, int(54 * field_energy)))
        base_glow.setColorAt(0.58, QColor(18, 210, 220, int(20 * field_energy)))
        base_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen); painter.setBrush(QBrush(base_glow))
        painter.drawEllipse(QRectF(emitter.x()-58, h-15.0, 116, 28))

        # Diffuse projector plume: layered translucent wedges instead of a visible ray.
        plume_top = 102.0
        plume_bottom = h - 4.0
        for idx, (base_half, top_half, alpha) in enumerate(((38.0, 15.0, 22), (29.0, 11.0, 30), (21.0, 8.0, 26))):
            wobble = 1.0 + 0.025 * math.sin(t * (0.55 + idx * 0.09) + idx)
            path = QPainterPath()
            path.moveTo(emitter.x() - base_half * wobble, plume_bottom)
            path.lineTo(emitter.x() - top_half, plume_top)
            path.lineTo(emitter.x() + top_half, plume_top)
            path.lineTo(emitter.x() + base_half * wobble, plume_bottom)
            path.closeSubpath()
            grad = QLinearGradient(0.0, plume_bottom, 0.0, plume_top)
            grad.setColorAt(0.0, QColor(42, 244, 230, int(alpha * field_energy)))
            grad.setColorAt(0.38, QColor(38, 222, 230, int(alpha * 0.58 * field_energy)))
            grad.setColorAt(0.78, QColor(32, 202, 224, int(alpha * 0.17 * field_energy)))
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen); painter.setBrush(QBrush(grad))
            painter.drawPath(path)

        # Thin projection ripples at the tray boundary. They imply a projector surface
        # without introducing a separate device or point source.
        ripple_energy = 0.32 + 0.46 * max(s.low, s.energy)
        for idx, (rx, ry, alpha) in enumerate(((24.0, 3.8, 74), (37.0, 6.4, 34))):
            pulse = 1.0 + 0.045 * math.sin(t * (1.1 + idx * 0.18))
            c = QColor(cyan)
            c.setAlpha(int(alpha * ripple_energy))
            painter.setPen(self._pen(c, 0.78 if idx else 0.92))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(
                emitter.x() - rx * pulse, h - 8.0 - ry * pulse,
                rx * 2.0 * pulse, ry * 2.0 * pulse
            ))

        # A handful of faint motes rise from the tray field and vanish before the core.
        for i in range(9):
            seed = i * 4.913
            phase = (t * (0.10 + 0.035 * (i % 4)) + seed) % 1.0
            y = plume_bottom - phase * (plume_bottom - 108.0)
            span = 30.0 * (1.0 - phase) + 8.0
            x = emitter.x() + math.sin(seed * 1.37 + t * 0.21) * span
            r = 0.45 + 0.45 * ((i % 3) / 2.0)
            a = int((12 + 42 * s.high) * (1.0 - phase) * field_energy)
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(108, 255, 243, a))
            painter.drawEllipse(QRectF(x-r, y-r, r*2, r*2))

        # Reactor containment rings: three different planes, slow differential rotation.
        self._draw_ring(painter, core_c, 44.0+2.4*s.mid, 12.0+1.8*s.high, -18.0 + t*7.0,
                        cyan, 0.72+0.38*s.mid, 1.05)
        self._draw_ring(painter, core_c, 35.0+3.5*s.low, 18.0+1.6*s.mid, 57.0 - t*9.0,
                        blue, 0.52+0.46*s.energy, 0.95)
        self._draw_ring(painter, core_c, 29.0+2.0*s.high, 9.0+2.4*s.high, 12.0 + t*13.0,
                        pale, 0.45+0.56*s.high, 0.80)

        # Eight spectrum nodes ride the outer containment ring. Zones give it real musical structure.
        zones = tuple(getattr(s, 'zones', ()) or ())
        for i in range(8):
            z = zones[i] if i < len(zones) else 0.0
            a = t*0.22 + i*(math.tau/8.0)
            rx = 45.5 + z*4.8
            ry = 16.5 + z*2.0
            x = core_c.x() + math.cos(a)*rx
            y = core_c.y() + math.sin(a)*ry
            rr = 1.0 + 1.7*z
            glow = QRadialGradient(QPointF(x,y), 7.0+5.0*z)
            glow.setColorAt(0.0, QColor(215,255,252,205))
            glow.setColorAt(0.25, QColor(62,248,232,125+int(80*z)))
            glow.setColorAt(1.0, QColor(0,0,0,0))
            painter.setPen(Qt.NoPen); painter.setBrush(QBrush(glow))
            painter.drawEllipse(QRectF(x-(7+5*z), y-(7+5*z), (14+10*z), (14+10*z)))
            painter.setBrush(QColor(190,255,249,150+int(90*z)))
            painter.drawEllipse(QRectF(x-rr,y-rr,rr*2,rr*2))

        # Central core: layered radial energy, bass controls size; RMS/beat controls luminance.
        core_r = 13.5 + 5.5*s.low + 2.0*s.beat
        core_grad = QRadialGradient(core_c, core_r*2.4)
        core_grad.setColorAt(0.0, QColor(248,255,255,248))
        core_grad.setColorAt(0.13, QColor(116,255,244,230))
        core_grad.setColorAt(0.36, QColor(28,235,225,150+int(62*s.energy)))
        core_grad.setColorAt(0.66, QColor(20,155,220,42+int(54*s.mid)))
        core_grad.setColorAt(1.0, QColor(0,0,0,0))
        painter.setPen(Qt.NoPen); painter.setBrush(QBrush(core_grad))
        halo = core_r*2.4
        painter.drawEllipse(QRectF(core_c.x()-halo, core_c.y()-halo, halo*2, halo*2))

        # Thin faceted containment shell around the nucleus.
        shell_r = 20.0 + 2.4*s.energy
        pts=[]
        for i in range(12):
            a = -math.pi/2 + i*math.tau/12.0 + t*0.07
            wobble = 1.0 + 0.045*math.sin(t*1.3+i*1.7) + 0.055*(zones[i%8] if zones else 0.0)
            pts.append(QPointF(core_c.x()+math.cos(a)*shell_r*wobble,
                               core_c.y()+math.sin(a)*shell_r*wobble))
        shell = QPolygonF(pts)
        for width, alpha in ((4.5,18),(1.15,148)):
            c=QColor(cyan); c.setAlpha(int(alpha*(0.72+0.36*s.energy)))
            painter.setPen(self._pen(c,width)); painter.setBrush(Qt.NoBrush); painter.drawPolygon(shell)

        # Beat shockwave; short-lived and geometric rather than a generic bar flash.
        pulse = max(s.beat, s.flux*0.72)
        if pulse > 0.015:
            pr = 24.0 + (1.0-pulse)*25.0
            c=QColor(140,255,248,int(118*pulse))
            painter.setPen(self._pen(c,1.0)); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(core_c.x()-pr, core_c.y()-pr*0.34, pr*2, pr*0.68))

        # Sparse upward energy motes. High frequencies wake them without turning the projection noisy.
        for i in range(18):
            seed=i*8.731
            y=18.0 + (math.sin(seed+t*(0.20+0.20*s.high))*0.5+0.5)*116.0
            spread=18.0 + 22.0*(1.0-max(0.0,min(1.0,(y-18.0)/116.0)))
            x=core_c.x()+math.sin(seed*1.91+t*0.28)*spread
            r=0.55+0.75*((i%4)/3.0)
            a=int((18+92*s.high)*(0.45+0.55*((i*5)%9)/8.0))
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(104,255,241,a))
            painter.drawEllipse(QRectF(x-r,y-r,r*2,r*2))

        painter.end()


class ProjectionController(QObject):
    activeScreenChanged = Signal(str)
    projectionFailed = Signal(str, str)
    PROJECTION_STYLES = get_registry().keys("projection")

    def __init__(self, frame_provider: Callable[[], object | None], parent=None):
        super().__init__(parent)
        self.registry = get_registry()
        self._window_entry = None
        self._frame_provider = frame_provider
        self._window: HolographicOrbitWindow | None = None
        self._screen_name = ""
        self._projection_style = "orbital_atlas"
        self._last_anchor = QRect()

    def active_screen(self) -> str:
        return self._screen_name

    def projection_style(self) -> str:
        return self._projection_style

    def _window_type(self):
        entry = self.registry.resolve(self._projection_style, 'projection')
        return (entry or self.registry.resolve('orbital_atlas', 'projection')).factory

    def _ensure_window(self):
        entry = self.registry.resolve(self._projection_style, 'projection')
        entry = entry or self.registry.resolve('orbital_atlas', 'projection')
        if self._window is not None and self._window_entry is entry:
            return self._window
        try:
            next_window = entry.factory(self._frame_provider)
        except Exception as exc:
            if entry.source != 'package':
                raise
            key, reason = entry.id, str(exc)[:240]
            entry = self.registry.resolve('orbital_atlas', 'projection')
            next_window = entry.factory(self._frame_provider)
            self._projection_style = entry.id
            QTimer.singleShot(0, lambda failed_key=key, message=reason: self.projectionFailed.emit(failed_key, message))
        if self._window is not None:
            self._window.close()
            self._window.deleteLater()
        self._window = next_window
        self._window_entry = entry
        if entry.source == 'package':
            window = self._window
            window.failed.connect(lambda reason, current=window, key=entry.id: self._package_failed(current, key, reason))
        return self._window

    def _package_failed(self, window, key, reason):
        if window is not self._window:
            return
        import logging
        logging.getLogger('aureon').warning('Projection %s failed: %s', key, reason)
        self.set_projection_style('orbital_atlas')
        self.projectionFailed.emit(key, reason)

    def refresh_content(self):
        entry = self.registry.resolve(self._projection_style, 'projection')
        if self._window is None or self._window_entry is entry:
            return
        if self._screen_name:
            self.activate(self._last_anchor)
        else:
            self._window.close()
            self._window.deleteLater()
            self._window = None
            self._window_entry = None

    def set_projection_style(self, style: str):
        style = str(style or "orbital_atlas").strip().lower()
        if self.registry.resolve(style, "projection") is None:
            style = "orbital_atlas"
        if style == self._projection_style:
            return
        was_active = bool(self._screen_name)
        anchor = QRect(self._last_anchor)
        if self._window is not None:
            try:
                self._window.close()
                self._window.deleteLater()
            except Exception:
                pass
            self._window = None
        self._projection_style = style
        if was_active:
            self._screen_name = ""
            self.activate(anchor)

    def _position_for_anchor(self, anchor: QRect):
        window = self._ensure_window()
        w, h = window.width(), window.height()
        app = QApplication.instance()
        screen = QApplication.screenAt(anchor.center()) if app is not None and anchor is not None and not anchor.isNull() else None
        if screen is None:
            screen = QApplication.primaryScreen()
        geo = screen.geometry() if screen is not None else QRect(0, 0, 1920, 1080)
        if anchor is None or anchor.isNull():
            return geo.right()-w-8, geo.bottom()-h-40
        x = int(round(anchor.center().x() - w / 2.0))
        y = int(round(anchor.center().y() - h + max(6, anchor.height() * 0.55)))
        x = max(geo.left(), min(x, geo.right() - w + 1))
        y = max(geo.top(), min(y, geo.bottom() - h + 1))
        return x, y

    def activate(self, anchor: QRect | None = None) -> bool:
        anchor = QRect(anchor or QRect())
        self._last_anchor = QRect(anchor)
        window = self._ensure_window()
        x, y = self._position_for_anchor(anchor)
        window.move(x, y)
        window.show()
        window.raise_()
        window._apply_native_window_policy()
        QTimer.singleShot(0, window._ensure_native_topmost)
        self._screen_name = "tray"
        self.activeScreenChanged.emit(self._screen_name)
        return True

    def toggle(self, anchor: QRect | None = None):
        if self._screen_name:
            self.stop()
        else:
            self.activate(anchor)

    def stop(self):
        if self._window is not None:
            self._window.hide()
        if self._screen_name:
            self._screen_name = ""
            self.activeScreenChanged.emit("")

    def shutdown(self):
        self._screen_name = ""
        if self._window is not None:
            try:
                self._window.close()
                self._window.deleteLater()
            except Exception:
                pass
            self._window = None
        self.activeScreenChanged.emit("")
