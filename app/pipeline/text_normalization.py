import re
import unicodedata


def normalize_text(text: str) -> str:
    """Conservative normalization: retain case, punctuation, and meaningful joiners.

    NFC avoids changing compatibility symbols. Remove BOM/NUL and unsafe control
    characters; preserve ZWJ/ZWNJ (meaningful in scripts/emoji). Do not guess glyphs,
    dehyphenate, strip accents, or deduplicate repeated lines.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n").replace("\ufeff", "")
    text = "".join(c for c in text if c in "\n\t" or unicodedata.category(c) != "Cc")
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
