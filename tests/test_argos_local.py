import logging
import os
import sys
import threading
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QTimer

from app.config import AppConfig
from app.errors import TranslationError
from app.main import parse_args
from app.pipeline.translation_pipeline import TranslationPipeline
from app.pipeline.worker import PipelineRunner
from app.translation import argos_local
from app.translation.argos_local import ArgosLocalTranslationProvider
from app.translation.registry import create_providers


@pytest.fixture
def argos_stub(monkeypatch, tmp_path):
    class Splitter:
        def __init__(self, lang):
            self.lang = lang

    class PackageTranslation:
        def __init__(self, source="en", target="ru"):
            self.pkg = SimpleNamespace(from_code=source, to_code=target)
            self.sentencizer = Splitter(source)

    class CachedTranslation:
        def __init__(self, underlying):
            self.underlying = underlying

    class CompositeTranslation:
        def __init__(self, t1, t2):
            self.t1, self.t2 = t1, t2

    class IdentityTranslation:
        pass

    argos = SimpleNamespace(
        PackageTranslation=PackageTranslation, CachedTranslation=CachedTranslation,
        CompositeTranslation=CompositeTranslation, IdentityTranslation=IdentityTranslation,
        get_installed_languages=Mock(return_value=[]),
    )
    models = SimpleNamespace(cache_dir=str(tmp_path), MODELS={"en": "en.onnx", "ru": "ru.onnx"})
    monkeypatch.setitem(sys.modules, "argostranslate", SimpleNamespace(
        sbd=SimpleNamespace(MiniSBDSentencizer=Splitter),
    ))
    monkeypatch.setitem(sys.modules, "minisbd", SimpleNamespace(models=models))
    monkeypatch.setattr(argos_local, "load_argos", lambda: argos)
    return argos, tmp_path


def test_creation_is_lazy_and_all_providers_remain(monkeypatch):
    monkeypatch.setenv("ORT_DISABLE_TELEMETRY", "0")
    resolver = Mock(side_effect=AssertionError("must stay lazy"))
    provider = ArgosLocalTranslationProvider(resolver)
    assert os.environ["ORT_DISABLE_TELEMETRY"] == "1"
    assert provider.provider_id == "argos-local"
    assert set(create_providers()) == {"mock", "google-cloud-basic", "argos-local"}
    resolver.assert_not_called()
    assert AppConfig().provider == parse_args([]).provider == "argos-local"
    assert parse_args([]).source == "en" and parse_args([]).target == "ru"
    for name in create_providers():
        assert parse_args(["--provider", name]).provider == name
        assert AppConfig(provider=name).provider == name


def test_success_reuses_translator_per_pair():
    translator = Mock(translate=Mock(return_value="Привет"))
    resolver = Mock(return_value=translator)
    provider = ArgosLocalTranslationProvider(resolver)
    assert provider.translate("Hello", "en", "ru") == "Привет"
    assert provider.translate("Different text", "en", "ru") == "Привет"
    resolver.assert_called_once_with("en", "ru")
    provider.translate("Bonjour", "fr", "ru")
    assert resolver.call_count == 2


@pytest.mark.parametrize("source,target", [("auto", "ru"), ("xx", "ru"), ("en", "xx")])
def test_unsupported_language_pair_never_loads_argos(source, target):
    resolver = Mock()
    with pytest.raises(TranslationError):
        ArgosLocalTranslationProvider(resolver).translate("Hello", source, target)
    resolver.assert_not_called()


def test_blank_and_identity_need_no_models():
    resolver = Mock()
    provider = ArgosLocalTranslationProvider(resolver)
    assert provider.translate(" ", "en", "ru") == ""
    assert provider.translate("Hello", "en", "en") == "Hello"
    resolver.assert_not_called()


def test_missing_language_model_has_explicit_install_command(argos_stub):
    with pytest.raises(TranslationError, match="python -m tools.install_translation_model en ru"):
        ArgosLocalTranslationProvider().translate("Hello", "en", "ru")


