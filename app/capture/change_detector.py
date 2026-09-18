import numpy as np
from numpy.typing import NDArray
from PIL import Image

from app.capture.base import RGBImage


class ImageChangeDetector:
    """Compare to the last *accepted* frame, including gradual accumulated drift.

    Local-change fraction catches a changed word in an otherwise static region.
    Thresholds trade OCR sensitivity for tolerance of antialiasing/cursor noise.
    """

    def __init__(
        self,
        mean_threshold: float = 2.0,
        pixel_threshold: float = 20.0,
        changed_fraction: float = 0.003,
        sample_size: tuple[int, int] = (320, 180),
    ) -> None:
        if not 0 < mean_threshold <= 255 or not 0 < pixel_threshold <= 255:
            raise ValueError("Pixel thresholds must be in (0, 255].")
        if not 0 < changed_fraction <= 1 or min(sample_size) <= 0:
            raise ValueError("Invalid change fraction or sample size.")
        self.mean_threshold = mean_threshold
        self.pixel_threshold = pixel_threshold
        self.changed_fraction = changed_fraction
        self.sample_size = sample_size
        self._baseline: NDArray[np.float32] | None = None
        self._shape: tuple[int, ...] | None = None

    def _sample(self, image: RGBImage) -> NDArray[np.float32]:
        if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Expected H x W x 3 uint8 RGB image.")
        if min(image.shape[:2]) <= 0:
            raise ValueError("Image cannot be empty.")
        sample = Image.fromarray(image).convert("L")
        sample.thumbnail(self.sample_size, Image.Resampling.BOX)
        return np.asarray(sample, dtype=np.float32)

    def has_changed(self, image: RGBImage) -> bool:
        sample = self._sample(image)
        if self._baseline is None or self._shape != image.shape:
            return True
        delta = np.abs(sample - self._baseline)
        return bool(
            delta.mean() >= self.mean_threshold
            or np.mean(delta >= self.pixel_threshold) >= self.changed_fraction
        )

    def commit(self, image: RGBImage) -> None:
        self._baseline = self._sample(image)
        self._shape = image.shape

    def reset(self) -> None:
        self._baseline = None
        self._shape = None
