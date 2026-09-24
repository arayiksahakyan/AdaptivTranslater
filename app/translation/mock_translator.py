from app.translation.provider import validate_languages


class MockTranslationProvider:
    """Deliberate offline pipeline demonstrator; never presented as real translation."""

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        validate_languages(source_language, target_language)
        return f"[MOCK {source_language} → {target_language}]\n{text}" if text else ""

    provider_id = "mock"
