"""Run with `python -m app.main`; native DPI initialization precedes Qt windows."""

import argparse
import logging
import signal
import sys

from app.config import AppConfig


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translation Lens — local OCR, labeled mock translation"
    )
    parser.add_argument("--capture-mode", choices=("auto", "hide"), default="auto")
    parser.add_argument("--interval-ms", type=int, default=350)
    parser.add_argument("--hide-settle-ms", type=int, default=80)
    parser.add_argument(
        "--ocr-language", default="en", help="Paddle model language; independent of source Auto"
    )
    parser.add_argument("--source", default="auto")
    parser.add_argument("--target", default="en")
    parser.add_argument("--confidence", type=float, default=0.6)
    parser.add_argument(
        "--image-threshold", type=float, default=2.0, help="Mean grayscale difference"
    )
    parser.add_argument("--changed-fraction", type=float, default=0.003)
    parser.add_argument(
        "--debug", action="store_true", help="Timings and cache logs, no screen text"
    )
    parser.add_argument(
        "--log-text", action="store_true", help="Explicitly log recognized text (private data)"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG if args.debug or args.log_text else logging.INFO)
    try:
        from app.errors import LensError
        from app.translation.provider import validate_languages

        config = AppConfig(
            capture_interval_ms=args.interval_ms,
            capture_mode=args.capture_mode,
            hide_settle_ms=args.hide_settle_ms,
            ocr_language=args.ocr_language,
            source_language=args.source,
            target_language=args.target,
            min_ocr_confidence=args.confidence,
            image_mean_threshold=args.image_threshold,
            image_changed_fraction=args.changed_fraction,
            log_text=args.log_text,
        )
        validate_languages(config.source_language, config.target_language)
    except (ValueError, LensError) as exc:
        logger.error("Invalid configuration: %s", exc)
        return 2
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        from app.capture.change_detector import ImageChangeDetector
        from app.capture.screen_capture import MSSCaptureProvider
        from app.ocr.paddle_ocr import PaddleOCRProvider
        from app.pipeline.translation_pipeline import TranslationPipeline
        from app.pipeline.worker import PipelineRunner
        from app.translation.cache import TranslationCache
        from app.translation.mock_translator import MockTranslationProvider
        from app.ui.control_panel import ControlPanel
        from app.ui.controller import LensController
        from app.ui.overlay import LensOverlay

        if sys.platform == "win32":
            from app.platform.windows import WindowsPlatform, configure_dpi_awareness

            configure_dpi_awareness()
            platform = WindowsPlatform(force_hide=config.capture_mode == "hide")
        else:
            from app.platform.preview import PreviewPlatform

            platform = PreviewPlatform()
    except (ImportError, LensError) as exc:
        message = (
            str(exc) if isinstance(exc, LensError) else "Install requirements.txt in this venv."
        )
        logger.error("Startup failed: %s", message)
        return 2

    app = QApplication([sys.argv[0]])
    app.setApplicationName("Translation Lens")
    app.setQuitOnLastWindowClosed(False)  # Hiding both windows during capture is not exit.
    lens = LensOverlay()
    panel = ControlPanel(config.source_language, config.target_language, config.ocr_language)

    def pipeline_factory() -> TranslationPipeline:
        return TranslationPipeline(
            MSSCaptureProvider(),
            PaddleOCRProvider(config.ocr_language),
            MockTranslationProvider(),
            ImageChangeDetector(
                config.image_mean_threshold,
                config.image_pixel_threshold,
                config.image_changed_fraction,
            ),
            TranslationCache(config.cache_size),
            config.min_ocr_confidence,
            config.log_text,
        )

    runner = PipelineRunner(pipeline_factory)
    controller = LensController(config, lens, panel, platform, runner)
    controller.stopped.connect(app.quit)
    screen = app.primaryScreen()
    if screen is not None:
        area = screen.availableGeometry()
        lens.resize(min(720, area.width() - 80), min(360, area.height() - 100))
        lens.move(area.left() + 40, area.top() + 60)
    lens.show()
    panel.show()
    controller.initialize(app)
    if screen is not None:
        panel.adjustSize()
        panel.move(
            max(area.left() + 20, area.right() - panel.width() - 20),
            min(area.top() + 60, max(area.top(), area.bottom() - panel.height() - 20)),
        )
    # Keep Python signal delivery live while Qt is idle. All normal exit routes
    # request shutdown instead of destroying a running QThread.
    signal.signal(signal.SIGINT, lambda *_: controller.shutdown())
    signal.signal(signal.SIGTERM, lambda *_: controller.shutdown())
    heartbeat = QTimer()
    heartbeat.timeout.connect(lambda: None)
    heartbeat.start(200)
    logger.info(
        "Translation Lens started on %s; mock translation; images remain local", sys.platform
    )
    try:
        return app.exec()
    finally:
        controller.shutdown()
        runner.wait_after_event_loop()


if __name__ == "__main__":
    raise SystemExit(main())
