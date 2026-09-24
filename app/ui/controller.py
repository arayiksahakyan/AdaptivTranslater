"""GUI-thread coordinator: native geometry, capture visibility, and current results."""

import logging
from time import monotonic

from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication, QWidget

from app.config import AppConfig
from app.errors import LensError
from app.pipeline.translation_pipeline import PipelineJob, PipelineResult
from app.pipeline.worker import PipelineRunner
from app.platform.base import PlatformAdapter
from app.translation.registry import PROVIDER_LABELS
from app.ui.control_panel import ControlPanel
from app.ui.overlay import LensOverlay

logger = logging.getLogger(__name__)


class LensController(QObject):
    stopped = Signal()

    def __init__(
        self,
        config: AppConfig,
        lens: LensOverlay,
        panel: ControlPanel,
        platform: PlatformAdapter,
        runner: PipelineRunner,
    ) -> None:
        super().__init__()
        self.config, self.lens, self.panel = config, lens, panel
        self.platform, self.runner = platform, runner
        self.revision = 0
        self.active = False
        self.closing = False
        self._in_flight = False
        self._pending: PipelineJob | None = None
        self._hidden: list[QWidget] = []
        self._next_attempt = 0.0
        self._errors = 0
        self._logged_region = None
        self.source, self.target = config.source_language, config.target_language
        self.provider = config.provider
        self.timer = QTimer(self)
        self.timer.setInterval(config.capture_interval_ms)
        self.timer.timeout.connect(self.tick)
        self.settle_timer = QTimer(self)
        self.settle_timer.setSingleShot(True)
        self.settle_timer.timeout.connect(self._dispatch)
        panel.toggle_requested.connect(self.toggle_running)
        panel.mode_requested.connect(self.toggle_mode)
        panel.edit_requested.connect(self.edit_mode)
        panel.languages_changed.connect(self.set_languages)
        panel.provider_changed.connect(self.set_provider)
        panel.close_requested.connect(self.shutdown)
        lens.close_requested.connect(self.shutdown)
        lens.edit_requested.connect(self.edit_mode)
        lens.geometry_changed.connect(self.invalidate)
        lens.interaction_changed.connect(self._interaction_changed)
        runner.captured.connect(self._capture_finished)
        runner.result.connect(self._result)
        runner.stopped.connect(self._stopped)

    def initialize(self, app: QApplication) -> None:
        notices = self.platform.prepare_windows((self.lens, self.panel))
        notices.extend(self.platform.register_hotkeys(app, self.toggle_running, self.toggle_mode))
        self.panel.platform_note.setText("\n".join((self.platform.description, *notices)))
        self.panel.mode_button.setEnabled(self.platform.supports_click_through)
        handle = self.lens.windowHandle()
        if handle is not None:
            handle.screenChanged.connect(self.invalidate)

    @Slot()
    def invalidate(self, *_args) -> None:
        self.revision += 1
        self.runner.cancel()
        self.lens.set_translation("")
        self._next_attempt = 0
        self._errors = 0
        if self._pending is not None:
            self.settle_timer.stop()
            self._pending = None
            self._in_flight = False
            self._restore_windows()

    @Slot(bool)
    def _interaction_changed(self, _editing: bool) -> None:
        self.invalidate()

    @Slot(str, str)
    def set_languages(self, source: str, target: str) -> None:
        self.source, self.target = source, target
        self.invalidate()

    @Slot(str)
    def set_provider(self, provider: str) -> None:
        self.provider = provider
        self.invalidate()
        label = PROVIDER_LABELS[provider]
        self.panel.set_status(f"Provider selected: {label}.")

    @Slot()
    def toggle_running(self) -> None:
        if self.closing:
            return
        self.active = not self.active
        self.invalidate()
        self.panel.set_running(self.active)
        self.panel.set_status("Running — waiting for capture / OCR" if self.active else "Paused")
        if self.active:
            self.timer.start()
            self.tick()
        else:
            self.timer.stop()

    @Slot()
    def toggle_mode(self) -> None:
        if self.closing:
            return
        enabled = not self.lens.click_through
        try:
            self.platform.set_click_through(self.lens, enabled)
        except LensError as exc:
            self.panel.set_status(str(exc), error=True)
            return
        self.lens.set_mode(enabled)
        self.panel.set_mode(enabled)
        self.invalidate()

    @Slot()
    def edit_mode(self) -> None:
        self.lens.cancel_interaction()
        if self.lens.click_through:
            self.toggle_mode()

    @Slot()
    def tick(self) -> None:
        if (
            not self.active
            or self.closing
            or self._in_flight
            or self.runner.busy
            or self.lens.interacting
            or self.lens.isMinimized()
            or not self.lens.isVisible()
            or monotonic() < self._next_attempt
            or QApplication.activePopupWidget() is not None
            or QApplication.activeModalWidget() is not None
        ):
            return
        try:
            region = self.platform.capture_region(self.lens, self.lens.capture_rect())
        except Exception as exc:
            message = (
                str(exc) if isinstance(exc, LensError) else "Cannot determine the capture region."
            )
            self._show_error(message)
            return
        self._pending = PipelineJob(self.revision, region, self.source, self.target, self.provider)
        if region != self._logged_region:
            logger.debug("Physical capture region: %s", region)
            self._logged_region = region
        self._in_flight = True
        if self.config.capture_mode == "hide" or self.platform.requires_hide:
            self._hidden = [
                w for w in (self.lens, self.panel) if w.isVisible() and not w.isMinimized()
            ]
            for window in self._hidden:
                window.hide()
            self.settle_timer.start(self.config.hide_settle_ms)
        else:
            self._dispatch()

    @Slot()
    def _dispatch(self) -> None:
        job, self._pending = self._pending, None
        if job is None or self.closing or not self.active or job.revision != self.revision:
            self._in_flight = False
            self._restore_windows()
            return
        if not self.runner.submit(job):
            self._in_flight = False
            self._restore_windows()

    def _restore_windows(self) -> None:
        windows, self._hidden = self._hidden, []
        for window in windows:
            # Restoring after capture must not activate the lens over the target app.
            window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
            window.show()

    @Slot(int)
    def _capture_finished(self, _revision: int) -> None:
        self._restore_windows()

    def _show_error(self, message: str) -> None:
        # Geometry/platform errors occur before the core sees a frame. Force the
        # next valid job to render again after this method clears the old output.
        self.revision += 1
        self.runner.cancel()
        self._errors += 1
        self._next_attempt = monotonic() + min(8, 0.5 * 2 ** min(self._errors, 4))
        self.lens.set_translation("")
        self.panel.set_status(message + " Retrying; Pause stops retries.", error=True)

    @Slot(object)
    def _result(self, result: PipelineResult) -> None:
        self._in_flight = False
        self._restore_windows()
        if self.closing or not self.active or result.revision != self.revision:
            logger.debug("Discarded obsolete pipeline result")
            return
        if result.status == "error":
            self._show_error(result.error)
            return
        if result.status == "cancelled":
            return
        self._errors = 0
        self._next_attempt = 0
        if result.status == "translated":
            self.lens.set_translation(result.translated_text)
            self.panel.set_status(
                f"Running — {PROVIDER_LABELS[self.provider]}"
                + (" (cache hit)" if result.cache_hit else "")
            )
        elif result.status == "empty":
            self.lens.set_translation("")
            self.panel.set_status("Running — no confident text detected")
        if result.status != "unchanged_image":
            translation = "cache" if result.cache_hit else f"{result.translation_ms:.0f} ms"
            if result.status in ("unchanged_text", "empty"):
                translation = "skipped"
            self.panel.metrics.setText(
                f"Capture: {result.capture_ms:.0f} ms | OCR: {result.ocr_ms:.0f} ms | "
                f"Translation: {translation}"
            )

    @Slot()
    def shutdown(self) -> None:
        if self.closing:
            return
        logger.info("Shutdown requested; waiting for any active native OCR call")
        self.closing = True
        self.active = False
        self.timer.stop()
        self.settle_timer.stop()
        self.invalidate()
        # Wait for an in-flight capture before restoring, avoiding self-capture.
        if not self.runner.busy:
            self._restore_windows()
        self.panel.set_status("Closing — waiting for current OCR operation to finish…")
        self.panel.start_button.setEnabled(False)
        self.panel.mode_button.setEnabled(False)
        self.panel.source.setEnabled(False)
        self.panel.target.setEnabled(False)
        self.platform.close()
        self.runner.shutdown()

    @Slot()
    def _stopped(self) -> None:
        self._restore_windows()
        self.lens.hide()
        self.panel.hide()
        logger.info("Worker cleaned up; shutdown complete")
        self.stopped.emit()
