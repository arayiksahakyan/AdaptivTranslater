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
.venv/bin/python -m pip install -r requirements-translation.txt
.venv/bin/python -m tools.install_translation_model en ru
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
.venv\Scripts\python.exe -m pip install -r requirements-translation.txt
.venv\Scripts\python.exe -m tools.install_translation_model en ru
.venv\Scripts\python.exe -m app.main --provider argos-local --ocr-language en --source en --target ru
```

There is no activation-policy requirement when using the interpreter directly.
Paddle is an optional install to keep core development light, but is required for
actual OCR: the application must report a missing provider, never substitute fake OCR.
First model initialization can download model weights and be slow. Review model
download/network requirements before an offline session.

## Local Argos Translate setup

`argos-local` is the preferred real development provider and the application default
(source `en`, target `ru`). Select **Local (Offline)** in the panel. Capture, OCR,
recognized text, and translation all remain on the computer. Google is optional.
Missing translation dependencies/models do not prevent launch: Start shows an
actionable error, Pause stops retries, and Mock remains selectable. Mock only labels
the original text. Install a missing model explicitly and restart the app; the
worker retains loaded translators and Argos caches its installed-language graph.
The adapter suppresses Argos's INFO-level text logger and opts out of ONNX Runtime
telemetry using its pre-initialization environment setting and runtime API. Native
network/telemetry behavior still needs the Windows checks below.

The optional runtime requirements pin `argostranslate==1.11.0` (current official
release checked 2026-09-24) and `minisbd==0.9.5`. Keep the existing Python 3.12 x64
environment and PaddleOCR 3.3.2 / PaddlePaddle 3.2.2 pins. No unrelated package was
downgraded. Install all requirements in one command if checking an existing environment:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ocr.txt -r requirements-translation.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m tools.install_translation_model en ru
```

The installer explicitly updates the official index, selects the newest compatible
direct package, downloads/installs it if absent, and prepares its source-language
MiniSBD sentence model. It checks the local translation path before reporting
completion. Existing direct packages are reused; rerunning can complete a missing
auxiliary model. Installation errors return exit 1; no background downloader runs.
If an interrupted/corrupt archive remains, remove only that downloaded `.argosmodel`
from the Argos downloads directory and rerun. Do not delete the entire model store.

Argos normally uses `%USERPROFILE%\.local\share\argos-translate\packages` on Windows
and `~/.local/share/argos-translate/packages` on Linux. `ARGOS_PACKAGES_DIR` overrides
the package directory; `XDG_DATA_HOME` changes the Argos data root. MiniSBD models go
in the Argos data root's `minisbd` directory. Downloaded archives are retained under
`~/.local/cache/argos-translate/downloads` unless `XDG_CACHE_HOME` is set. Use the same
account/environment for installation and launch. These contain models, not OCR history.
Keep custom model directories outside Git (or under ignored `.models/`).

English → Russian index entry `translate-en_ru`, package version 1.9, currently points
to an archive of **195,746,693 bytes** (~196 MB / 187 MiB). MiniSBD's English model is
**188,043 bytes** (~188 KB). Sizes were checked with HTTP HEAD on 2026-09-24, without
downloading these models. Disk needs also include the unpacked archive and Python
dependencies; PyTorch/spaCy/ONNX Runtime make runtime installation substantially
larger than the tiny Argos wheel. Budget several GB for the combined OCR/translation
environment. Package/model sizes can change.

Only explicitly installed **directional** models are used. `en → ru` does not supply
`ru → en`. Argos can compose installed paths such as `es → en → ru` when a direct
`es → ru` model is absent. Install each leg explicitly with this tool. Every leg's
source sentence model must also be present. The installer does not automatically
choose/download pivot legs. Pivots can be slower and lose quality; direct models
take priority. The runtime reports an unavailable installed path without consulting
the online catalog, so it cannot distinguish a model never published upstream from
one not yet downloaded. The explicit installer reports unsupported direct pairs.

Argos Auto source detection is not implemented. Choose English for English OCR;
changing Source does not change Paddle's OCR model. Same-source/target returns the
input unchanged without loading translation models.

### Offline preparation and optional real smoke

While connected, install the translation model and run the existing OCR smoke once
to cache both English Paddle models. Then disable Paddle's host connectivity probe:

```powershell
$env:PADDLE_PDX_CACHE_HOME = Join-Path $PWD '.paddle-cache'
$env:PADDLE_PDX_MODEL_SOURCE = 'bos'
.venv\Scripts\python.exe -m tools.ocr_smoke
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = 'True'
```

