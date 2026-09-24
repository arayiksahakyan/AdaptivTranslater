# Translation Lens

Windows-first desktop translation-lens prototype (repository: AdaptivTranslater).
Local capture → visual change detection → OCR → normalization → translation cache
→ Local Argos, mock, or optional Google Cloud translation → overlay. Screenshots remain local;
translation providers receive recognized text only.

Status: **IMPLEMENTED**, with **142 automated tests passing on Linux**, offscreen Qt
launch/shutdown checked, and real local PaddleOCR smoke-tested on generated text.
Native Windows behavior is **REQUIRES WINDOWS VERIFICATION**. This is an MVP
candidate, not a verified Windows release. See [PROGRESS.md](PROGRESS.md).

## Run on Windows

Use 64-bit Python 3.12 in the repository root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ocr.txt
.venv\Scripts\python.exe -m pip install -r requirements-translation.txt
.venv\Scripts\python.exe -m tools.install_translation_model en ru
$env:PADDLE_PDX_CACHE_HOME = Join-Path $PWD '.paddle-cache'
$env:PADDLE_PDX_MODEL_SOURCE = 'bos'
.venv\Scripts\python.exe -m tools.ocr_smoke
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = 'True'
.venv\Scripts\python.exe -m app.main --provider argos-local --ocr-language en --source en --target ru
```

Place the lens over text, drag its title strip, and resize its edges/corners.
Choose source/target in the control panel and select **Start Translation**.
Ctrl+Shift+T starts/pauses; Ctrl+Shift+L toggles Edit/Click-through. Esc cancels a
drag/resize or returns to Edit while the app has focus. The control panel remains
available if a global shortcut conflicts with another application.

The default is **Local (Offline)**, English → Russian. The explicit setup above
downloads translation and OCR models; subsequent local translation requires no
Internet, API key, account, billing, or backend. Argos never downloads during app
startup or translation. Missing dependencies/models produce an actionable status;
the GUI stays usable and you can select Mock. No automatic provider fallback occurs.
After installing a model in another terminal, restart the app.

| Provider | Output | Network and cost |
| --- | --- | --- |
| `mock` | Labeled repeated text, no real translation | Offline, free |
| `argos-local` | Real local Argos Translate; default | Free, offline after explicit setup |
| `google-cloud-basic` | Real Google Cloud Translation Basic | Optional; sends text, requires key/billing |

Local requires an explicit source language; Auto remains available for Google/Mock.
OCR model selection is separate (`--ocr-language en`, `ru`, etc.). Missing OCR is
an error, with no simulated OCR fallback. Google support remains available unchanged.

Argos **1.11.0** and MiniSBD **0.9.5** are pinned in `requirements-translation.txt`.
English → Russian currently downloads about **196 MB (187 MiB)**, plus a **188 KB**
English sentence model. Python dependencies and Paddle models are additional.
See [development](DEVELOPMENT.md#local-argos-translate-setup) for model paths,
intermediate-language translation, dependency research, and optional real smoke tests.
Real Argos inference and its integration with PaddleOCR on Windows remain
**REQUIRES WINDOWS VERIFICATION**; automated Argos tests use doubles, not large models.

## Capture and privacy

The capture region is inside the border and below the title strip, including the
area behind the output panel. Capture defaults to 350 ms without a queued backlog;
OCR and translation run only after relevant changes. Windows uses native capture
exclusion. If it fails or captures black/recursive pixels, relaunch with
`--capture-mode hide` and follow the Windows pixel checks. Hide mode can flicker.

Select `Google Cloud Translation` in the control panel, or start directly with
`--provider google-cloud-basic`. The cache includes provider, source, target, and
normalized text, so changing providers cannot reuse a result from another provider.

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
