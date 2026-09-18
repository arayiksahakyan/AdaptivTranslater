import pytest

from app.pipeline.text_normalization import normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Hello\t world!  ", "Hello world!"),
        (" first\r\n second \rthird ", "first\nsecond\nthird"),
        ("A\n\n\n\nB", "A\n\nB"),
        ("\ufeffPrice:\x00 12.50 € — OK?!", "Price: 12.50 € — OK?!"),
        ("e\u0301\u00a0café", "é café"),
        ("設定\u2028安全", "設定\n安全"),
        ("Repeat\nRepeat", "Repeat\nRepeat"),
        ("hyphen-\nated", "hyphen-\nated"),
        ("👩\u200d💻 می\u200cروم", "👩\u200d💻 می\u200cروم"),
        ("  \r\n\t ", ""),
    ],
)
def test_normalization(raw, expected):
    assert normalize_text(raw) == expected
    assert normalize_text(expected) == expected
