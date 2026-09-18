"""PaddleOCR 3 adapter. Import, model loading, and inference all run in the worker."""

import logging
from collections.abc import Callable, Iterable, Mapping
from typing import Any

import numpy as np

from app.capture.base import RGBImage
from app.errors import OCRError
from app.ocr.base import OCRResult

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
            except ImportError:
                raise OCRError(
                    "PaddleOCR is unavailable. Install requirements-ocr.txt in this venv."
                ) from None
        logger.info("Initializing local PaddleOCR; first use may download model weights")
        try:
            # Paddle 3 ignores `lang` when *any* explicit model name is supplied.
            # Select both mobile models for English; otherwise let Paddle resolve
            # a compatible detection/recognition pair for the chosen language.
            model_options = (
                {
                    "text_detection_model_name": "PP-OCRv5_mobile_det",
                    "text_recognition_model_name": "en_PP-OCRv5_mobile_rec",
                }
                if self.language == "en"
                else {"lang": self.language, "ocr_version": "PP-OCRv5"}
            )
            self._engine = factory(
                **model_options,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                device="cpu",
                enable_mkldnn=False,
                cpu_threads=4,
            )
        except Exception as exc:
            logger.warning("OCR initialization failed (%s)", type(exc).__name__)
            raise OCRError(
                "OCR model could not load. Check OCR language, model downloads, and "
                "the pinned CPU dependencies in DEVELOPMENT.md."
            ) from None

    def recognize(self, image: RGBImage) -> list[OCRResult]:
        self._load()
        try:
            # Paddle's numpy path uses OpenCV's BGR convention.
            bgr = np.ascontiguousarray(image[:, :, ::-1])
            return parse_results(self._engine.predict(bgr))
        except Exception as exc:
            logger.warning("OCR inference failed (%s)", type(exc).__name__)
            raise OCRError("OCR failed. Check model compatibility and try again.") from None

    def close(self) -> None:
        self._engine = None
