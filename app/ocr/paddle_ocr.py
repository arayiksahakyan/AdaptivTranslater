"""PaddleOCR 3 adapter. Import, model loading, and inference all run in the worker."""

import logging
from collections.abc import Callable, Iterable, Mapping
from typing import Any

import numpy as np

from app.capture.base import RGBImage
from app.errors import OCRError, OCRInitializationError
from app.ocr.base import OCRResult
from app.ocr.paddle_config import paddle_options

logger = logging.getLogger(__name__)


def parse_results(pages: Iterable[Mapping[str, Any]]) -> list[OCRResult]:
    """Read PaddleOCR 3 result dictionaries without saving images/JSON to disk."""
    results: list[OCRResult] = []
    for page in pages:
        texts, scores, polygons = page["rec_texts"], page["rec_scores"], page["rec_polys"]
        if not (len(texts) == len(scores) == len(polygons)):
            raise ValueError("Inconsistent PaddleOCR result lengths.")
        for text, score, polygon in zip(texts, scores, polygons, strict=True):
            points = tuple((float(p[0]), float(p[1])) for p in polygon)
            confidence = float(score)
            if len(points) < 4 or not np.isfinite(points).all():
                raise ValueError("Invalid OCR polygon.")
            if not np.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError("Invalid OCR confidence.")
            results.append(OCRResult(str(text), confidence, points))
    return results


class PaddleOCRProvider:
    def __init__(self, language: str = "en", engine_factory: Callable[..., Any] | None = None):
        self.language = language
        self._engine: Any = None
        self._engine_factory = engine_factory

    def _load(self) -> None:
        if self._engine is not None:
            return
        factory = self._engine_factory
        if factory is None:
            try:
                from paddleocr import PaddleOCR

                factory = PaddleOCR
            except ImportError as exc:
                raise OCRInitializationError(
                    "PaddleOCR is unavailable. Install requirements-ocr.txt in this venv."
                    " Move/resize the lens to retry initialization."
                ) from exc
            except Exception as exc:
                logger.warning("OCR import failed (%s)", type(exc).__name__)
                raise OCRInitializationError(
                    "PaddleOCR could not initialize. Run tools.paddle_diagnostic for details. "
                    "Move/resize the lens to retry initialization."
                ) from exc
        logger.info("Initializing local PaddleOCR; first use may download model weights")
        try:
            self._engine = factory(**paddle_options(self.language))
        except Exception as exc:
            logger.warning("OCR initialization failed (%s)", type(exc).__name__)
            raise OCRInitializationError(
                "OCR model could not load. Check OCR language, model downloads, and "
                "the pinned CPU dependencies in DEVELOPMENT.md. "
                "Move/resize the lens to retry initialization."
            ) from exc

    def recognize(self, image: RGBImage) -> list[OCRResult]:
        self._load()
        try:
            # Paddle's numpy path uses OpenCV's BGR convention.
            bgr = np.ascontiguousarray(image[:, :, ::-1])
            return parse_results(self._engine.predict(bgr))
        except Exception as exc:
            logger.warning("OCR inference failed (%s)", type(exc).__name__)
            raise OCRError("OCR failed. Check model compatibility and try again.") from exc

    def close(self) -> None:
        self._engine = None
