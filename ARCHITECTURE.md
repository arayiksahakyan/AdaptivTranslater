# Architecture

## Components and flow

```text
Qt UI thread                              Single Qt worker thread
Lens + controls
  | physical capture region + revision ------> CaptureProvider (mss)
  | <---- capture complete (restore windows)     |
  |                                         ImageChangeDetector
  |                                             | changed
  |                                         OCRProvider (PaddleOCR)
  |                                             |
  |                                         normalize + text comparison
  |                                             | changed
  |                                         TranslationCache
  |                                             | miss
  |                                         TranslationProvider (mock)
  | <--------- result + revision ----------------|
  | validate current revision, then render
```

`app/capture` handles physical rectangles, RGB arrays, and visual comparison.
`app/ocr` returns text/confidence/polygon records, independent of Qt.
`app/translation` owns provider contracts and bounded LRU cache.
`app/pipeline` owns normalized-text deduplication, timings, worker lifecycle, and
revision checks. `app/platform` isolates Win32 DPI, geometry, exclusion, click-through,
and global hotkeys. `app/ui` owns widgets and GUI-thread coordination; the core
processing modules do not depend on Qt.

## Threading and state

Only the UI thread touches widgets or native UI handles. A QObject moved to a QThread
creates and uses the screenshot/OCR resources on that worker. Capture, OCR, and
translation are serial: at most one job, no frame backlog. Signals carry immutable
job metadata/results. Geometry/language/pause changes invalidate a revision token;
late results are discarded and detector/text state resets on the next revision.
Shutdown stops scheduling, requests cooperative cancellation between stages, closes
resources in their owning thread, and exits when the worker finishes. Native OCR
calls cannot be forcibly cancelled safely; shutdown may await the current call.
A final wait after the Qt event loop exits also covers external quit routes. Normal
close uses the asynchronous path and keeps the UI responsive while waiting.

## Capture and DPI

The capture rectangle is the lens client area inside its border/header, including
the transparent area behind the translation output. Windows maps client coordinates
using physical `GetClientRect` + `ClientToScreen`, never by multiplying a global Qt
screen origin by a DPI factor. Negative coordinates remain signed. A pure geometry
function scales local client edges. Per-monitor V2 awareness is selected before Qt.

Windows first excludes both application windows with `WDA_EXCLUDEFROMCAPTURE`.
If exclusion is unavailable, or `--capture-mode hide` is selected, the UI temporarily
hides its visible windows, waits for compositor settling, captures, then restores
them before OCR. This can flicker. API success is not proof that GDI reveals the
underlying content: test exclusion on Windows and use the hide path if it produces
black/stale/self-captured content. Neither method captures protected content.
Hide mode waits 80 ms by default (`--hide-settle-ms`); this is a settling heuristic,
not a proof of compositor readiness. Capture completion restores windows before
OCR starts returning results. The controller suppresses capture during drags,
resize gestures, popups, and modal dialogs. Both app windows are non-activating
when restored, but focus behavior still needs Windows verification.

mss receives only the requested region, rejects requests outside the desktop
bounding rectangle or over 16 million pixels, and returns an owned RGB array.
Its session is recreated periodically (5 seconds) or after a capture error to
refresh monitor metadata using public APIs. Gaps between monitors have no content.

## Efficiency and errors

Default capture interval: 350 ms, with no overlapping jobs. Visual comparison uses
a downsampled grayscale image plus mean/local change thresholds. Compare against
the last successfully processed image so gradual changes accumulate. Translation
keys are `(source, target, normalized_text)` in a bounded in-memory LRU. Do not
commit detector/text success state on errors, so the same frame can retry.
Empty text clears the display; unchanged text avoids a translation call. Providers
report actionable, sanitized errors; failures back off and do not kill the GUI.
Error backoff is 1/2/4/8 seconds. Errors reset success state; platform errors also
advance the revision so the last good text can be rendered again after recovery.
The default cache capacity is 256 entries. Image comparison uses at most 320×180
grayscale samples; defaults are mean difference 2/255 or at least 0.3% of samples
changing by 20/255. These heuristics need tuning on real screen content.

## OCR model selection and upgrade path

PaddleOCR 3.3.2 / PaddlePaddle 3.2.2 are the tested CPU pair. English uses explicit
`PP-OCRv5_mobile_det` and `en_PP-OCRv5_mobile_rec`. Other model languages use
Paddle's model-pair resolution. Do not mix `lang` with explicit model names: this
Paddle version ignores the language in that combination. Native calls receive BGR
converted from the capture contract's RGB. Polygon/text/confidence results are
validated; filtering defaults to confidence ≥ 0.60. First-load timings include
model initialization and possibly download; warm timings reflect inference.

Future providers implement `OCRProvider.recognize(image)` or
`TranslationProvider.translate(text, source_language, target_language)`. Create a
new pipeline/cache when swapping translator instances to avoid mixing provider
results. To replace mss, implement `CaptureProvider` with physical region semantics;
the UI's visibility strategy and Windows acceptance tests must also be reviewed.

## Privacy

Capture arrays and cache are memory-only. No frame/history persistence or default
recognized-text logging. An explicit text-log flag is separate from ordinary debug.
Paddle model downloads may need network access initially; inference is local.
Future online providers should send text only and have explicit timeouts and consent.
