from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Protocol

from app.capture.base import CaptureRegion

if TYPE_CHECKING:
    from PySide6.QtCore import QRect
    from PySide6.QtWidgets import QApplication, QWidget


class PlatformAdapter(Protocol):
    supports_click_through: bool
    requires_hide: bool
    description: str

    def prepare_windows(self, windows: Sequence[QWidget]) -> list[str]: ...

    def capture_region(self, window: QWidget, local_rect: QRect) -> CaptureRegion: ...

    def set_click_through(self, window: QWidget, enabled: bool) -> None: ...

    def register_hotkeys(
        self,
        app: QApplication,
        toggle_running: Callable[[], None],
        toggle_mode: Callable[[], None],
    ) -> list[str]: ...

    def close(self) -> None: ...
