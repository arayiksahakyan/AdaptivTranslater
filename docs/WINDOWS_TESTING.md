# Windows acceptance procedure

**REQUIRES WINDOWS VERIFICATION** — no Windows execution yet. Leave every checkbox
unchecked until that exact test has run on Windows. Linux/offscreen checks do not
satisfy this procedure. Use non-sensitive sample text; do not save private screens.

## Preparation

Follow the Windows setup in `../DEVELOPMENT.md`. Record Windows build (`winver`),
Python/dependency versions (`python -m pip freeze`), GPU, desktop session type,
monitor arrangement, and scale per monitor. Use a regular windowed desktop app
(Notepad/browser) with large text: `Settings`, `Account`, `Security`, `Hello 123!`.
Position it under the lens. The default translation is explicitly mock output.

## Lens and controls

- [ ] Run `.venv\Scripts\python.exe -m app.main --ocr-language en`.
  Both windows appear; no traceback; status identifies mock translation.
- [ ] See content through the center; border and output remain legible.
- [ ] Focus Notepad: lens stays above it. Test ordinary and maximized windows.
- [ ] Drag the lens title strip to several positions; content stays aligned.
- [ ] Resize every edge/corner, including rapid reversals; minimum size holds.
- [ ] During a drag/resize press Esc; the edit cancels. Esc in click-through
  returns to Edit when the app has focus. Esc is not a global keyboard hook.
- [ ] Choose source/target; start, pause, resume; status and buttons agree.
- [ ] Test long output and smaller lens: text wraps and remains bounded.

## Coordinates and capture exclusion

- [ ] At 100% scale put distinctive text immediately inside/outside each capture
  edge (inside border, below title). Only inside text reaches OCR.
- [ ] Repeat at 125%, 150%, and 200%; restart after changing display settings.
- [ ] Place a second monitor to the left and above the primary (negative origins),
  repeat each edge test; capture must not shift toward the primary monitor.
- [ ] Use different scale factors on two monitors, move the lens across them,
  and span the boundary. Check text at both ends and update behavior while moving.
- [ ] Put a unique string under the output panel and a different string in the
  lens result; OCR must see the underlying string, never its own rendered output.
- [ ] Move the control panel into the capture area; its labels must not enter OCR.
  The pixels underneath the panel must still be available (a black box is a fail).
- [ ] Repeat with `--capture-mode hide`. App windows may flicker, but must return
  after successful capture, screenshot error, pause, and close.
- [ ] Verify exclusion actually reveals underlying content on the tested build.
  If auto/affinity captures black/stale pixels, record FAIL and use hide mode;
  do not mark the default exclusion path passed just because the API succeeded.
- [ ] Move partly off the virtual desktop and disconnect/reconnect a monitor.
  The app reports an actionable capture error or returns to valid capture without
  crashing; off-desktop requests must not silently capture the entire desktop.

For direct pixel inspection of the **auto/exclusion** path, start the app with
`--debug`, start capture, and copy the `left`, `top`, `width`, and `height` from
its `Physical capture region` log entry. Keep the lens still and pause translation.
In a second PowerShell window replace these example numbers with the logged ones:

```powershell
.venv\Scripts\python.exe -m tools.capture_probe --left 100 --top 140 --width 704 --height 314 --output capture-probe-auto.png
```

Open the PNG and compare boundary text and content behind the lens output/control
panel with the original application. Negative `--left`/`--top` are valid. The tool
uses the same mss provider with physical pixels; it does not hide another process's
windows. It therefore cannot test hide-mode timing. Use the hide-mode OCR checks
above for that path. The file is an explicitly requested screenshot, ignored by
Git when named `capture-probe*.png`; keep it non-sensitive and remove it after review.
No file is written by normal application capture. This probe has not run on Windows.

## OCR, cache, errors, and privacy

- [ ] Allow initial model download, then read the sample text through real OCR.
  The output is labeled `MOCK`; it proves routing, not linguistic translation.
- [ ] Run `.venv\Scripts\python.exe -m tools.ocr_smoke` separately. Both generated
  sample runs report `passed: true`; record timings and model initialization errors.
- [ ] Hold content still: debug timings show no repeated OCR on identical images.
- [ ] Change visual decoration without changing text: no new translation call.
- [ ] Show A, then B, then A; the last result reports a cache hit.
- [ ] Change target language on an unchanged screen: new target appears.
- [ ] Blank the region: previous output clears. Small/low-confidence text is
  filtered, not converted into a persistent previous translation.
- [ ] Move/change languages rapidly during slow OCR: old results never overwrite
  the new revision. Pause during OCR: no late output is rendered.
- [ ] In a core-only venv without Paddle, start: show a useful provider error and
  remain responsive. Install OCR requirements and relaunch to recover.
- [ ] Test invalid OCR model language (`--ocr-language invalid-code`): show a
  recoverable failure, not fabricated text or a GUI crash.
- [ ] Inspect ordinary/debug logs: no screenshots, recognized text, or provider
  payloads. Text appears only if explicitly enabled with `--log-text`.

## Input, hotkeys, lifecycle, and performance

- [ ] In Click-through, click/type/scroll in Notepad through the full lens;
  the lens does not steal focus. The separate panel remains interactive.
- [ ] With another app focused, Ctrl+Shift+L returns to Edit and back.
- [ ] With another app focused, Ctrl+Shift+T pauses/resumes exactly once per press.
- [ ] Start a second instance to create hotkey conflicts: useful status and
  working panel; no silent claim that registration succeeded.
- [ ] Close via panel/window manager while idle, hiding, OCR loading, and inference.
  No stuck invisible windows, `QThread destroyed` warning, or registered hotkeys.
- [ ] Run at least 10 minutes with static/changing text and repeated moves.
  Record OCR/capture latency, visible responsiveness, memory, and CPU. Jobs do not
  accumulate; capture default is 350 ms, expensive stages run only as needed.
- [ ] Test borderless-windowed game separately if relevant. Record protected or
  exclusive-fullscreen capture limitations; these modes are not an MVP guarantee.

## Result record

```text
Date / tester:
Commit or working-tree snapshot:
Windows build / Python / dependencies:
GPU / monitor positions / scale factors:
Capture mode / OCR model language:
Test ID or checkbox:
Expected:
Observed:
PASS / FAIL / BLOCKED:
Evidence (non-sensitive only):
```
