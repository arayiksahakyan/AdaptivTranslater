from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

RGBImage = NDArray[np.uint8]


@dataclass(frozen=True)
class CaptureRegion:
    """Signed physical desktop coordinates, not Qt logical coordinates."""

    left: int
    top: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Capture region must have positive dimensions.")

    def as_mss(self) -> dict[str, int]:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


class CaptureProvider(Protocol):
    def capture(self, region: CaptureRegion) -> RGBImage:
        """Return an owned H x W x 3 uint8 RGB array; raise CaptureError on failure."""
        ...

    def close(self) -> None: ...
