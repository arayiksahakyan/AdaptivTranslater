import numpy as np
import pytest

from app.capture.base import CaptureRegion
from app.capture.screen_capture import MSSCaptureProvider
from app.errors import CaptureError
from app.platform.geometry import map_client_region


@pytest.mark.parametrize("scale", [1, 1.25, 1.5, 2])
def test_local_scaling_preserves_negative_desktop_origin(scale):
    result = map_client_region(
        (-1920, -300), (int(800 * scale), int(400 * scale)), (800, 400), (8, 40, 784, 352)
    )
    assert result == CaptureRegion(
        -1920 + int(8 * scale), -300 + int(40 * scale), int(784 * scale), int(352 * scale)
    )


def test_fractional_edges_round_inward():
    result = map_client_region((0, 0), (125, 125), (100, 100), (1, 1, 98, 98))
    assert result == CaptureRegion(2, 2, 121, 121)


def test_invalid_rectangles_rejected():
    with pytest.raises(ValueError):
        map_client_region((0, 0), (100, 100), (100, 100), (-1, 0, 20, 20))
    with pytest.raises(ValueError):
        CaptureRegion(0, 0, 0, 100)


class Session:
    monitors = [{"left": -100, "top": -50, "width": 500, "height": 400}]

    def __init__(self):
        self.closed = False
        self.requests = []
        self.pixels = np.array([[[10, 20, 30, 255]]], dtype=np.uint8)

    def grab(self, region):
        self.requests.append(region)
        return self.pixels

    def close(self):
        self.closed = True


def test_mss_uses_region_and_owns_rgb_memory():
    provider = MSSCaptureProvider()
    provider._session = session = Session()
    region = CaptureRegion(-90, -30, 1, 1)
    image = provider.capture(region)
    assert session.requests == [region.as_mss()]
    assert image.tolist() == [[[30, 20, 10]]]
    session.pixels[:] = 0
    assert image.tolist() == [[[30, 20, 10]]]
    provider.close()
    assert session.closed


def test_outside_desktop_is_reported_without_whole_screen_capture():
    provider = MSSCaptureProvider()
    provider._session = session = Session()
    with pytest.raises(CaptureError, match="beyond"):
        provider.capture(CaptureRegion(-101, 0, 20, 20))
    assert session.requests == [] and session.closed


def test_capture_sanitizes_backend_failure():
    class FailedSession(Session):
        def grab(self, region):
            raise RuntimeError("private backend details")

    provider = MSSCaptureProvider()
    provider._session = session = FailedSession()
    with pytest.raises(CaptureError, match="Screen capture failed") as error:
        provider.capture(CaptureRegion(0, 0, 1, 1))
    assert "private" not in str(error.value)
    assert session.closed
