"""mss is created and closed on the same worker that calls capture."""

import logging
from time import monotonic
from typing import Any

import numpy as np

from app.capture.base import CaptureRegion, RGBImage
from app.errors import CaptureError

logger = logging.getLogger(__name__)


class MSSCaptureProvider:
    def __init__(self) -> None:
        self._session: Any = None
        self._opened_at = monotonic()

    def capture(self, region: CaptureRegion) -> RGBImage:
        if region.width * region.height > 16_000_000:
            raise CaptureError("Lens is too large. Resize it below 16 million physical pixels.")
        try:
            # mss caches the monitor layout. Reopen periodically using its public
            # API instead of mutating version-specific private monitor fields.
            if self._session is not None and monotonic() - self._opened_at > 5:
                self.close()
            if self._session is None:
                import mss

                self._session = mss.mss()
                self._opened_at = monotonic()
            desktop = self._session.monitors[0]
            if (
                region.left < desktop["left"]
                or region.top < desktop["top"]
                or region.left + region.width > desktop["left"] + desktop["width"]
                or region.top + region.height > desktop["top"] + desktop["height"]
            ):
                raise CaptureError("Lens extends beyond the desktop. Move it fully onto a monitor.")
            shot = self._session.grab(region.as_mss())
            # MSS is BGRA; OCR contract is RGB. Own the bytes beyond the next grab.
            return np.asarray(shot, dtype=np.uint8)[:, :, 2::-1].copy()
        except CaptureError:
            self.close()  # Refresh a changed display layout on the next attempt.
            raise
        except Exception as exc:
            logger.warning("Screen capture failed (%s)", type(exc).__name__)
            self.close()
            raise CaptureError(
                "Screen capture failed. Check desktop access and lens position; "
                "Linux preview needs X11."
            ) from None

    def close(self) -> None:
        if self._session is not None:
            try:
                self._session.close()
            except Exception as exc:
                logger.warning("Capture cleanup failed (%s)", type(exc).__name__)
            finally:
                self._session = None
