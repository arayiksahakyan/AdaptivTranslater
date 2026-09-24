"""Lazy, worker-owned Argos translation with strictly local inference.

The pinned Argos/MiniSBD adapter checks every leg of a pivot before inference.
Only tools.install_translation_model may download packages or auxiliary models.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import Any, Protocol

from app.errors import TranslationError
from app.translation.provider import validate_languages


class LocalTranslator(Protocol):
    def translate(self, text: str) -> str: ...


def load_argos() -> Any:
    """Configure before importing translate: SpaCy can download at import time.

    Override environment/user settings in this process only. A local provider
    must never become an Argos remote provider, even with inherited settings.
    """
    if version("argostranslate") != "1.11.0" or version("minisbd") != "0.9.5":
        raise TranslationError("Install the pinned versions in requirements-translation.txt.")
    os.environ.update(
        ARGOS_MODEL_PROVIDER="OPENNMT", ARGOS_CHUNK_TYPE="MINISBD",
        ARGOS_DEVICE_TYPE="cpu", ARGOS_DEBUG="0", ORT_DISABLE_TELEMETRY="1",
    )
    import onnxruntime

    onnxruntime.disable_telemetry_events()
    # Argos 1.11 also logs input/output at INFO even when ARGOS_DEBUG=0.
    # Disable its payload logger before imports; never attach it to app logging.
    logging.getLogger("argostranslate.utils").disabled = True
    from argostranslate import settings

    settings.model_provider = settings.ModelProvider.OPENNMT
    settings.chunk_type = settings.ChunkType.MINISBD
    settings.device = "cpu"
    settings.debug = False  # Argos debug output includes input and output text.
    from argostranslate import translate

    return translate


def require_local_models(translation: Any, argos: Any) -> None:
    """Bind MiniSBD to an absolute file, never a downloadable language/URL.

    This small version-specific traversal covers direct and composite Argos
    translations. An unknown translation type fails closed.
    """
    if isinstance(translation, argos.CachedTranslation):
        require_local_models(translation.underlying, argos)
    elif isinstance(translation, argos.CompositeTranslation):
        require_local_models(translation.t1, argos)
        require_local_models(translation.t2, argos)
    elif isinstance(translation, argos.PackageTranslation):
        from argostranslate import sbd

        splitter = translation.sentencizer
        if not isinstance(splitter, sbd.MiniSBDSentencizer):
            raise TranslationError("Local model configuration changed. Restart Translation Lens.")
        # MiniSBD's catalog is bundled in its Python package, with no index call.
        from minisbd import models

        candidate = Path(splitter.lang)
        if not candidate.is_absolute():
            filename = models.MODELS.get(splitter.lang)
            candidate = Path(models.cache_dir) / filename if filename else candidate
        if not candidate.is_absolute() or not candidate.is_file():
            pkg = translation.pkg
            raise TranslationError(
                "Local sentence model is missing. Run: python -m tools.install_translation_model "
                f"{pkg.from_code} {pkg.to_code}; then restart the app. Or select Mock."
            )
        # get_model_file(absolute_path) only opens a file; deletion yields an
        # error rather than a download. This also closes the preflight/use race.
        splitter.lang = str(candidate.resolve())
    elif not isinstance(translation, argos.IdentityTranslation):
        raise TranslationError("Unsupported local model type. Reinstall translation dependencies.")


def resolve_translator(source: str, target: str) -> LocalTranslator:
    argos = load_argos()
    languages = {language.code: language for language in argos.get_installed_languages()}
    translation = None
    if source in languages and target in languages:
        translation = languages[source].get_translation(languages[target])
    if translation is None:
        raise TranslationError(
            f"No installed local translation path for {source} → {target}. "
            f"Run: python -m tools.install_translation_model {source} {target}; "
            "then restart the app. Or select Mock."
        )
    require_local_models(translation, argos)
    return translation


class ArgosLocalTranslationProvider:
    provider_id = "argos-local"

    def __init__(
        self, resolver: Callable[[str, str], LocalTranslator] = resolve_translator,
    ) -> None:
        # No optional imports, model loads, or downloads at construction/startup.
        # Set before the pipeline's OCR stage can import optional ONNX dependencies.
        os.environ["ORT_DISABLE_TELEMETRY"] = "1"
        self._resolver = resolver
        self._translators: dict[tuple[str, str], LocalTranslator] = {}

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        validate_languages(source_language, target_language)
        if source_language == "auto":
            raise TranslationError(
                "Local translation needs an explicit source language; select English."
            )
        if not text.strip():
            return ""
        if source_language == target_language:
            return text
        pair = (source_language, target_language)
        try:
            translator = self._translators.get(pair)
            if translator is None:
                translator = self._resolver(*pair)
                self._translators[pair] = translator
            result = translator.translate(text)
            if not isinstance(result, str) or not result.strip():
                raise TranslationError("Local translation returned an empty or invalid result.")
            return result
        except TranslationError:
            raise
        except ImportError:
            raise TranslationError(
                "Local translation dependencies are missing. Run: "
                "python -m pip install -r requirements-translation.txt. Or select Mock."
            ) from None
        except Exception:
            # Native dependency/model errors may include recognized text. Never
            # expose arbitrary exceptions or silently fall back to a cloud API.
            self._translators.pop(pair, None)
            raise TranslationError(
                "Local translation failed. Check installed models/dependencies, restart the app, "
                "or select Mock. See DEVELOPMENT.md."
            ) from None
