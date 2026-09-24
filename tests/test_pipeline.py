import logging
from dataclasses import replace

import pytest

from app.errors import CaptureError, OCRError, TranslationError
from app.ocr.paddle_ocr import PaddleOCRProvider
from app.translation.cache import TranslationCache
from app.translation.mock_translator import MockTranslationProvider


def test_unchanged_frame_skips_ocr_and_translation(pipeline, job, capture, ocr, translator):
    first = pipeline.run(job)
    assert first.status == "translated"
    assert first.translated_text == "en: Hello world!"
    assert pipeline.run(job).status == "unchanged_image"
    assert capture.calls == 2 and ocr.calls == 1 and len(translator.calls) == 1


def test_visual_change_with_same_normalized_text_skips_translation(
    pipeline, job, capture, ocr, translator
):
    pipeline.run(job)
    capture.image[:] = 60
    ocr.text = "  Hello\t world! "
    assert pipeline.run(job).status == "unchanged_text"
    assert ocr.calls == 2 and len(translator.calls) == 1


def test_a_b_a_uses_cache(pipeline, job, capture, ocr, translator):
    pipeline.run(job)
    capture.image[:] = 60
    ocr.text = "Different"
    pipeline.run(job)
    capture.image[:] = 0
    ocr.text = "Hello world!"
    assert pipeline.run(job).cache_hit
    assert len(translator.calls) == 2


@pytest.mark.parametrize(
    "change", [{"revision": 2}, {"target_language": "ru"}, {"source_language": "en"}]
)
def test_context_change_reprocesses_static_image(pipeline, job, ocr, change):
    pipeline.run(job)
    assert pipeline.run(replace(job, **change)).status == "translated"
    assert ocr.calls == 2


def test_region_change_without_revision_still_reprocesses(pipeline, job, ocr):
    pipeline.run(job)
    moved = replace(job, region=replace(job.region, left=-600))
    assert pipeline.run(moved).status == "translated"
    assert ocr.calls == 2


@pytest.mark.parametrize("confidence", [0.1, float("nan"), 1.1])
def test_empty_or_low_confidence_clears_output(pipeline, job, ocr, translator, confidence):
    ocr.confidence = confidence
    result = pipeline.run(job)
    assert result.status == "empty" and result.translated_text == ""
    assert not translator.calls


def test_empty_text_after_translation_clears_display(pipeline, job, capture, ocr):
    pipeline.run(job)
    ocr.text = " \n "
    capture.image[:] = 60
    assert pipeline.run(job).status == "empty"


@pytest.mark.parametrize(
    ("resource", "error"),
    [
        ("capture", CaptureError("Cannot capture")),
        ("ocr", OCRError("Cannot recognize")),
        ("translator", TranslationError("Provider offline")),
    ],
)
def test_failures_retry_identical_frame(pipeline, job, resource, error):
    provider = getattr(pipeline, resource)
    provider.error = error
    result = pipeline.run(job)
    assert result.status == "error" and result.error == str(error)
    provider.error = None
    assert pipeline.run(job).status == "translated"


def test_recovery_to_pre_error_text_renders_again(pipeline, job, capture, ocr):
    pipeline.run(job)
    capture.error = CaptureError("Temporary capture failure")
    assert pipeline.run(job).status == "error"
    capture.error = None
    result = pipeline.run(job)
    assert result.status == "translated" and result.cache_hit
    assert ocr.calls == 2


def test_unknown_error_payload_and_text_not_logged(pipeline, job, translator, caplog):
    caplog.set_level(logging.DEBUG, logger="app")
    translator.error = RuntimeError("PRIVATE-SCREEN-TEXT secret-token")
    result = pipeline.run(job)
    assert "PRIVATE" not in result.error + caplog.text
    assert "Hello world!" not in caplog.text
    assert "OCR execution" in caplog.text


def test_text_logging_requires_explicit_opt_in(pipeline, job, caplog):
    caplog.set_level(logging.DEBUG, logger="app")
    pipeline.log_text = True
    pipeline.run(job)
    assert "Hello world!" in caplog.text


def test_capture_callback_fires_even_on_capture_error(pipeline, job, capture):
    capture.error = CaptureError("Unavailable")
    calls = []
    pipeline.run(job, on_captured=lambda: calls.append(True))
    assert calls == [True]


