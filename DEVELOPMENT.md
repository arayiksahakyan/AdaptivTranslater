# Development

Target: Windows 10/11. Development host: Linux. Use Python 3.12 (64-bit) for the
initial dependency combination; the core targets Python 3.11+. Install into a venv.
Linux setup and automated checks were executed; recorded versions/results are in
`docs/validation/2026-09-19-linux.md`. Windows instructions are an unexecuted
procedure: native Windows behavior is **REQUIRES WINDOWS VERIFICATION**.

## Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install -r requirements-ocr.txt
.venv/bin/python -m app.main --help
.venv/bin/python -m app.main
```

Linux GUI is a development preview limited to X11 and 100% scale. Its capture
implementation uses real mss with hide/restore, but live X11 capture was not tested.
Native Windows hotkeys/click-through/exclusion are unavailable. Wayland capture is not
supported by this preview. Pure tests and offscreen Qt tests require no desktop.

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
.venv\Scripts\python.exe -m app.main --ocr-language en
```

There is no activation-policy requirement when using the interpreter directly.
Paddle is an optional install to keep core development light, but is required for
actual OCR: the application must report a missing provider, never substitute fake OCR.
First model initialization can download model weights and be slow. Review model
download/network requirements before an offline session.

## Checks

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall -q app tests tools
.venv/bin/python -m pip check
```

On Windows substitute `.venv\Scripts\python.exe`. Follow `docs/WINDOWS_TESTING.md`
for physical capture and interaction checks that automated tests cannot establish.

## Models, diagnostics, and offline use

The English default selects `PP-OCRv5_mobile_det` + `en_PP-OCRv5_mobile_rec`.
Other `--ocr-language` values use Paddle's language resolution and may load larger
models. `en`, `ru`, `japan`, `korean`, and `ch` are OCR language examples; these are
Paddle identifiers, not necessarily the translation provider's language codes.
Only English inference has been tested here. Invalid model languages produce a
provider error. Automatic script/model detection is not implemented.

Paddle defaults to a per-user `.paddlex` model cache. To keep weights in this
checkout (ignored by Git), before launching or running diagnostics:

```bash
export PADDLE_PDX_CACHE_HOME="$PWD/.paddle-cache"
export PADDLE_PDX_MODEL_SOURCE=bos
.venv/bin/python -m tools.ocr_smoke
```

PowerShell equivalent:

```powershell
$env:PADDLE_PDX_CACHE_HOME = Join-Path $PWD '.paddle-cache'
$env:PADDLE_PDX_MODEL_SOURCE = 'bos'
.venv\Scripts\python.exe -m tools.ocr_smoke
```

The smoke tool generates harmless text in memory and runs real OCR twice. It
prints recognized sample text and initialization/warm timings; it never captures
the desktop. `bos` is Paddle's official model host, used here when fetching weights.
Without this setting Paddle chooses its default model host.

After the needed models are downloaded, set
`PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` (PowerShell:
`$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = 'True'`) to skip the initial host
connectivity probe. The Linux smoke passed with cached models and network access
restricted. This flag does not download missing models or disable TLS checks.

`python -m tools.capture_probe --help` describes a one-shot region capture that
saves pixels only with an explicit `--output`. See the Windows pixel procedure.

Useful application flags: `--capture-mode hide`, `--interval-ms 500`,
`--hide-settle-ms 150`, `--confidence 0.7`, `--image-threshold 2`,
`--changed-fraction 0.003`, `--source auto`, `--target ru`, `--debug`.
Use `python -m app.main --help` for the complete list. Settings are not persisted.

## Troubleshooting

- Missing OCR dependency/model: install the OCR requirements; check first-run
  network access. The control panel shows provider errors; pause before retrying.
- Wrong script recognition: source selection affects translation; choose the real
  OCR model language with `--ocr-language`. Auto does not auto-select OCR models.
- Black or recursive capture on Windows: retry with `--capture-mode hide`, then
  perform contamination tests. Hiding can flicker; record failures rather than
  asserting that a successful exclusion call proves correct pixels.
- Wrong coordinates: remove manual `QT_SCALE_FACTOR` overrides, check per-monitor
  DPI mode, and follow the mixed-DPI procedure. Do not multiply global origins.
- Linux plugin/display error: use `QT_QPA_PLATFORM=offscreen` for tests or an X11
  display for interactive preview. This is not evidence about Windows behavior.
- A `No ccache found` Paddle warning was observed during successful CPU inference;
  it does not require changing the application. Offscreen Qt's
  `propagateSizeHints` notice also occurred during a successful launch/shutdown.
- A missing Windows native DLL may require the current Microsoft Visual C++ runtime;
  follow the provider's official installation guidance and record the exact error.
- Hotkey conflict: close the conflicting application or use the control panel.
- Slow/hung OCR: initialization is expensive; shutdown cooperatively waits for an
  active native call. Do not terminate QThreads or destroy running workers.
- Debug logs omit text by default; explicit text logging may expose private data.
