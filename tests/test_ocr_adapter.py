import numpy as np
import pytest

from app.errors import OCRError
from app.ocr.paddle_ocr import PaddleOCRProvider, parse_results


def page():
    return {
        "rec_texts": ["Hello"],
        "rec_scores": np.array([0.95]),
        "rec_polys": np.array([[[1, 2], [40, 2], [40, 20], [1, 20]]]),
    }


def test_parse_structured_paddle3_results():
    result = parse_results([page()])[0]
    assert result.text == "Hello" and result.confidence == 0.95
    assert result.bbox == ((1, 2), (40, 2), (40, 20), (1, 20))
    assert parse_results([]) == []
    assert parse_results([{"rec_texts": [], "rec_scores": [], "rec_polys": []}]) == []


def test_reject_mismatched_schema():
    bad = page()
    bad["rec_scores"] = []
    with pytest.raises(ValueError):
        parse_results([bad])


def test_lazy_engine_init_and_rgb_to_bgr_conversion():
    calls = []
    frames = []

    class Engine:
        def predict(self, image):
            frames.append(image.copy())
            return [page()]

    def factory(**kwargs):
        calls.append(kwargs)
        return Engine()

    provider = PaddleOCRProvider("en", engine_factory=factory)
    assert calls == []
    rgb = np.array([[[30, 20, 10]]], dtype=np.uint8)
    assert provider.recognize(rgb)[0].text == "Hello"
    provider.recognize(rgb)
    assert len(calls) == 1 and calls[0]["device"] == "cpu"
    assert calls[0]["text_recognition_model_name"] == "en_PP-OCRv5_mobile_rec"
    assert "lang" not in calls[0]  # Paddle ignores language alongside explicit models.
    assert frames[0].tolist() == [[[10, 20, 30]]]
    provider.close()


def test_non_english_language_is_not_overridden_by_a_model_name():
    options = []

    class Engine:
        def predict(self, image):
            return []

    def factory(**kwargs):
        options.append(kwargs)
        return Engine()

    provider = PaddleOCRProvider("ru", engine_factory=factory)
    provider.recognize(np.zeros((20, 20, 3), dtype=np.uint8))
    assert options[0]["lang"] == "ru"
    assert "text_detection_model_name" not in options[0]


def test_initialization_errors_are_safe_and_retryable():
    def failed_factory(**kwargs):
        raise RuntimeError("token / private details")

    provider = PaddleOCRProvider(engine_factory=failed_factory)
    with pytest.raises(OCRError, match="could not load") as error:
        provider.recognize(np.zeros((10, 10, 3), dtype=np.uint8))
    assert "private" not in str(error.value) and provider._engine is None


def test_inference_errors_are_safe():
    class Engine:
        def predict(self, image):
            raise RuntimeError("private screen text")

    provider = PaddleOCRProvider(engine_factory=lambda **_: Engine())
    with pytest.raises(OCRError, match="OCR failed") as error:
        provider.recognize(np.zeros((10, 10, 3), dtype=np.uint8))
    assert "private" not in str(error.value)
