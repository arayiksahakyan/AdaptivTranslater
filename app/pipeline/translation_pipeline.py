"""Synchronous core, called only by the background worker in the desktop app."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from app.capture.base import CaptureProvider, CaptureRegion
from app.capture.change_detector import ImageChangeDetector
from app.errors import LensError, TranslationError
from app.ocr.base import OCRProvider
from app.pipeline.text_normalization import normalize_text
from app.translation.base import TranslationProvider
from app.translation.cache import TranslationCache
from app.translation.provider import validate_languages

logger = logging.getLogger(__name__)
ResultStatus = Literal[
    "translated", "empty", "unchanged_image", "unchanged_text", "error", "cancelled"
]


@dataclass(frozen=True)
class PipelineJob:
    revision: int
    region: CaptureRegion
    source_language: str
    target_language: str


@dataclass(frozen=True)
class PipelineResult:
    revision: int
    status: ResultStatus
    text: str = ""
    translated_text: str = ""
    cache_hit: bool = False
    capture_ms: float = 0.0
    ocr_ms: float = 0.0
    translation_ms: float = 0.0
    error: str = ""


class TranslationPipeline:
    def __init__(
        self,
        capture: CaptureProvider,
        ocr: OCRProvider,
        translator: TranslationProvider,
        detector: ImageChangeDetector | None = None,
        cache: TranslationCache | None = None,
        min_confidence: float = 0.6,
        log_text: bool = False,
    ) -> None:
        if not 0 <= min_confidence <= 1:
            raise ValueError("Confidence must be in [0, 1].")
        self.capture = capture
        self.ocr = ocr
        self.translator = translator
        self.detector = detector if detector is not None else ImageChangeDetector()
        self.cache = cache if cache is not None else TranslationCache()
        self.min_confidence = min_confidence
        self.log_text = log_text
        self._context: PipelineJob | None = None
        self._last_text: str | None = None

    def run(
        self,
        job: PipelineJob,
        on_captured: Callable[[], None] = lambda: None,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> PipelineResult:
        timings = {"capture_ms": 0.0, "ocr_ms": 0.0, "translation_ms": 0.0}

        def result(status: ResultStatus, **kwargs) -> PipelineResult:
            return PipelineResult(job.revision, status, **timings, **kwargs)

        try:
            if self._context != job:
                self.detector.reset()
                self._last_text = None
                self._context = job
            validate_languages(job.source_language, job.target_language)
            if cancelled():
                return result("cancelled")
            started = perf_counter()
            try:
                image = self.capture.capture(job.region)
            finally:
                timings["capture_ms"] = (perf_counter() - started) * 1000
                on_captured()
            if cancelled():
                return result("cancelled")
            if not self.detector.has_changed(image):
                return result("unchanged_image")
            started = perf_counter()
            try:
                detections = self.ocr.recognize(image)
            finally:
                timings["ocr_ms"] = (perf_counter() - started) * 1000
                logger.debug("OCR execution: %.1f ms", timings["ocr_ms"])
            if cancelled():
                return result("cancelled")
            text = normalize_text(
                "\n".join(d.text for d in detections if self.min_confidence <= d.confidence <= 1.0)
            )
            if self.log_text:
                logger.debug("Detected text (explicit opt-in): %r", text)
            if not text:
                self.detector.commit(image)
                self._last_text = ""
                return result("empty")
            if text == self._last_text:
                self.detector.commit(image)
                return result("unchanged_text")
            key = (job.source_language, job.target_language, text)
            translated = self.cache.get(key)
            cache_hit = translated is not None
            if translated is None:
                started = perf_counter()
                try:
                    translated = self.translator.translate(
                        text, job.source_language, job.target_language
                    )
                    if not isinstance(translated, str) or not translated.strip():
                        raise TranslationError(
                            "Translation provider returned an empty or invalid result."
                        )
                finally:
                    timings["translation_ms"] = (perf_counter() - started) * 1000
                    logger.debug("Translation execution: %.1f ms", timings["translation_ms"])
                if cancelled():
                    return result("cancelled")
                self.cache.put(key, translated)
            if cancelled():
                return result("cancelled")
            self._last_text = text
            self.detector.commit(image)
            return result("translated", text=text, translated_text=translated, cache_hit=cache_hit)
        except Exception as exc:
            # The UI clears output on an error. A later return to the old frame
            # must render again, even when its text was previously successful.
            self.detector.reset()
            self._last_text = None
            # External exceptions can contain recognized text or credentials: never
            # dump str(exc), a traceback, or request bodies for untrusted errors.
            logger.warning("Pipeline failure (%s)", type(exc).__name__)
            public = (
                str(exc) if isinstance(exc, LensError) else "Processing failed. Pause and retry."
            )
            return result("error", error=public)

    def close(self) -> None:
        for resource in (self.capture, self.ocr):
            try:
                resource.close()
            except Exception as exc:
                logger.warning("Provider cleanup failed (%s)", type(exc).__name__)
        self.cache.clear()
