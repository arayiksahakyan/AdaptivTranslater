"""Win32 integration. IMPLEMENTED; REQUIRES WINDOWS VERIFICATION.

All window APIs run in the GUI thread. Import-safe on Linux; DLLs are loaded only
when constructing the Windows adapter or configuring Windows DPI awareness.
"""

import ctypes
import logging
import sys
from collections.abc import Callable, Sequence
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QRect
from PySide6.QtWidgets import QApplication, QWidget

from app.capture.base import CaptureRegion
from app.errors import PlatformError
from app.platform.geometry import map_client_region

logger = logging.getLogger(__name__)
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WM_HOTKEY = 0x0312


def configure_dpi_awareness() -> None:
    """Call before QApplication and mss. Refuse known DPI virtualization."""
    if sys.platform != "win32":
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    try:
        set_awareness = user32.SetProcessDpiAwarenessContext
        set_awareness.argtypes = [ctypes.c_void_p]
        set_awareness.restype = wintypes.BOOL
        get_awareness = user32.GetThreadDpiAwarenessContext
        get_awareness.argtypes = []
        get_awareness.restype = ctypes.c_void_p
        equal = user32.AreDpiAwarenessContextsEqual
        equal.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        equal.restype = wintypes.BOOL
        if not set_awareness(ctypes.c_void_p(-4)) and not equal(
            get_awareness(), ctypes.c_void_p(-4)
        ):
            raise PlatformError(
                "Per-monitor V2 DPI awareness is unavailable. Use Windows 10 1703+."
            )
    except AttributeError:
        raise PlatformError(
            "Required DPI APIs are unavailable. Use Windows 10 1703+ or Windows 11."
        ) from None


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callbacks: dict[int, Callable[[], None]]) -> None:
        super().__init__()
        self.callbacks = callbacks

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and int(msg.wParam) in self.callbacks:
                self.callbacks[int(msg.wParam)]()
                return True, 0
        return False, 0


class WindowsPlatform:
    supports_click_through = True
    description = "Windows · native capture exclusion · Ctrl+Shift+T / Ctrl+Shift+L"

    def __init__(self, force_hide: bool = False) -> None:
        if sys.platform != "win32":
            raise PlatformError("WindowsPlatform requires Windows.")
        self.requires_hide = force_hide or sys.getwindowsversion().build < 19041
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._configure_signatures()
        self._styles: dict[int, int] = {}
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._filter: _HotkeyFilter | None = None
        self._app: QApplication | None = None

    def _configure_signatures(self) -> None:
        u = self._user32
        u.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        u.GetClientRect.restype = wintypes.BOOL
        u.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        u.ClientToScreen.restype = wintypes.BOOL
        u.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
        u.SetWindowDisplayAffinity.restype = wintypes.BOOL
        # LONG_PTR must not be truncated on a 64-bit Python process.
        self._get_style = getattr(u, "GetWindowLongPtrW", u.GetWindowLongW)
        self._set_style = getattr(u, "SetWindowLongPtrW", u.SetWindowLongW)
        self._get_style.argtypes = [wintypes.HWND, ctypes.c_int]
        self._get_style.restype = ctypes.c_ssize_t
        self._set_style.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        self._set_style.restype = ctypes.c_ssize_t
        u.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        u.SetWindowPos.restype = wintypes.BOOL
        u.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        u.RegisterHotKey.restype = wintypes.BOOL
        u.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        u.UnregisterHotKey.restype = wintypes.BOOL

    def prepare_windows(self, windows: Sequence[QWidget]) -> list[str]:
        notices = []
        if not self.requires_hide:
            for window in windows:
                if not self._user32.SetWindowDisplayAffinity(
                    int(window.winId()), WDA_EXCLUDEFROMCAPTURE
                ):
                    logger.warning(
                        "Window capture exclusion failed (Win32 %d)", ctypes.get_last_error()
                    )
                    self.requires_hide = True
        if self.requires_hide:
            self.description = "Windows · hide/capture/restore · may flicker"
            notices.append("Capture uses hide/restore. Verify underlying pixels on Windows.")
        return notices

    def capture_region(self, window: QWidget, local_rect: QRect) -> CaptureRegion:
        hwnd = int(window.winId())
        native = wintypes.RECT()
        origin = wintypes.POINT(0, 0)
        if not self._user32.GetClientRect(
            hwnd, ctypes.byref(native)
        ) or not self._user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            raise PlatformError("Unable to map the lens to physical desktop coordinates.")
        return map_client_region(
            (origin.x, origin.y),
            (native.right - native.left, native.bottom - native.top),
            (window.width(), window.height()),
            (local_rect.x(), local_rect.y(), local_rect.width(), local_rect.height()),
        )

    def set_click_through(self, window: QWidget, enabled: bool) -> None:
        hwnd = int(window.winId())
        ctypes.set_last_error(0)
        current = self._get_style(hwnd, GWL_EXSTYLE)
        if current == 0 and ctypes.get_last_error():
            raise PlatformError("Cannot read lens window styles.")
        self._styles.setdefault(hwnd, current)
        mask = WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        desired = (current | mask) if enabled else (current & ~mask) | (self._styles[hwnd] & mask)
        ctypes.set_last_error(0)
        previous = self._set_style(hwnd, GWL_EXSTYLE, desired)
        if previous == 0 and ctypes.get_last_error():
            raise PlatformError("Cannot change click-through mode; use the control panel to retry.")
        # Refresh cached styles without moving, activating, or changing z-order.
        flags = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020
        if not self._user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, flags):
            self._set_style(hwnd, GWL_EXSTYLE, current)
            raise PlatformError("Cannot apply click-through window styles.")

    def register_hotkeys(
        self,
        app: QApplication,
        toggle_running: Callable[[], None],
        toggle_mode: Callable[[], None],
    ) -> list[str]:
        self._app = app
        notices = []
        for hotkey_id, key, callback in ((0x5101, "T", toggle_running), (0x5102, "L", toggle_mode)):
            # Thread-associated messages continue to arrive while windows are hidden.
            if self._user32.RegisterHotKey(None, hotkey_id, 0x0002 | 0x0004 | 0x4000, ord(key)):
                self._callbacks[hotkey_id] = callback
            else:
                notices.append(f"Ctrl+Shift+{key} unavailable (in use). Use the control panel.")
                logger.warning("Hotkey registration failed (Win32 %d)", ctypes.get_last_error())
        self._filter = _HotkeyFilter(self._callbacks)
        app.installNativeEventFilter(self._filter)
        return notices

    def close(self) -> None:
        for hotkey_id in self._callbacks:
            if not self._user32.UnregisterHotKey(None, hotkey_id):
                logger.warning("Hotkey cleanup failed (Win32 %d)", ctypes.get_last_error())
        self._callbacks.clear()
        if self._app is not None and self._filter is not None:
            self._app.removeNativeEventFilter(self._filter)
        self._filter = None
