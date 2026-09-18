# Current Status

Current phase: Phase 1 — MVP candidate implemented; Linux validation complete;
Windows acceptance pending. No Windows release is verified.

Working:

- IMPLEMENTED: lens, controls, bounded mss capture, Win32 adapter, real PaddleOCR
  adapter, image/text detection, mock translation, LRU cache, asynchronous pipeline.
- TESTED ON LINUX: 94 automated core/offscreen Qt tests pass. Ruff, compilation,
  and dependency consistency pass; full app launches and shuts down offscreen.
- TESTED ON LINUX: real English PaddleOCR recognizes generated sample text;
  cached models also run with network access restricted (223 ms warm sample).
- Revision cancellation, capture hide/restore, provider errors/retries, and worker
  cleanup are covered by automated tests with injected dependencies.

Not working:

- Real linguistic translation is NOT IMPLEMENTED; mock output is explicitly labeled.
- Live Windows behavior and full desktop acceptance have not been tested.
- Automatic OCR language/model detection, settings persistence, and packaging are
  NOT IMPLEMENTED. Source Auto is only a translation hint.

Requires Windows verification:

- All native GUI/capture/DPI/input behaviors. No Windows environment is available.
- Actual underlying pixels with exclusion/hide mode, mixed-DPI geometry, negative
  monitor origins, focus/click-through, shortcut conflicts, and sustained operation.

# Last Completed Task

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

Implementation and available Linux verification are complete. The next execution
task is the Windows acceptance procedure in `docs/WINDOWS_TESTING.md` on actual
Windows hardware. Its checkboxes intentionally remain unchecked.

# Next Tasks

1. Set up a Windows 10/11 x64 Python 3.12 venv using `DEVELOPMENT.md`.
2. Execute `docs/WINDOWS_TESTING.md`; record build, monitor/scaling, versions, and
   exact results, starting with uncontaminated capture and coordinate boundaries.
3. Resolve observed Windows issues, then measure sustained real desktop performance.
4. Validate additional OCR languages/fonts; choose a real translation provider only
   in a later scoped task. Preserve the local/no-paid-API baseline.

# Known Problems

- No Windows test host; native acceptance cannot be completed here.
- Capture exclusion success alone cannot establish uncontaminated underlying pixels.
  Use `--capture-mode hide` if needed; the fallback may flicker and its 80 ms
  settling delay needs actual compositor validation.
- Native OCR/model-loading calls cannot be interrupted safely. UI shutdown waits
  for the current call; a permanently hung library would require process isolation.
- Real OCR was tested only on generated English text, not games or live screens.
  Non-English models and all live Windows/X11 capture remain unverified.
- Model downloads need network on first use. This checkout's tested weights are
  in ignored `.paddle-cache`; configure `PADDLE_PDX_CACHE_HOME` to reuse them.
- Linux preview supports only X11 at 100% scale; offscreen tests are not proof of
  a Linux desktop product. No cloud/paid translation/account infrastructure exists.

# Last Test Results

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
**TESTED ON WINDOWS: none.** All Windows manual checks remain pending.
