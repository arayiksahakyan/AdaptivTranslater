# Current Status

Current phase: Phase 1 — MVP candidate implemented; Linux validation complete;
current Windows OCR initialization fails; diagnostic output pending;
offline Argos acceptance pending. Earlier Windows mock evidence is historical.

## REAL WINDOWS OBSERVATION — 2026-09-25 (user report)

- Windows 11, Python **3.12.3**.
- `PP-OCRv5_mobile_det` exists in local cache at
  `.paddle-cache/official_models/PP-OCRv5_mobile_det`.
- Paddle finds the cached model and reports
  `Creating model: ('PP-OCRv5_mobile_det', None)` and cached-file reuse.
- Initialization raises **RuntimeError**; the original Paddle/PaddleX traceback
  was hidden by our `_load()` wrapper's `raise OCRError(...) from None`.
- **Root cause is not yet known. Windows OCR is not currently working.**
- `No ccache found` is a warning, not an established cause. No Paddle/PaddleOCR/
  PaddleX/NumPy dependency versions were changed or speculative fixes applied.
- **REQUIRES WINDOWS VERIFICATION:** run the new direct diagnostic and smoke tool
  below and collect their full output before determining the actual fix.

Working:

- IMPLEMENTED: lens, controls, bounded mss capture, Win32 adapter, real PaddleOCR
  adapter, image/text detection, mock translation, LRU cache, asynchronous pipeline.
- TESTED ON LINUX: 154 automated core/offscreen Qt tests pass. Ruff, compilation,
  and dependency consistency pass; full app launches and shuts down offscreen.
- TESTED ON LINUX: real English PaddleOCR recognizes generated sample text;
  cached models also run with network access restricted (223 ms warm sample).
- Revision cancellation, capture hide/restore, provider errors/retries, and worker
  cleanup are covered by automated tests with injected dependencies.
- Historical TESTED ON WINDOWS (user-provided evidence, 2026-09-20; superseded for
  current OCR status by the failing 2026-09-25 report): the real application
  captured a screen region, PaddleOCR recognized English text, MockTranslationProvider
  produced `[MOCK en → ru]`, and the translated result rendered in the overlay.
  Sample recognized text was `HELLO WORLD` / `THIS IS A TEST`.
- IMPLEMENTED: Google Cloud Translation Basic adapter, provider selector, API-key
  environment configuration, provider-aware cache keys, and mocked network tests.
- IMPLEMENTED: free `argos-local` provider, default Local / English → Russian,
  lazy worker-owned translators, installed direct/pivot model checks, explicit
  translation/sentence-model installer, optional real smoke, and local privacy note.
- IMPLEMENTED: offline model-path guards and Argos payload-log suppression; no
  silent model downloads, automatic cloud fallback, or provider changes on errors.
- IMPLEMENTED: ONNX Runtime telemetry opt-out before processing and API disable
  before translation sessions; covered by configuration regression assertions.
- TESTED ON LINUX: all 109 previous tests plus 33 Argos/tool/UI/worker tests pass.
  Argos tests use doubles and download no models. Local startup/shutdown works with
  optional dependencies absent; missing dependencies produce an actionable error.

Not working:

- Current Windows 11 / Python 3.12.3 OCR initialization fails despite a cached
  detector. The original error output is needed; no root cause or fix is claimed.
- Real Argos inference and PaddleOCR + Argos integration have not been executed in
  this Linux task or verified on Windows. No translation models were downloaded.
- Full native Windows desktop acceptance remains incomplete.
- Real Google translation is IMPLEMENTED, preserved, optional, and unverified on Windows.
- Automatic OCR language/model detection, settings persistence, and packaging are
  NOT IMPLEMENTED. Source Auto is only a translation hint.

Requires Windows verification:

- All native GUI/capture/DPI/input behaviors. No Windows environment is available.
- DPI/multiple-monitor mapping, capture contamination/exclusion, click-through,
  global hotkeys, sustained operation, and real local/network providers remain open.
- Actual underlying pixels with exclusion/hide mode, mixed-DPI geometry, negative
  monitor origins, focus/click-through, shortcut conflicts, and sustained operation.

# Last Completed Task

2026-09-25: **IMPLEMENTED** original exception chaining for OCR import/load/inference,
environment and full traceback reporting in `tools.ocr_smoke`, and
`tools.paddle_diagnostic` (tiny CPU tensor addition, then direct PaddleOCR construction).
Both paths share exactly the existing English mobile model options and inherit the
same cache environment. No UI, capture, Argos, translation-provider, or dependency
files changed. Normal application errors/logging remain concise and sanitized.

**IMPLEMENTED** initialization failure latch in the pipeline. Further scheduled
jobs skip capture and initialization until region/language/provider changes.
Move/resize the lens to explicitly retry; a failed retry is latched again. The
controller increments revisions on errors, so revision changes alone (including
pause/resume) deliberately do not reset this latch. Existing UI error suffix may
still say `Retrying`; these timer jobs return the saved error without reloading OCR.
No UI redesign or UI source changes were made. Genuine inference errors retain
their existing retry behavior. Original exception objects are not stored in the
latch, avoiding retention of screenshot frames through tracebacks.

