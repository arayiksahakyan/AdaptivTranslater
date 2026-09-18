import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.capture.base import CaptureRegion
from app.pipeline.translation_pipeline import PipelineJob, TranslationPipeline
from tests.fakes import FakeCapture, FakeOCR, FakeTranslator


@pytest.fixture
def capture():
    return FakeCapture()


@pytest.fixture
def ocr():
    return FakeOCR()


@pytest.fixture
def translator():
    return FakeTranslator()


@pytest.fixture
def pipeline(capture, ocr, translator):
    return TranslationPipeline(capture, ocr, translator)


@pytest.fixture
def job():
    return PipelineJob(1, CaptureRegion(-400, 100, 120, 80), "auto", "en")