def test_cancel_after_capture_skips_expensive_stages(pipeline, job, ocr):
    captured = []
    result = pipeline.run(job, lambda: captured.append(True), lambda: bool(captured))
    assert result.status == "cancelled" and ocr.calls == 0


def test_cancel_after_ocr_skips_translation(pipeline, job, ocr, translator):
    result = pipeline.run(job, cancelled=lambda: ocr.calls > 0)
    assert result.status == "cancelled" and not translator.calls


def test_cancel_after_translation_does_not_commit_or_cache(pipeline, job, translator):
    result = pipeline.run(job, cancelled=lambda: bool(translator.calls))
    assert result.status == "cancelled" and len(pipeline.cache) == 0
    assert pipeline.run(job).status == "translated"


def test_invalid_languages_are_reported(pipeline, job, capture):
    assert pipeline.run(replace(job, target_language="auto")).status == "error"
    assert capture.calls == 0


def test_injected_empty_cache_is_preserved(pipeline):
    cache = TranslationCache(1)
    from app.pipeline.translation_pipeline import TranslationPipeline

    instance = TranslationPipeline(pipeline.capture, pipeline.ocr, pipeline.translator, cache=cache)
    assert instance.cache is cache


def test_close_releases_both_providers_and_cache(pipeline, job, capture, ocr):
    pipeline.run(job)
    pipeline.close()
    assert capture.closed and ocr.closed and len(pipeline.cache) == 0


def test_mock_explicitly_labels_output_and_validates_languages():
    provider = MockTranslationProvider()
    assert provider.translate("Hello", "auto", "ru") == "[MOCK auto → ru]\nHello"
    with pytest.raises(TranslationError):
        provider.translate("Hello", "bad", "ru")


def test_provider_selection_uses_provider_specific_cache_key(pipeline, job, capture):
    real = FakeRealTranslator()
    pipeline.providers["real"] = real
    assert pipeline.run(job).status == "translated"
    real_job = replace(job, provider_name="real")
    assert pipeline.run(real_job).status == "translated"
    assert len(real.calls) == 1
    assert pipeline.run(real_job).status == "unchanged_image"


class FakeRealTranslator:
    provider_id = "real"

    def __init__(self):
        self.calls = []

    def translate(self, text, source, target):
        self.calls.append((text, source, target))
        return "real translation"


@pytest.mark.parametrize("retry_change", ["region", "source_language", "provider_name"])
def test_initialization_latches_across_error_revisions_and_explicit_change_retries(
    pipeline, job, capture, caplog, retry_change
):
    calls = []

    class Engine:
        def predict(self, image):
            return []

    def factory(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("PRIVATE native initialization details")
        return Engine()

    pipeline.ocr = PaddleOCRProvider(engine_factory=factory)
    first = pipeline.run(job)
    assert first.status == "error" and "Move/resize" in first.error
    restored = []
    # The real controller increments the revision on every error display.
    for revision in range(2, 22):
        result = pipeline.run(replace(job, revision=revision), lambda: restored.append(True))
        assert result.status == "error" and result.error == first.error
    assert len(calls) == 1 and capture.calls == 1 and len(restored) == 20
    assert "PRIVATE" not in caplog.text + first.error
    assert pipeline.run(job, cancelled=lambda: True).status == "cancelled"
    change = {
        "region": replace(job.region, left=job.region.left + 1),
        "source_language": "en",
        "provider_name": "mock",
    }
    retry_job = replace(job, revision=23, **{retry_change: change[retry_change]})
    assert pipeline.run(retry_job).status == "empty"
    assert len(calls) == 2 and capture.calls == 2
    assert pipeline.run(retry_job).status == "unchanged_image"


def test_failed_explicit_retry_is_latched_again(pipeline, job):
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("native failure")

    pipeline.ocr = PaddleOCRProvider(engine_factory=factory)
    assert pipeline.run(job).status == "error"
    moved = replace(job, region=replace(job.region, left=0), revision=2)
    assert pipeline.run(moved).status == "error"
    for revision in range(3, 10):
        assert pipeline.run(replace(moved, revision=revision)).status == "error"
    assert len(calls) == 2