**TESTED ON LINUX:** 154 tests, Ruff, compilation; real direct CPU/model diagnostic
and real English generated-text OCR smoke pass using existing cached weights.
**REQUIRES WINDOWS VERIFICATION:** diagnostics and explicit retry on the affected
Windows machine. Changes are diagnostic; they do not resolve the unknown native error.

2026-09-24: Added Argos Translate 1.11.0 with MiniSBD 0.9.5 as the preferred free,
offline real provider. Retained Google and Mock, made model installation explicit,
reused translators/cache on the worker, and handled missing models without blocking
GUI use. Updated README, DEVELOPMENT, ARCHITECTURE, DECISIONS (ADR-008), ROADMAP,
and this file. Added dependency/validation evidence in
`docs/validation/2026-09-24-argos.md`.

Official dependency/source investigation found auxiliary auto-downloads and INFO
logs containing text in Argos; local-path guards and payload-logger suppression
address these. Windows x64 Python 3.12 and Linux combined binary-wheel metadata
resolution succeeded with the existing Paddle pins. No unrelated dependency was
downgraded and the existing venv runtime packages were unchanged. No Windows,
Google API, real Argos model, commit, or push action was performed in this task.

2026-09-20: Added Google Cloud Translation Basic as the first real provider and
updated provider selection, cache keys, and documentation. Network tests are mocked;
no paid API request was made. The user's Windows report was recorded with only its
demonstrated checkboxes marked.

2026-09-19: Created project memory before code, then implemented the local MVP in
small component steps. Added tests and diagnostics, installed a Python 3.12.8 venv,
ran real CPU OCR, and documented results. Fixed model-language selection, removed
private mss cache manipulation, covered error recovery to previous text, and added
safe final worker cleanup.

At the user's request, organized the MVP on `main` into logical commits:

- `de7e0e7`: project foundations, architecture, and dependencies.
- `1aafab7`: capture, OCR, translation/cache, core pipeline, and tests.
- `fac5630`: desktop UI, worker, Windows integration, diagnostics, and tests.
- A final documentation handoff commit records setup, validation, and this status.

At that historical MVP handoff, the commits were local and no push had been
requested. The 2026-09-25 diagnostic task explicitly requests commit and push to
`origin/main` so Windows can pull the new tools.

# Current Task

Run the diagnostics below on the affected Windows machine. Compare the CPU runtime,
direct PaddleOCR initialization, and wrapped OCR smoke results, including original
source locations. Determine the actual failure before proposing dependency changes.
Argos/native acceptance remains pending and is outside this diagnostic change.

PowerShell, from the repository root after pulling this change (no installs):

```powershell
git pull --ff-only origin main
$env:PADDLE_PDX_CACHE_HOME = Join-Path $PWD '.paddle-cache'
$env:PADDLE_PDX_MODEL_SOURCE = 'bos'
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = 'True'
.venv\Scripts\python.exe -m tools.paddle_diagnostic 2>&1 | Tee-Object -FilePath paddle-diagnostic.log
.venv\Scripts\python.exe -m tools.ocr_smoke 2>&1 | Tee-Object -FilePath ocr-smoke.log
```

Keep both full logs, including warnings, environment, original exception, and chained
tracebacks. These explicit diagnostics print detailed native exceptions and local
paths; they process no private screen content. A missing English recognizer may
still download through Paddle's usual behavior; no unrelated models are selected.

# Next Tasks

0. Obtain full Windows diagnostic output above; root cause remains unknown.
1. Set up a Windows 10/11 x64 Python 3.12 venv using `DEVELOPMENT.md`.
2. Install `requirements-translation.txt`, run
   `python -m tools.install_translation_model en ru`, cache Paddle models, disable
   its host probe, and run the optional real `tools.translation_smoke` offline.
3. Execute `docs/WINDOWS_TESTING.md`; record build, monitor/scaling, versions, and
   exact results, starting with uncontaminated capture and coordinate boundaries.
4. Verify real PaddleOCR → Argos → overlay, no network activity, responsive first
   load, model/cache reuse, switching/pause/recovery, and sustained desktop performance.
5. Test Google only if/when billing and a key are available; it remains optional.

# Known Problems

- No Windows test host; native acceptance cannot be completed here.
- The Windows pipeline result above is user-reported; it was not executed by this
  Linux session and does not prove DPI, input, or capture-exclusion behavior.
- Capture exclusion success alone cannot establish uncontaminated underlying pixels.
  Use `--capture-mode hide` if needed; the fallback may flicker and its 80 ms
  settling delay needs actual compositor validation.
- Native OCR/model-loading calls cannot be interrupted safely. UI shutdown waits
  for the current call; a permanently hung library would require process isolation.
- Real OCR was tested only on generated English text, not games or live screens.
  Non-English models and all live Windows/X11 capture remain unverified.
- Model downloads need network on first use. This checkout's tested weights are
  in ignored `.paddle-cache`; configure `PADDLE_PDX_CACHE_HOME` to reuse them.
