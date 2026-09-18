"""Explicitly save ONE physical-region screenshot for manual Windows diagnostics.

This tool saves screen pixels only when the user supplies --output. Run it against
non-sensitive test content. It does not hide/exclude another process's windows.
The running Translation Lens process must already have applied capture exclusion.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

from app.capture.base import CaptureRegion
from app.capture.screen_capture import MSSCaptureProvider
from app.errors import LensError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=int, required=True)
    parser.add_argument("--top", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Explicit PNG destination")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new filename.")
    if sys.platform == "win32":
        from app.platform.windows import configure_dpi_awareness

        configure_dpi_awareness()
    provider = MSSCaptureProvider()
    try:
        region = CaptureRegion(args.left, args.top, args.width, args.height)
        image = provider.capture(region)
        with args.output.open("xb") as destination:
            Image.fromarray(image).save(destination, format="PNG")
        print(f"Saved requested {region.width} x {region.height} region to {args.output}")
    except (LensError, ValueError, OSError) as exc:
        parser.exit(1, f"Capture probe failed: {exc}\n")
    finally:
        provider.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