def test_languages_installed_but_no_directional_path(argos_stub):
    argos, _ = argos_stub
    source = SimpleNamespace(code="en", get_translation=Mock(return_value=None))
    argos.get_installed_languages.return_value = [source, SimpleNamespace(code="ru")]
    with pytest.raises(TranslationError, match="No installed local translation path"):
        argos_local.resolve_translator("en", "ru")


def test_direct_model_and_pivot_require_local_auxiliary_files(argos_stub):
    argos, directory = argos_stub
    (directory / "en.onnx").touch()
    first = argos.PackageTranslation()
    second = argos.PackageTranslation("ru", "de")
    pivot = argos.CompositeTranslation(argos.CachedTranslation(first), second)
    source = SimpleNamespace(code="en", get_translation=Mock(return_value=pivot))
    argos.get_installed_languages.return_value = [source, SimpleNamespace(code="de")]
    with pytest.raises(TranslationError, match="install_translation_model ru de"):
        argos_local.resolve_translator("en", "de")
    (directory / "ru.onnx").touch()
    assert argos_local.resolve_translator("en", "de") is pivot
    assert first.sentencizer.lang == str(directory / "en.onnx")
    assert second.sentencizer.lang == str(directory / "ru.onnx")
    # On deletion an absolute path remains a failing file, never a download code.
    Path(first.sentencizer.lang).unlink()
    with pytest.raises(TranslationError, match="Local sentence model is missing"):
        argos_local.require_local_models(pivot, argos)


def test_unknown_or_remote_model_types_fail_closed(argos_stub):
    argos, _ = argos_stub
    with pytest.raises(TranslationError, match="Unsupported local model type"):
        argos_local.require_local_models(object(), argos)
    translation = argos.PackageTranslation()
    translation.sentencizer.lang = "https://example.invalid/model.onnx"
    with pytest.raises(TranslationError, match="Local sentence model is missing"):
        argos_local.require_local_models(translation, argos)


@pytest.mark.parametrize(
    "failure", [ImportError("private"), OSError("private"), RuntimeError("private")],
)
def test_errors_are_sanitized_and_recoverable(failure):
    resolver = Mock(side_effect=[failure, Mock(translate=Mock(return_value="Привет"))])
    provider = ArgosLocalTranslationProvider(resolver)
    with pytest.raises(TranslationError) as error:
        provider.translate("private text", "en", "ru")
    assert "private" not in str(error.value)
    assert provider.translate("private text", "en", "ru") == "Привет"


@pytest.mark.parametrize("result", [None, "", "  ", 42])
def test_invalid_output_is_rejected(result):
    provider = ArgosLocalTranslationProvider(lambda *_: Mock(translate=lambda text: result))
    with pytest.raises(TranslationError, match="empty or invalid"):
        provider.translate("Hello", "en", "ru")


def test_inference_failure_discards_broken_translator():
    resolver = Mock(side_effect=[
        Mock(translate=Mock(side_effect=RuntimeError("private"))),
        Mock(translate=Mock(return_value="Привет")),
    ])
    provider = ArgosLocalTranslationProvider(resolver)
    with pytest.raises(TranslationError, match="Local translation failed"):
        provider.translate("Hello", "en", "ru")
    assert provider.translate("Hello", "en", "ru") == "Привет"
    assert resolver.call_count == 2


