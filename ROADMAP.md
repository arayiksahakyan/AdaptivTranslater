# Roadmap

Implementation and OS validation are separate milestones. An unchecked Windows
item remains incomplete even when its implementation passes Linux tests.

## Phase 0: technical prototype

- [x] Inspect repository and preserve initial README identity.
- [x] Establish project memory, architecture, scope, and verification boundaries.
- [x] Add Python package, dependencies, lint configuration, and test harness.
- [x] Implement typed capture/OCR/translation interfaces.
- [x] Implement/test image change detection, normalization, and LRU cache.
- [x] Implement/test core pipeline with injected provider doubles.

## Phase 1: MVP

- [x] Implement lens widgets; verify alpha, flags, drag/resize in Linux offscreen tests.
- [ ] Validate native physical coordinate mapping and bounded mss capture on Windows
  (IMPLEMENTED; math and adapter contracts tested on Linux).
- [ ] Validate capture exclusion and hide/settle/restore on Windows (IMPLEMENTED;
  scheduling/visibility tested offscreen, physical pixels still unverified).
- [x] Integrate real PaddleOCR with confidence filtering and timing; Linux smoke passed.
- [x] Add labeled mock translation and provider-aware cache; automated tests pass.
- [x] Add opt-in Google Cloud Translation Basic text-only provider with sanitized
  timeout/error handling and mocked network tests.
- [x] Add free `argos-local` provider as the preferred real development default,
  explicit translation/sentence-model installer, offline guards, and retained models.
- [x] Test Argos creation, errors, model/path checks, pivots, cache, selection,
  and worker responsiveness on Linux with mocked Argos (no model downloads).
- [ ] Run optional real English → Russian Argos smoke on Windows.
- [ ] Verify Windows PaddleOCR + Argos → overlay with Internet disconnected and
  no translation network activity, including first-load and sustained responsiveness.
- [x] Run pipeline outside GUI thread; test stale results, cancellation, and cleanup.
- [x] Add/test controls, language choices, status, errors, start/pause, and timing.
- [ ] Verify implemented Windows click-through and registered global shortcuts.
- [ ] Verify Google Cloud Translation on Windows with a user-configured key.
- [x] Test recoverable errors, duplicate text, retries, stale jobs, and shutdown.
- [x] Execute Linux automated/Qt integration checks and record results (142 passed).
- [x] Execute real local OCR smoke test (English mobile models; cached/offline run).
- [ ] Verify Windows launch, transparency, geometry, capture, and contamination.
- [ ] Verify Windows 100/125/150/200% DPI and mixed-DPI/negative-origin monitors.
- [ ] Verify Windows OCR/output, global shortcuts, click-through, and shutdown.
- [ ] Complete a sustained Windows capture → OCR → mock output acceptance run.

## Phase 2: better OCR and UX

- [ ] Tune OCR on real desktop/game fonts and publish performance measurements.
- [ ] Improve layout/read order and text-position preservation.
- [ ] Add settings persistence, multiple lenses, and accessibility refinements.
- [ ] Add automatic OCR language detection; local Argos translation is implemented.
- [ ] Evaluate Windows Graphics Capture and packaged Windows distributions.

## Phase 3: context-aware translation

- [ ] Add explicit contextual memory controls, terminology, and subtitle modes.
- [ ] Evaluate additional real providers, local models, and privacy controls.

## Phase 4: commercial/cloud version (planning only)

- [ ] Review licensing, signing, updating, and distribution requirements.
- [ ] Design optional identity, plans/licenses, credits, and provider proxy.
- [ ] Design opt-in usage reporting and retention limits; no infrastructure now.
