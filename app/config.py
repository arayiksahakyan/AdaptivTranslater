"""Validated, immutable settings; persistence is deliberately outside the MVP."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AppConfig:
    capture_interval_ms: int = 350
    capture_mode: Literal["auto", "hide"] = "auto"
    hide_settle_ms: int = 80
    image_mean_threshold: float = 2.0
    image_pixel_threshold: float = 20.0
    image_changed_fraction: float = 0.003
    min_ocr_confidence: float = 0.60
    cache_size: int = 256
    ocr_language: str = "en"
    source_language: str = "auto"
    target_language: str = "en"
    log_text: bool = False

    def __post_init__(self) -> None:
        if not 200 <= self.capture_interval_ms <= 5000:
            raise ValueError("Capture interval must be between 200 and 5000 ms.")
        if self.capture_mode not in ("auto", "hide"):
            raise ValueError("Capture mode must be auto or hide.")
        if not 20 <= self.hide_settle_ms <= 1000:
            raise ValueError("Hide settling time must be between 20 and 1000 ms.")
        if not 0 < self.image_mean_threshold <= 255:
            raise ValueError("Image mean threshold must be in (0, 255].")
        if not 0 < self.image_pixel_threshold <= 255:
            raise ValueError("Image pixel threshold must be in (0, 255].")
        if not 0 < self.image_changed_fraction <= 1:
            raise ValueError("Changed fraction must be in (0, 1].")
        if not 0 <= self.min_ocr_confidence <= 1:
            raise ValueError("OCR confidence must be in [0, 1].")
        if self.cache_size < 1:
            raise ValueError("Cache capacity must be positive.")
        if not self.ocr_language.strip():
            raise ValueError("OCR model language must not be empty.")
