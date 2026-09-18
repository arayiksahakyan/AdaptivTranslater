import threading

from PySide6.QtCore import QTimer

from app.pipeline.translation_pipeline import TranslationPipeline
from app.pipeline.worker import PipelineRunner
from tests.fakes import FakeOCR


def test_worker_does_not_block_ui_and_cleans_up_on_own_thread(qtbot, job, capture, translator):
    gate, entered = threading.Event(), threading.Event()
    created = []

    class BlockingOCR(FakeOCR):
        def recognize(self, image):
            entered.set()
            if not gate.wait(5):
                raise RuntimeError("Test gate timed out")
            return super().recognize(image)

    ocr = BlockingOCR()

    def factory():
        created.append(threading.get_ident())
        return TranslationPipeline(capture, ocr, translator)

    runner = PipelineRunner(factory)
    results = []
    runner.result.connect(results.append)
    try:
        assert runner.submit(job)
        assert not runner.submit(job)
        qtbot.waitUntil(entered.is_set)
        ticks = []
        QTimer.singleShot(0, lambda: ticks.append(True))
        qtbot.waitUntil(lambda: ticks == [True])
        assert results == []  # main event loop ran while inference is still blocked
        runner.shutdown()
        gate.set()
        qtbot.waitUntil(lambda: not runner.running, timeout=5000)
        qtbot.waitUntil(lambda: bool(results))
        assert results[0].status == "cancelled"
        assert not translator.calls and ocr.closed and capture.closed
        assert created[0] != threading.get_ident()
        assert set(capture.threads + ocr.threads) == {created[0]}
    finally:
        gate.set()
        runner.shutdown()
        qtbot.waitUntil(lambda: not runner.running, timeout=5000)


def test_worker_factory_failure_emits_error_and_can_shutdown(qtbot, job):
    def factory():
        raise RuntimeError("private payload")

    runner = PipelineRunner(factory)
    try:
        with qtbot.waitSignal(runner.result, timeout=3000) as signal:
            runner.submit(job)
        assert signal.args[0].status == "error"
        assert "private" not in signal.args[0].error
    finally:
        with qtbot.waitSignal(runner.stopped, timeout=3000):
            runner.shutdown()


def test_final_wait_cleans_up_without_a_running_gui_event_loop(qapp):
    runner = PipelineRunner(lambda: None)
    runner.wait_after_event_loop()
    assert not runner.running