Disconnect the network and run:

```powershell
.venv\Scripts\python.exe -m tools.translation_smoke
.venv\Scripts\python.exe -m tools.ocr_smoke
.venv\Scripts\python.exe -m app.main --provider argos-local --ocr-language en --source en --target ru
```

The optional translation smoke uses two public sample sentences, checks for Russian
Cyrillic, and prints cold/warm timing. It never downloads anything and is not part of
automated tests. Review semantic quality yourself; Cyrillic alone is not a quality
guarantee. Verify the complete screen → PaddleOCR → Argos → overlay flow, responsiveness
during first load, unchanged-text skipping, provider/language changes, pause, shutdown,
and missing-model recovery via Mock. Check process network activity with the network
enabled too: no requests should originate from local translation. This Linux task did
not execute real Argos model inference; **REQUIRES WINDOWS VERIFICATION** applies to
native dependencies, real inference, and coexistence with Paddle in the same process.

### Dependency investigation

The official Argos 1.11.0 wheel requires CTranslate2 `>=4,<5`, SentencePiece `>=0.2,<0.3`,
Stanza `==1.10.1`, sacremoses `>=0.0.53,<0.2`, spaCy, MiniSBD, and packaging. Stanza pulls
PyTorch; MiniSBD pulls ONNX Runtime. Shared constraints include NumPy, protobuf,
Pydantic, and the existing Paddle stack. Resolving **all three requirements files
together** with binary wheels for Windows x64 Python 3.12 and Linux succeeded; no
declared dependency conflict was found. The metadata resolution retained compatible
NumPy 2.5.3, protobuf 7.36.2, and Pydantic 2.13.5 and selected CTranslate2 4.8.2,
SentencePiece 0.2.2, spaCy 3.8.16, ONNX Runtime 1.30.0, and PyTorch 2.14.0. These are
resolution observations, not extra pins or proof of native DLL/ABI compatibility.

Commands/results are recorded in `docs/validation/2026-09-24-argos.md`. Runtime
dependencies were not installed during this task. A pip dry-run was cancelled when
it began downloading large wheels; a temporary uv resolver completed metadata checks
instead. Existing `.venv` dependencies were preserved. If Windows pip reports a
conflict, retain the full resolver output and inspect the named constraints before
changing versions. Do not randomly downgrade Paddle/NumPy or use `--no-deps`.

Sources: [Argos release](https://pypi.org/project/argostranslate/1.11.0/),
[official implementation](https://github.com/argosopentech/argos-translate/tree/v1.11.0),
[model index](https://github.com/argosopentech/argospm-index/blob/main/index.json),
[MiniSBD](https://github.com/LibreTranslate/MiniSBD).

## Google Cloud Translation setup (optional)

Google Cloud Translation Basic (`google-cloud-basic`) remains an optional real provider.
It was selected because the Basic REST API supports broad language coverage and
accepts plain text, so the desktop sends normalized OCR text rather than screenshots.
The implementation uses Python's standard HTTPS client; no Google SDK is required.

Google requires a Google Cloud project with billing enabled, the Cloud Translation
API enabled, and an API key restricted to that API. Follow Google's current setup
steps: <https://cloud.google.com/translate/docs/setup>. API usage may incur charges;
configure quotas before testing. Do not put the key in source, Git, screenshots, or
logs. The app never logs the request URL or response body.

Set the key only in the current PowerShell session:

```powershell
$env:GOOGLE_TRANSLATE_API_KEY = "paste-key-here"
$env:PADDLE_PDX_CACHE_HOME = Join-Path $PWD ".paddle-cache"
$env:PADDLE_PDX_MODEL_SOURCE = "bos"
.venv\Scripts\python.exe -m app.main --provider google-cloud-basic --ocr-language en --source en --target ru
```

The application remains usable without the key using Local or `Mock (offline)`.
Missing key, HTTP failures, invalid responses, timeout, and network failures show
a recoverable status; they do not terminate the GUI. Stop the process and clear the
session variable when finished:

```powershell
Remove-Item Env:GOOGLE_TRANSLATE_API_KEY
```

The provider timeout defaults to 15 seconds. Requests contain only the normalized
OCR text, source (unless Auto), target, and plain-text format. No image is sent.

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

Useful application flags: `--provider argos-local|mock|google-cloud-basic`,
`--capture-mode hide`, `--interval-ms 500`,
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