- Google Cloud Translation requires a user-supplied API key, enabled API, billing,
  and quota configuration. No key is stored in the repository. Use Local for free
  real translation; Google billing is not required for this MVP path.
- Argos dependencies/models are optional and were not installed in this session.
  Metadata resolution is not proof of native DLL/ABI coexistence with PaddleOCR.
- Local requires explicit Source; Auto is unsupported. Directional packages and
  all pivot legs must be installed explicitly. Restart after model changes.
- English → Russian model HEAD size: 195746693 bytes; auxiliary English MiniSBD:
  188043 bytes. Python dependencies, unpacked models, and Paddle weights are extra.
- Linux preview supports only X11 at 100% scale; offscreen tests are not proof of
  a Linux desktop product. No cloud/paid translation/account infrastructure exists.

# Last Test Results

2026-09-25 commands (executed on Linux, Python 3.12.8):

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall -q app tests tools
PADDLE_PDX_CACHE_HOME="$PWD/.paddle-cache" PADDLE_PDX_MODEL_SOURCE=bos PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True .venv/bin/python -m tools.paddle_diagnostic
PADDLE_PDX_CACHE_HOME="$PWD/.paddle-cache" PADDLE_PDX_MODEL_SOURCE=bos PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True .venv/bin/python -m tools.ocr_smoke
git diff --check
```

Result: **154 passed in 0.55s**, Ruff **All checks passed**, compilation exit 0,
`git diff --check` PASS.
Two initial Ruff line-length violations were corrected. Tests cover original import,
initialization and inference causes; full diagnostic tracebacks; CPU-before-OCR order;
shared model configuration; repeated failure/retry; controller-driven error revisions;
and explicit lens resize recovery without changes to the UI source.

Direct diagnostic: exit **0**, CPU addition `[[2.0, 4.0], [6.0, 8.0]]`, both cached
English mobile models initialized. Smoke: exit **0**, both generated English text
runs passed (`Hello world 123`; 1572 ms first run, 192 ms warm run).
`No ccache found` was emitted during successful Linux diagnostics;
this does not explain the Windows failure. No models/dependencies were installed.
Linux results are not Windows verification.

## Earlier Argos verification (historical)

2026-09-24 commands (executed):

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall -q app tests tools
.venv/bin/python -m pip check
git diff --check
```

Result: **142 passed in 0.64s** (final recheck), Ruff **All checks passed**, compilation exit 0,
pip **No broken requirements found** for the existing venv, diff check PASS.
The pip cache-directory warning is non-fatal; no runtime packages were installed.
Initial Ruff line-length errors were fixed before the final successful run.

Command: `.venv/bin/python -m app.main --provider argos-local`, launched by a
subprocess with `QT_QPA_PLATFORM=offscreen`, then terminated via SIGTERM after two
seconds. Result: startup with Local selected, worker cleanup, exit **0**, even
without Argos installed. No capture/translation was started. Qt size-hint notices
were non-fatal; this is only Linux startup/shutdown evidence.

Command: `.venv/bin/python -m tools.translation_smoke`. Result: expected exit **1**
with the missing-dependency installation/Mock guidance. This is **not** a successful
real translation smoke. Real model/inference acceptance remains unexecuted.

Dependency resolution: combined core/OCR/translation requirements succeeded using
temporary uv for Windows x64 Python 3.12 and Linux, binary wheels only. The initial
pip dry-run was cancelled when it started downloading large runtime wheels; no
installation occurred. Exact commands, versions, model-size probes, and limitations:
`docs/validation/2026-09-24-argos.md`.

## Earlier MVP verification (historical)

Command: `.venv/bin/python -m pytest -q`

Result: **94 passed in 0.40s** on Linux with offscreen Qt, rechecked before the
requested commits. Ruff and compilation were also rechecked successfully. The
earlier validation record retains its original run timing.

Commands: `.venv/bin/python -m ruff check .`,
`.venv/bin/python -m compileall -q app tests tools`,
`.venv/bin/python -m pip check`, `git diff --check`.

Result: PASS. Full offscreen app launch → SIGTERM → worker cleanup: exit 0.

Command: `PADDLE_PDX_CACHE_HOME="$PWD/.paddle-cache" PADDLE_PDX_MODEL_SOURCE=bos
PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True .venv/bin/python -m tools.ocr_smoke`
(execute on one line).

Result: real `Hello world 123` recognized in both runs, one detection each;
initialization plus inference 2172 ms, warm inference 223 ms on a 700×180 generated
image. The cached run succeeded inside the network-restricted sandbox. First
download attempts hit sandbox DNS restrictions; authorized official-host downloads
completed. The `No ccache found` warning and offscreen size-hint notice were non-fatal.

Details and installed versions: `docs/validation/2026-09-19-linux.md`.
**TESTED ON WINDOWS (user report):** capture → English PaddleOCR → mock translation
→ overlay rendering. **Not tested/verified:** Google provider, DPI, multi-monitor,
click-through, global hotkeys, contamination/exclusion, and sustained operation.
