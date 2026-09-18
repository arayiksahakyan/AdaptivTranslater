"""Limited Linux/X11 development preview, not the product target."""

from collections.abc import Callable, Sequence

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QWidget

from app.capture.base import CaptureRegion
from app.errors import PlatformError


class PreviewPlatform:
    supports_click_through = False
    requires_hide = True
    description = "Linux preview · X11, scale 100% · app-local shortcuts only"

    def __init__(self) -> None:
        self._windows: list[QWidget] = []
        self._shortcuts: list[QShortcut] = []

    def prepare_windows(self, windows: Sequence[QWidget]) -> list[str]:
        self._windows = list(windows)
        return ["Windows click-through/global hotkeys require Windows verification."]

    def capture_region(self, window: QWidget, local_rect: QRect) -> CaptureRegion:
        if QApplication.platformName() != "xcb":
            raise PlatformError("Live Linux preview capture requires an X11 session (xcb).")
        if abs(window.devicePixelRatioF() - 1.0) > 0.01:
            raise PlatformError(
                "Linux preview capture is limited to 100% scale. Use Windows for DPI tests."
            )
        point = window.mapToGlobal(local_rect.topLeft())
        return CaptureRegion(point.x(), point.y(), local_rect.width(), local_rect.height())

    def set_click_through(self, window: QWidget, enabled: bool) -> None:
        if enabled:
            raise PlatformError("Native click-through is available only on Windows.")

    def register_hotkeys(
        self,
        app: QApplication,
        toggle_running: Callable[[], None],
        toggle_mode: Callable[[], None],
    ) -> list[str]:
        for key, callback in (("Ctrl+Shift+T", toggle_running), ("Ctrl+Shift+L", toggle_mode)):
            shortcut = QShortcut(QKeySequence(key), self._windows[0])
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)
        return []

    def close(self) -> None:
        for shortcut in self._shortcuts:
            shortcut.setEnabled(False)
        self._shortcuts.clear()
