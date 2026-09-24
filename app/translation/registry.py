"""Construct lightweight providers; optional engines load on the worker later."""

from app.translation.argos_local import ArgosLocalTranslationProvider
from app.translation.base import TranslationProvider
from app.translation.google_cloud import GoogleCloudTranslationProvider
from app.translation.mock_translator import MockTranslationProvider

PROVIDER_LABELS = {
    "argos-local": "Local (Offline)",
    "mock": "Mock (offline)",
    "google-cloud-basic": "Google Cloud Translation",
}


def create_providers() -> dict[str, TranslationProvider]:
    return {
        "mock": MockTranslationProvider(),
        "google-cloud-basic": GoogleCloudTranslationProvider(),
        "argos-local": ArgosLocalTranslationProvider(),
    }
