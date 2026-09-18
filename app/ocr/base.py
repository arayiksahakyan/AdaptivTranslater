from dataclasses import dataclass
from typing import Protocol

from app.capture.base import RGBImage

Point = tuple[float, float]


@dataclass(frozen=True)
class OCRResult:
    text: str
    confidence: float
    bbox: tuple[Point, ...]


class OCRProvider(Protocol):
    def recognize(self, image: RGBImage) -> list[OCRResult]: ...

    def close(self) -> None: ...
