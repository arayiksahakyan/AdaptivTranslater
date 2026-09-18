"""Qt bridge: exactly one job in flight, cooperative cancellation, owned resources."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot

from app.pipeline.translation_pipeline import PipelineJob, PipelineResult, TranslationPipeline

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _WorkItem:
    job: PipelineJob
    cancelled: Event


class _PipelineWorker(QObject):
    result = Signal(object)
    captured = Signal(int)
    stopped = Signal()

    def __init__(self, factory: Callable[[], TranslationPipeline]) -> None:
        super().__init__()
        self._factory = factory
        self._pipeline: TranslationPipeline | None = None

    @Slot(object)
    def execute(self, item: _WorkItem) -> None:
        try:
            if item.cancelled.is_set():
                outcome = PipelineResult(item.job.revision, "cancelled")
            else:
                if self._pipeline is None:
                    self._pipeline = self._factory()
                outcome = self._pipeline.run(
                    item.job,
                    lambda: self.captured.emit(item.job.revision),
                    item.cancelled.is_set,
                )
        except Exception as exc:
            logger.warning("Worker failed (%s)", type(exc).__name__)
            outcome = PipelineResult(
                item.job.revision, "error", error="Worker unavailable. Pause and retry."
            )
        self.result.emit(outcome)

    @Slot()
    def shutdown(self) -> None:
        if self._pipeline is not None:
            self._pipeline.close()
            self._pipeline = None
        self.stopped.emit()


class PipelineRunner(QObject):
    result = Signal(object)
    captured = Signal(int)
    stopped = Signal()
    _requested = Signal(object)
    _stop_requested = Signal()

    def __init__(self, factory: Callable[[], TranslationPipeline], parent: QObject | None = None):
        super().__init__(parent)
        self._thread = QThread(self)
        self._worker = _PipelineWorker(factory)
        self._worker.moveToThread(self._thread)
        self._requested.connect(self._worker.execute)
        self._stop_requested.connect(self._worker.shutdown)
        self._worker.captured.connect(self.captured)
        self._worker.result.connect(self._on_result)
        self._worker.stopped.connect(self._thread.quit, Qt.ConnectionType.DirectConnection)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self.stopped)
        self._current: _WorkItem | None = None
        self.closing = False
        self._thread.start()

    @property
    def busy(self) -> bool:
        return self._current is not None

    @property
    def running(self) -> bool:
        return self._thread.isRunning()

    def submit(self, job: PipelineJob) -> bool:
        if self.busy or self.closing:
            return False
        self._current = _WorkItem(job, Event())
        self._requested.emit(self._current)
        return True

    def cancel(self) -> None:
        if self._current is not None:
            self._current.cancelled.set()

    @Slot(object)
    def _on_result(self, result: PipelineResult) -> None:
        self._current = None
        self.result.emit(result)

    def shutdown(self) -> None:
        if self.closing:
            return
        self.closing = True
        self.cancel()
        # Enqueued after the current call; cleanup runs on the owning worker thread.
        self._stop_requested.emit()

    def wait_after_event_loop(self) -> None:
        """Final safety net after QApplication.exec() exits, never during UI work.

        External Qt quit/session-exit routes may bypass our asynchronous close
        handler. Keep ownership alive until cleanup and QThread completion.
        """
        self.shutdown()
        self._thread.wait()
