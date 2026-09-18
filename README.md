# Translation Lens

Windows-first desktop translation-lens prototype (repository: AdaptivTranslater).
Local capture → visual change detection → OCR → normalization → translation cache
→ labeled mock translation → overlay. Real linguistic translation is a future provider.

Status: **IMPLEMENTED**, with **94 automated tests passing on Linux**, offscreen Qt
launch/shutdown checked, and real local PaddleOCR smoke-tested on generated text.
Native Windows behavior is **REQUIRES WINDOWS VERIFICATION**. This is an MVP
candidate, not a verified Windows release. See [PROGRESS.md](PROGRESS.md).

## Run on Windows

Use 64-bit Python 3.12 in the repository root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ocr.txt
.venv\Scripts\python.exe -m app.main --ocr-language en
```

Place the lens over text, drag its title strip, and resize its edges/corners.
Choose source/target in the control panel and select **Start Translation**.
Ctrl+Shift+T starts/pauses; Ctrl+Shift+L toggles Edit/Click-through. Esc cancels a
drag/resize or returns to Edit while the app has focus. The control panel remains
available if a global shortcut conflicts with another application.

The result starts with `[MOCK source → target]` and repeats recognized text.
**No real linguistic translation or paid API is included.** Source Auto is a
translation hint; OCR model selection is separate (`--ocr-language en`, `ru`, etc.).
Initial model loading may download weights. If OCR is missing, the app reports an
error; there is no simulated OCR fallback.

## Capture and privacy

The capture region is inside the border and below the title strip, including the
area behind the output panel. Capture defaults to 350 ms without a queued backlog;
OCR and translation run only after relevant changes. Windows uses native capture
exclusion. If it fails or captures black/recursive pixels, relaunch with
`--capture-mode hide` and follow the Windows pixel checks. Hide mode can flicker.

Images and translation cache remain in memory; screenshots and OCR history are
not saved by the app. Debug logging omits text unless `--log-text` is explicitly
supplied. The separate capture probe saves a screenshot only with `--output`.

## Development and project memory

Linux can run core/offscreen tests and a limited X11/100%-scale preview. The product
target remains Windows 10/11. Full capture/compositor verification needs Windows.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
```

- [Product](docs/PRODUCT.md)
- [Architecture](ARCHITECTURE.md) and [decisions](DECISIONS.md)
- [Development setup](DEVELOPMENT.md) and [testing](TESTING.md)
- [Windows acceptance procedure](docs/WINDOWS_TESTING.md)
- [Recorded Linux validation](docs/validation/2026-09-19-linux.md)
- [Roadmap](ROADMAP.md)
- [Future commercial planning](docs/COMMERCIAL_ARCHITECTURE.md)
- [Agent instructions](AGENTS.md)
