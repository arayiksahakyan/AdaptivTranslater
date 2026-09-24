import sys
from types import SimpleNamespace

import pytest

from app.ocr.paddle_config import paddle_options
from app.ocr.paddle_ocr import PaddleOCRProvider
from tools import ocr_smoke, paddle_diagnostic


def test_environment_reports_versions_and_cache_without_importing_paddle(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setenv("PADDLE_PDX_CACHE_HOME", str(tmp_path))
    monkeypatch.setenv("PADDLE_PDX_MODEL_SOURCE", "bos")
    monkeypatch.setenv("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    monkeypatch.setenv("GOOGLE_TRANSLATE_API_KEY", "PRIVATE-KEY")
    monkeypatch.setitem(sys.modules, "paddle", None)
    detector = tmp_path / "official_models" / "PP-OCRv5_mobile_det"
    detector.mkdir(parents=True)
    paddle_diagnostic.print_environment()
    output = capsys.readouterr().out
    for field in (
        "=== ENVIRONMENT ===", "Python:", "Windows version:", "Architecture:",
        "paddlepaddle:", "paddleocr:", "paddlex:", "numpy:", "opencv-python:", "cv2 module:",
        "PADDLE_PDX_MODEL_SOURCE=bos", "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True",
        f"PADDLE_PDX_CACHE_HOME={tmp_path}", f"{detector} (exists=True)",
        "en_PP-OCRv5_mobile_rec (exists=False)",
    ):
        assert field in output
    assert "PRIVATE-KEY" not in output


def test_smoke_prints_original_traceback_and_closes_provider(monkeypatch, capsys):
    closed = []

    def paddle_source_location(**kwargs):
        raise RuntimeError("actual Paddle failure")

    class FailingProvider(PaddleOCRProvider):
        def __init__(self, language):
            super().__init__(language, engine_factory=paddle_source_location)

        def close(self):
            closed.append(True)
            super().close()

    monkeypatch.setattr("app.ocr.paddle_ocr.PaddleOCRProvider", FailingProvider)
    monkeypatch.setattr(sys, "argv", ["ocr_smoke"])
    assert ocr_smoke.main() == 1
    output = capsys.readouterr().out
    for field in (
        "=== ENVIRONMENT ===", "=== ORIGINAL EXCEPTION ===",
        "Exception class: builtins.RuntimeError", "Exception message: actual Paddle failure",
        "Traceback (most recent call last)", "paddle_source_location",
        "RuntimeError: actual Paddle failure", "direct cause", "OCRInitializationError:",
    ):
        assert field in output
    assert closed == [True]


@pytest.mark.parametrize("fail_stage", [None, "runtime", "ocr"])
def test_direct_diagnostic_checks_cpu_before_same_model_options(monkeypatch, capsys, fail_stage):
    events = []

    class Tensor:
        def __add__(self, other):
            events.append("add")
            if fail_stage == "runtime":
                raise RuntimeError("CPU native failure")
            return self

        def numpy(self):
            return SimpleNamespace(tolist=lambda: [[2.0, 4.0], [6.0, 8.0]])

    def to_tensor(data, dtype):
        assert data == [[1.0, 2.0], [3.0, 4.0]] and dtype == "float32"
        events.append("tensor")
        return Tensor()

    def direct_ocr(**kwargs):
        assert kwargs == paddle_options()
        events.append("ocr")
        if fail_stage == "ocr":
            raise RuntimeError("PaddleX native failure")

    monkeypatch.setitem(sys.modules, "paddle", SimpleNamespace(
        __version__="test", device=SimpleNamespace(get_device=lambda: "cpu"),
        set_device=lambda device: events.append(device), to_tensor=to_tensor,
    ))
    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=direct_ocr))
    # The direct diagnostic must not call the Translation Lens adapter.
    monkeypatch.setattr(PaddleOCRProvider, "_load", lambda _: pytest.fail("wrapper called"))
    assert paddle_diagnostic.main() == (1 if fail_stage else 0)
    output = capsys.readouterr().out
    assert events == ["cpu", "tensor", "add"] + ([] if fail_stage == "runtime" else ["ocr"])
    if fail_stage:
        assert "=== ORIGINAL EXCEPTION ===" in output and "RuntimeError:" in output
        assert "test_paddle_diagnostic.py" in output
    else:
        assert "Paddle CPU runtime: PASS" in output
        assert "Direct PaddleOCR initialization: PASS" in output
