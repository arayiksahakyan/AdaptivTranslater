"""Developer-only Paddle CPU and direct PaddleOCR initialization diagnostics.

Run: python -m tools.paddle_diagnostic
Uses the app's English model pair and inherited cache/model-source environment.
Missing weights may download, just as in the app; no unrelated models are selected.
"""

import importlib.metadata
import importlib.util
import os
import platform
import struct
import sys
import traceback
from pathlib import Path

from app.ocr.paddle_config import paddle_options


def print_environment() -> None:
    """Report metadata without importing the native OCR stack or exposing all env vars."""
    print("=== ENVIRONMENT ===", flush=True)
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Windows version: {platform.win32_ver()}")
    print(f"Architecture: {platform.machine()} / {struct.calcsize('P') * 8}-bit Python")
    for name in (
        "paddlepaddle", "paddleocr", "paddlex", "numpy", "opencv-python",
        "opencv-contrib-python", "opencv-python-headless", "opencv-contrib-python-headless",
    ):
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "not installed"
        print(f"{name}: {version}")
    cv2 = importlib.util.find_spec("cv2")
    print(f"cv2 module: {cv2.origin if cv2 else 'not installed'} (not imported)")
    for name in (
        "PADDLE_PDX_CACHE_HOME", "PADDLE_PDX_MODEL_SOURCE",
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK",
    ):
        print(f"{name}={os.environ.get(name, '<unset>')}")
    # Mirrors PaddleX utils/cache.py without importing it before the runtime test.
    cache = Path(os.environ.get("PADDLE_PDX_CACHE_HOME", str(Path.home() / ".paddlex")))
    print(f"Working directory: {Path.cwd()}")
    print(f"Model cache: {cache.absolute()} (exists={cache.is_dir()})")
    options = paddle_options()
    print(f"PaddleOCR options: {options}")
    for key in ("text_detection_model_name", "text_recognition_model_name"):
        path = cache / "official_models" / options[key]
        print(f"{key}: {path.absolute()} (exists={path.is_dir()})")
    print(
        "Cache presence alone does not establish model completeness or compatibility.", flush=True
    )


def print_exception(exc: BaseException) -> None:
    """Explicit diagnostic output only; ordinary app logs must remain sanitized."""
    original = exc
    seen: set[int] = set()
    while id(original) not in seen:
        seen.add(id(original))
        cause = original.__cause__
        if cause is None and not original.__suppress_context__:
            cause = original.__context__
        if cause is None:
            break
        original = cause
    print("=== ORIGINAL EXCEPTION ===")
    print(f"Exception class: {type(original).__module__}.{type(original).__qualname__}")
    print(f"Exception message: {original}")
    print("=== FULL TRACEBACK (including exception chain) ===", flush=True)
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stdout, chain=True)
    sys.stdout.flush()


def main() -> int:
    print_environment()
    print("=== PADDLE CPU RUNTIME ===", flush=True)
    try:
        import paddle

        print(f"paddle.__version__: {paddle.__version__}")
        print(f"paddle.device.get_device(): {paddle.device.get_device()}")
        paddle.set_device("cpu")
        print(f"CPU test device: {paddle.device.get_device()}", flush=True)
        tensor = paddle.to_tensor([[1.0, 2.0], [3.0, 4.0]], dtype="float32")
        actual = (tensor + tensor).numpy().tolist()
        print(f"CPU tensor addition: {actual}", flush=True)
        if actual != [[2.0, 4.0], [6.0, 8.0]]:
            raise RuntimeError(f"Unexpected CPU addition result: {actual}")
    except Exception as exc:
        print_exception(exc)
        print("Paddle CPU runtime: FAIL; direct PaddleOCR initialization skipped.", flush=True)
        return 1
    print("Paddle CPU runtime: PASS", flush=True)
    print("=== DIRECT PADDLEOCR INITIALIZATION ===", flush=True)
    try:
        from paddleocr import PaddleOCR

        # No Translation Lens provider, capture, GUI, or translation code is involved.
        PaddleOCR(**paddle_options())
    except Exception as exc:
        print_exception(exc)
        print("Direct PaddleOCR initialization: FAIL", flush=True)
        return 1
    print("Direct PaddleOCR initialization: PASS (inference not tested here)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
