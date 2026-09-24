"""Real inference on generated non-sensitive text; no screen capture or fake OCR.

Run: python -m tools.ocr_smoke [--font /path/to/font.ttf]
First use may download official OCR models into the provider's configured cache.
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

from tools.paddle_diagnostic import print_environment, print_exception


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path)
    parser.add_argument(
        "--repeat", type=int, default=2, help="Include a warm inference measurement"
    )
    args = parser.parse_args()
    if not 1 <= args.repeat <= 10:
        parser.error("--repeat must be between 1 and 10.")
    candidates = (
        [args.font]
        if args.font
        else [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/hack/Hack-Regular.ttf"),
        ]
    )
    font_path = next((p for p in candidates if p is not None and p.exists()), None)
    if font_path is None:
        parser.error("Supply --font with a local TrueType font.")
    print_environment()
    provider = None
    try:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont

        from app.ocr.paddle_ocr import PaddleOCRProvider

        image = Image.new("RGB", (700, 180), "white")
        ImageDraw.Draw(image).text(
            (24, 45), "Hello world 123", fill="black", font=ImageFont.truetype(str(font_path), 48)
        )
        provider = PaddleOCRProvider("en")
        runs = []
        for _ in range(args.repeat):
            started = perf_counter()
            results = provider.recognize(np.asarray(image))
            text = " ".join(r.text for r in results)
            success = all(part in text.casefold() for part in ("hello", "world", "123"))
            runs.append(
                {
                    "recognized": text,
                    "passed": success,
                    "duration_ms": round((perf_counter() - started) * 1000),
                    "detections": len(results),
                }
            )
        print(json.dumps({"runs": runs}, ensure_ascii=False))
        return 0 if all(run["passed"] for run in runs) else 1
    except Exception as exc:
        print_exception(exc)
        return 1
    finally:
        if provider is not None:
            provider.close()


if __name__ == "__main__":
    raise SystemExit(main())
