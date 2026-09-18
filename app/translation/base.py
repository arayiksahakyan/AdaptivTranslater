from typing import Protocol


class TranslationProvider(Protocol):
    """Future network providers must enforce request timeouts and sanitize errors."""

    def translate(self, text: str, source_language: str, target_language: str) -> str: ...
