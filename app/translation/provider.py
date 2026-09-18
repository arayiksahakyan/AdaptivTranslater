"""Small public language catalog; providers can extend this when added."""

from app.errors import TranslationError

LANGUAGES = (
    ("en", "English"),
    ("ru", "Russian"),
    ("de", "German"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("uk", "Ukrainian"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("zh", "Chinese"),
    ("ar", "Arabic"),
    ("hy", "Armenian"),
)
LANGUAGE_CODES = frozenset(code for code, _ in LANGUAGES)


def validate_languages(source_language: str, target_language: str) -> None:
    if source_language not in LANGUAGE_CODES | {"auto"} or target_language not in LANGUAGE_CODES:
        raise TranslationError(
            "Unsupported translation language. Select a listed source and target."
        )
