"""Google Cloud Translation Basic REST provider.

Only normalized OCR text is placed in the JSON request. Credentials are read from
``GOOGLE_TRANSLATE_API_KEY`` and are never included in application logs or errors.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.errors import TranslationError
from app.translation.provider import validate_languages

logger = logging.getLogger(__name__)


class GoogleCloudTranslationProvider:
    provider_id = "google-cloud-basic"
    endpoint = "https://translation.googleapis.com/language/translate/v2"

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float = 15.0,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Translation timeout must be positive.")
        self._api_key = api_key if api_key is not None else os.getenv("GOOGLE_TRANSLATE_API_KEY")
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        validate_languages(source_language, target_language)
        if not text.strip():
            return ""
        if not self._api_key:
            raise TranslationError(
                "Google translation is not configured. Set GOOGLE_TRANSLATE_API_KEY."
            )
        payload = {"q": text, "target": target_language, "format": "text"}
        if source_language != "auto":
            payload["source"] = source_language
        url = f"{self.endpoint}?{urlencode({'key': self._api_key})}"
        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except TimeoutError:
            raise TranslationError("Google translation timed out. Retry or use Mock.") from None
        except HTTPError as exc:
            logger.warning("Google translation HTTP failure (status=%s)", exc.code)
            raise TranslationError(
                f"Google translation was rejected (HTTP {exc.code}). Check API access."
            ) from None
        except URLError:
            logger.warning("Google translation network failure")
            raise TranslationError(
                "Google translation is unavailable. Check network access."
            ) from None
        except OSError:
            logger.warning("Google translation transport failure")
            raise TranslationError("Google translation transport failed. Retry later.") from None

        try:
            document = json.loads(raw.decode("utf-8"))
            translated = document["data"]["translations"][0]["translatedText"]
            if not isinstance(translated, str) or not translated.strip():
                raise ValueError("empty translation")
        except (
            UnicodeDecodeError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            logger.warning("Google translation returned an invalid response")
            raise TranslationError("Google translation returned an invalid response.") from None
        return translated
