from __future__ import annotations

import math
import sys
import time
from typing import Callable

try:
    import ctypes
except Exception:
    ctypes = None

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


class ProjectionHost(QWidget):
    """Shared alpha window, audio snapshot source and native input/z-order policy."""

    stopRequested = Signal()

    WIDTH = 208
    HEIGHT = 186

    def __init__(self, frame_provider: Callable[[], object | None]):
        super().__init__(None)
        self._frame_provider = frame_provider
        self._core = ReactiveAudioCore(zone_count=8)
        self._start = time.perf_counter()
        self.setWindowTitle("Aureon Tray Hologram")
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        try:
            flags |= Qt.WindowDoesNotAcceptFocus
        except Exception:
            pass
        try:
            flags |= Qt.WindowTransparentForInput
        except Exception:
            pass
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setStyleSheet("background: transparent;")
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self.update)

        # Windows taskbar is itself a topmost shell surface. Clicking it can move
        # another topmost tool window behind the taskbar in the topmost band.
        # Re-assert z-order at a low cadence without ever activating the hologram.
        self._native_topmost_timer = QTimer(self)
        self._native_topmost_timer.setTimerType(Qt.CoarseTimer)
        self._native_topmost_timer.setInterval(260)
        self._native_topmost_timer.timeout.connect(self._ensure_native_topmost)

    def _native_hwnd(self) -> int:
        if sys.platform != "win32" or ctypes is None:
            return 0
        try:
            return int(self.winId())
        except Exception:
            return 0

    def _apply_native_window_policy(self):
        """Make the hologram a non-activating, shell-click-through topmost HWND."""
        hwnd = self._native_hwnd()
        if not hwnd:
            return
        try:
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000

            get_style = getattr(user32, "GetWindowLongPtrW", None)
            set_style = getattr(user32, "SetWindowLongPtrW", None)
            if get_style is None or set_style is None:
                get_style = user32.GetWindowLongW
                set_style = user32.SetWindowLongW
                style_type = ctypes.c_long
            else:
                style_type = ctypes.c_ssize_t

            get_style.argtypes = [wintypes.HWND, ctypes.c_int]
            get_style.restype = style_type
            set_style.argtypes = [wintypes.HWND, ctypes.c_int, style_type]
            set_style.restype = style_type

            ex = int(get_style(wintypes.HWND(hwnd), GWL_EXSTYLE))
            ex |= WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            set_style(wintypes.HWND(hwnd), GWL_EXSTYLE, style_type(ex))
            self._ensure_native_topmost()
        except Exception:
            # Qt flags remain the safe cross-platform fallback.
            return

    def _ensure_native_topmost(self):
        if not self.isVisible():
            return
        hwnd = self._native_hwnd()
        if not hwnd:
            return
        try:
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            SWP_NOOWNERZORDER = 0x0200

            set_pos = user32.SetWindowPos
            set_pos.argtypes = [
                wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                ctypes.c_int, ctypes.c_int, wintypes.UINT,
            ]
            set_pos.restype = wintypes.BOOL
            HWND_TOPMOST = wintypes.HWND(-1)
            set_pos(
                wintypes.HWND(hwnd), HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOOWNERZORDER,
            )
        except Exception:
            return

    def nativeEvent(self, eventType, message):
        # WA_TransparentForMouseEvents is Qt-side only. On Windows explicitly
        # report HTTRANSPARENT so hit-testing falls through to Explorer's taskbar.
        if sys.platform == "win32" and ctypes is not None:
            try:
                from ctypes import wintypes

                class MSG(ctypes.Structure):
                    _fields_ = [
                        ("hwnd", wintypes.HWND),
                        ("message", wintypes.UINT),
                        ("wParam", wintypes.WPARAM),
                        ("lParam", wintypes.LPARAM),
                        ("time", wintypes.DWORD),
                        ("pt", wintypes.POINT),
                    ]

                msg = MSG.from_address(int(message))
                WM_NCHITTEST = 0x0084
                WM_MOUSEACTIVATE = 0x0021
                HTTRANSPARENT = -1
                MA_NOACTIVATE = 3
                if msg.message == WM_NCHITTEST:
                    return True, HTTRANSPARENT
                if msg.message == WM_MOUSEACTIVATE:
                    return True, MA_NOACTIVATE
            except Exception:
                pass
        return super().nativeEvent(eventType, message)

    def showEvent(self, event):
        self._start = time.perf_counter()
        self._core.reset()
        self._timer.start()
        super().showEvent(event)
        self._apply_native_window_policy()
        self._native_topmost_timer.start()

    def hideEvent(self, event):
        self._timer.stop()
        self._native_topmost_timer.stop()
        super().hideEvent(event)

    def cleanup(self):
        self._timer.stop()
        self._native_topmost_timer.stop()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)


