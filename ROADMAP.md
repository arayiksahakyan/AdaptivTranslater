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
- [x] Add labeled mock translation and language-aware cache; automated tests pass.
- [x] Run pipeline outside GUI thread; test stale results, cancellation, and cleanup.
- [x] Add/test controls, language choices, status, errors, start/pause, and timing.
- [ ] Verify implemented Windows click-through and registered global shortcuts.
- [x] Test recoverable errors, duplicate text, retries, stale jobs, and shutdown.
- [x] Execute Linux automated/Qt integration checks and record results (94 passed).
- [x] Execute real local OCR smoke test (English mobile models; cached/offline run).
- [ ] Verify Windows launch, transparency, geometry, capture, and contamination.
- [ ] Verify Windows 100/125/150/200% DPI and mixed-DPI/negative-origin monitors.
- [ ] Verify Windows OCR/output, global shortcuts, click-through, and shutdown.
- [ ] Complete a sustained Windows capture → OCR → mock output acceptance run.

## Phase 2: better OCR and UX

- [ ] Tune OCR on real desktop/game fonts and publish performance measurements.
- [ ] Improve layout/read order and text-position preservation.
- [ ] Add settings persistence, multiple lenses, and accessibility refinements.
- [ ] Add automatic OCR language detection and local translation provider.
- [ ] Evaluate Windows Graphics Capture and packaged Windows distributions.

## Phase 3: context-aware translation

- [ ] Add explicit contextual memory controls, terminology, and subtitle modes.
- [ ] Evaluate local LLMs and real translation providers with privacy controls.

## Phase 4: commercial/cloud version (planning only)

- [ ] Review licensing, signing, updating, and distribution requirements.
- [ ] Design optional identity, plans/licenses, credits, and provider proxy.
- [ ] Design opt-in usage reporting and retention limits; no infrastructure now.
