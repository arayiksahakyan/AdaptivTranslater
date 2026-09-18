"""Pure coordinate math shared by the Win32 adapter and deterministic tests."""

from math import ceil, floor

from app.capture.base import CaptureRegion


def map_client_region(
    origin: tuple[int, int],
    native_size: tuple[int, int],
    logical_size: tuple[int, int],
    local_rect: tuple[int, int, int, int],
) -> CaptureRegion:
    """Scale local edges only; the native desktop origin is already physical.

    Round inward to avoid including the lens border. Native client size reflects
    the window's current DPI even when the desktop contains negative origins.
    """
    nw, nh = native_size
    lw, lh = logical_size
    x, y, w, h = local_rect
    if min(nw, nh, lw, lh, w, h) <= 0 or min(x, y) < 0 or x + w > lw or y + h > lh:
        raise ValueError("Invalid client rectangle.")
    left, top = ceil(x * nw / lw), ceil(y * nh / lh)
    right, bottom = floor((x + w) * nw / lw), floor((y + h) * nh / lh)
    return CaptureRegion(origin[0] + left, origin[1] + top, right - left, bottom - top)
