# Current Status

Current phase: Phase 1 — MVP candidate implemented; Linux validation complete;
partial Windows mock pipeline verification complete; offline Argos acceptance pending.

Working:

- IMPLEMENTED: lens, controls, bounded mss capture, Win32 adapter, real PaddleOCR
  adapter, image/text detection, mock translation, LRU cache, asynchronous pipeline.
- TESTED ON LINUX: 142 automated core/offscreen Qt tests pass. Ruff, compilation,
  and dependency consistency pass; full app launches and shuts down offscreen.
- TESTED ON LINUX: real English PaddleOCR recognizes generated sample text;
  cached models also run with network access restricted (223 ms warm sample).
- Revision cancellation, capture hide/restore, provider errors/retries, and worker
  cleanup are covered by automated tests with injected dependencies.
- TESTED ON WINDOWS (user-provided evidence, 2026-09-20): the real application
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

The commits are local; no push was requested or performed. Push `main` to `origin`
before pulling these changes from the GitHub remote on a Windows machine.

# Current Task

Argos implementation and available Linux verification are complete. Next: execute
the Windows local-provider setup/offline smoke in `DEVELOPMENT.md`, then the native
acceptance procedure in `docs/WINDOWS_TESTING.md`. Only earlier user-reported
capture/OCR/mock-overlay checks are marked; Argos and native acceptance remain open.

# Next Tasks

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
