from PySide6.QtCore import QObject, QPoint, Qt, Signal

from app.capture.base import CaptureRegion
from app.config import AppConfig
from app.errors import PlatformError
from app.pipeline.translation_pipeline import PipelineResult
from app.ui.control_panel import ControlPanel
from app.ui.controller import LensController
from app.ui.overlay import LensOverlay


class RunnerDouble(QObject):
    captured = Signal(int)
    result = Signal(object)
    stopped = Signal()

    def __init__(self):
        super().__init__()
        self.busy = False
        self.jobs = []
        self.cancelled = False
        self.closing = False

    def submit(self, job):
        if self.busy:
            return False
        self.busy = True
        self.jobs.append(job)
        return True

    def cancel(self):
        self.cancelled = True

    def shutdown(self):
        self.closing = True
        self.stopped.emit()

    def complete(self, result):
        self.busy = False
        self.result.emit(result)


class PlatformDouble:
    requires_hide = False
    supports_click_through = True
    description = "test adapter"

    def capture_region(self, window, rect):
        return CaptureRegion(-200, 30, rect.width(), rect.height())

    def set_click_through(self, window, enabled):
        pass

    def close(self):
        pass


def build_controller(qtbot, hide=False):
    config = AppConfig(hide_settle_ms=20)
    lens, panel = LensOverlay(), ControlPanel("auto", "en", "en")
    qtbot.addWidget(lens)
    qtbot.addWidget(panel)
    platform = PlatformDouble()
    platform.requires_hide = hide
    runner = RunnerDouble()
    controller = LensController(config, lens, panel, platform, runner)
    lens.show()
    panel.show()
    return controller, lens, panel, runner


def test_lens_transparency_flags_min_size_and_plain_text(qtbot):
    lens = LensOverlay()
    qtbot.addWidget(lens)
    lens.show()
    assert lens.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    assert lens.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    image = lens.grab().toImage()
    assert image.pixelColor(lens.width() // 2, lens.HEADER + 20).alpha() == 0
    lens.resize(1, 1)
    assert lens.width() == 280 and lens.height() == 180
    lens.set_translation("<b>literal OCR text</b>")
    assert lens.output.textFormat() == Qt.TextFormat.PlainText
    assert lens.output.isVisible()


def test_drag_and_escape_restore_geometry(qtbot):
    lens = LensOverlay()
    qtbot.addWidget(lens)
    lens.show()
    original = lens.geometry()
    qtbot.mousePress(lens, Qt.MouseButton.LeftButton, pos=QPoint(100, 20))
    qtbot.mouseMove(lens, QPoint(140, 50))
    assert lens.geometry().topLeft() != original.topLeft()
    qtbot.keyClick(lens, Qt.Key.Key_Escape)
    assert lens.geometry() == original and not lens.interacting


def test_resize_corner(qtbot):
    lens = LensOverlay()
    qtbot.addWidget(lens)
    lens.show()
    old = lens.size()
    qtbot.mousePress(lens, Qt.MouseButton.LeftButton, pos=QPoint(old.width() - 3, old.height() - 3))
    qtbot.mouseMove(lens, QPoint(old.width() + 35, old.height() + 20))
    qtbot.mouseRelease(lens, Qt.MouseButton.LeftButton)
    assert lens.width() > old.width() and lens.height() > old.height()


def test_obsolete_result_does_not_render_after_move(qtbot):
    controller, lens, panel, runner = build_controller(qtbot)
    controller.toggle_running()
    old = runner.jobs[-1]
    lens.move(lens.x() + 20, lens.y())
    runner.complete(PipelineResult(old.revision, "translated", translated_text="OLD"))
    assert lens.output.text() == ""
    controller.tick()
    current = runner.jobs[-1]
    runner.complete(PipelineResult(current.revision, "translated", translated_text="NEW"))
    assert lens.output.text() == "NEW"
    controller.shutdown()


def test_pause_discards_late_result_and_clears_output(qtbot):
    controller, lens, panel, runner = build_controller(qtbot)
    controller.toggle_running()
    old = runner.jobs[-1]
    controller.toggle_running()
    runner.complete(PipelineResult(old.revision, "translated", translated_text="OLD"))
    assert lens.output.text() == "" and panel.status.text() == "Paused"
    controller.shutdown()


def test_no_backlog_while_worker_busy(qtbot):
    controller, lens, panel, runner = build_controller(qtbot)
    controller.toggle_running()
    for _ in range(10):
        controller.tick()
    assert len(runner.jobs) == 1
    controller.shutdown()


def test_hide_restore_occurs_at_capture_completion_before_ocr(qtbot):
    controller, lens, panel, runner = build_controller(qtbot, hide=True)
    controller.toggle_running()
    assert not lens.isVisible() and not panel.isVisible()
    qtbot.waitUntil(lambda: len(runner.jobs) == 1)
    assert not lens.isVisible()
    runner.captured.emit(runner.jobs[-1].revision)
    assert lens.isVisible() and panel.isVisible() and runner.busy
    controller.shutdown()


def test_error_before_capture_signal_restores_windows(qtbot):
    controller, lens, panel, runner = build_controller(qtbot, hide=True)
    controller.toggle_running()
    qtbot.waitUntil(lambda: len(runner.jobs) == 1)
    runner.complete(PipelineResult(runner.jobs[-1].revision, "error", error="OCR unavailable"))
    assert lens.isVisible() and panel.isVisible()
    assert "OCR unavailable" in panel.status.text()
    controller.tick()
    assert len(runner.jobs) == 1  # error backoff
    controller.shutdown()


def test_pause_during_settle_cancels_capture_and_restores(qtbot):
    controller, lens, panel, runner = build_controller(qtbot, hide=True)
    controller.toggle_running()
    controller.toggle_running()
    qtbot.wait(40)
    assert runner.jobs == []
    assert lens.isVisible() and panel.isVisible()
    controller.shutdown()


def test_language_and_mode_changes_invalidate_and_update_controls(qtbot):
    controller, lens, panel, runner = build_controller(qtbot)
    before = controller.revision
    panel.target.setCurrentIndex(panel.target.findData("ru"))
    assert controller.target == "ru" and controller.revision > before
    controller.toggle_mode()
    assert lens.click_through and "Click-through" in panel.mode_button.text()
    controller.edit_mode()
    assert not lens.click_through
    controller.shutdown()


def test_geometry_error_advances_revision_for_recovery(qtbot):
    controller, lens, panel, runner = build_controller(qtbot)
    controller.toggle_running()
    initial = runner.jobs[-1]
    runner.complete(PipelineResult(initial.revision, "translated", translated_text="RESULT"))
    controller._show_error("Monitor temporarily unavailable")
    assert controller.revision > initial.revision
    assert lens.output.text() == ""
    controller._next_attempt = 0
    controller.tick()
    assert runner.jobs[-1].revision > initial.revision
    controller.shutdown()


def test_click_through_failure_preserves_edit_mode(qtbot):
    controller, lens, panel, runner = build_controller(qtbot)

    def failure(window, enabled):
        raise PlatformError("Native style failed")

    controller.platform.set_click_through = failure
    controller.toggle_mode()
    assert not lens.click_through and "Mode: Edit" in panel.mode_button.text()
    assert "Native style failed" in panel.status.text()
    controller.shutdown()
