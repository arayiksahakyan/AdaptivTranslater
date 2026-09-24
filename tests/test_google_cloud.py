import json
from urllib.error import HTTPError, URLError

import pytest

from app.errors import TranslationError
from app.translation.google_cloud import GoogleCloudTranslationProvider


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_successful_response_parsing_and_text_only_request():
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return Response({"data": {"translations": [{"translatedText": "ПРИВЕТ"}]}})

    provider = GoogleCloudTranslationProvider("secret-api-key", 4.5, opener)
    assert provider.translate("HELLO WORLD", "en", "ru") == "ПРИВЕТ"
    request, timeout = requests[0]
    assert timeout == 4.5
    assert json.loads(request.data) == {
        "q": "HELLO WORLD",
        "source": "en",
        "target": "ru",
        "format": "text",
    }
    assert "secret-api-key" in request.full_url
    assert b"screen" not in request.data.lower()


def test_auto_source_omits_source_field():
    requests = []

    def opener(request, timeout):
        requests.append(request)
        return Response({"data": {"translations": [{"translatedText": "text"}]}})

    GoogleCloudTranslationProvider("key", opener=opener).translate("text", "auto", "ru")
    assert "source" not in json.loads(requests[0].data)


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError(),
        TimeoutError(),
        URLError("offline"),
        HTTPError("https://example.invalid", 403, "forbidden", {}, None),
    ],
)
def test_transport_failures_are_sanitized(failure):
    def opener(request, timeout):
        raise failure

    with pytest.raises(TranslationError) as error:
        GoogleCloudTranslationProvider("secret", opener=opener).translate("hello", "en", "ru")
    assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"data": {}},
        {"data": {"translations": []}},
        {"data": {"translations": [{"translatedText": ""}]}},
        {"data": {"translations": [{"translatedText": 123}]}},
    ],
)
def test_invalid_response_is_rejected(payload):
    with pytest.raises(TranslationError, match="invalid response"):
        GoogleCloudTranslationProvider(
            "key", opener=lambda *args, **kwargs: Response(payload)
        ).translate("hello", "en", "ru")


def test_missing_key_and_invalid_timeout():
    with pytest.raises(TranslationError, match="GOOGLE_TRANSLATE_API_KEY"):
        GoogleCloudTranslationProvider(api_key="").translate("hello", "en", "ru")
    with pytest.raises(ValueError):
        GoogleCloudTranslationProvider("key", timeout_seconds=0)


def test_supported_language_mapping_and_validation():
    assert (
        GoogleCloudTranslationProvider(
            "key",
            opener=lambda *a, **k: Response({"data": {"translations": [{"translatedText": "ok"}]}}),
        ).translate("hello", "en", "ru")
        == "ok"
    )
    with pytest.raises(TranslationError):
        GoogleCloudTranslationProvider("key").translate("hello", "xx", "ru")