def test_argos_cache_normalization_provider_isolation_and_retry(capture, ocr, job):
    ocr.text = " Hello   world! "
    translator = Mock(translate=Mock(side_effect=[TranslationError("Missing model"), "Привет"]))
    provider = ArgosLocalTranslationProvider(lambda *_: translator)
    providers = create_providers()
    providers[provider.provider_id] = provider
    pipeline = TranslationPipeline(capture, ocr, provider, providers=providers)
    job = replace(job, source_language="en", target_language="ru", provider_name="argos-local")
    assert pipeline.run(job).status == "error"
    assert len(pipeline.cache) == 0
    assert pipeline.run(job).translated_text == "Привет"
    assert pipeline.run(job).status == "unchanged_image"
    capture.image[:] = 255
    assert pipeline.run(job).status == "unchanged_text"
    assert translator.translate.call_count == 2  # one failure, one successful call
    assert pipeline.run(replace(job, revision=2)).cache_hit
    mock = pipeline.run(replace(job, revision=3, provider_name="mock"))
    assert mock.translated_text.startswith("[MOCK") and not mock.cache_hit
    assert pipeline.run(replace(job, revision=4)).cache_hit
    assert pipeline.cache.get(("argos-local", "en", "ru", "Hello world!")) == "Привет"


def test_local_model_loading_and_translation_do_not_block_qt(qtbot, capture, ocr, job):
    entered, gate = threading.Event(), threading.Event()
    threads = []

    def resolve(*_):
        threads.append(threading.get_ident())
        entered.set()
        if not gate.wait(5):
            raise RuntimeError("gate timeout")
        return Mock(translate=translate)

    def translate(text):
        threads.append(threading.get_ident())
        return "Привет"

    provider = ArgosLocalTranslationProvider(resolve)
    runner = PipelineRunner(lambda: TranslationPipeline(capture, ocr, provider))
    job = replace(job, source_language="en", target_language="ru", provider_name="argos-local")
    results = []
    runner.result.connect(results.append)
    try:
        assert runner.submit(job)
        qtbot.waitUntil(entered.is_set)
        ticks = []
        QTimer.singleShot(0, lambda: ticks.append(True))
        qtbot.waitUntil(lambda: bool(ticks))
        assert not runner.submit(job) and not results
        gate.set()
        qtbot.waitUntil(lambda: bool(results))
        assert results[0].translated_text == "Привет"
        assert len(threads) == 2 and len(set(threads)) == 1
        assert threads[0] != threading.get_ident()
    finally:
        gate.set()
        runner.shutdown()
        qtbot.waitUntil(lambda: not runner.running)


def test_load_argos_forces_offline_configuration(monkeypatch, caplog):
    payload_logger = logging.getLogger("argostranslate.utils")
    monkeypatch.setattr(payload_logger, "disabled", False)
    settings = SimpleNamespace(
        ModelProvider=SimpleNamespace(OPENNMT="local"),
        ChunkType=SimpleNamespace(MINISBD="minisbd"),
    )
    translate = object()
    ort = SimpleNamespace(disable_telemetry_events=Mock())
    monkeypatch.setitem(sys.modules, "onnxruntime", ort)
    monkeypatch.setitem(sys.modules, "argostranslate", SimpleNamespace(
        settings=settings, translate=translate,
    ))
    monkeypatch.setattr(argos_local, "version", lambda name: {
        "argostranslate": "1.11.0", "minisbd": "0.9.5",
    }[name])
    for name, value in {"ARGOS_MODEL_PROVIDER": "OPENAI", "ARGOS_CHUNK_TYPE": "SPACY",
                        "ARGOS_DEVICE_TYPE": "cuda", "ARGOS_DEBUG": "1",
                        "ORT_DISABLE_TELEMETRY": "0"}.items():
        monkeypatch.setenv(name, value)
    assert argos_local.load_argos() is translate
    assert settings.model_provider == "local" and settings.chunk_type == "minisbd"
    assert settings.device == "cpu" and settings.debug is False
    assert os.environ["ORT_DISABLE_TELEMETRY"] == "1"
    ort.disable_telemetry_events.assert_called_once()
    with caplog.at_level(logging.INFO):
        payload_logger.info("private OCR payload")
    assert payload_logger.disabled and "private OCR payload" not in caplog.text


def test_unreviewed_argos_version_is_rejected(monkeypatch):
    monkeypatch.setattr(argos_local, "version", lambda _: "99.0")
    with pytest.raises(TranslationError, match="pinned versions"):
        argos_local.load_argos()
