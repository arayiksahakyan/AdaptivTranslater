import pytest

from app.config import AppConfig
from app.main import main


@pytest.mark.parametrize(
    "kwargs",
    [
        {"capture_interval_ms": 10},
        {"hide_settle_ms": 0},
        {"cache_size": 0},
        {"min_ocr_confidence": -1},
        {"capture_mode": "bad"},
        {"ocr_language": ""},
    ],
)
def test_invalid_settings(kwargs):
    with pytest.raises(ValueError):
        AppConfig(**kwargs)


def test_invalid_cli_language_and_interval_return_without_gui():
    assert main(["--target", "auto"]) == 2
    assert main(["--interval-ms", "1"]) == 2
