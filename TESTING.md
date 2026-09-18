# Testing

## Automated tests

Use pytest with dependency-injected test providers. No paid API, real monitor, or
model downloads are required by the default suite. Qt integration runs offscreen.
Cover image thresholds and accumulated drift; Unicode/line normalization; cache
language separation/eviction; unchanged frames and duplicate OCR; empty/filtered
OCR; translation/capture/OCR failures and retries; revision invalidation; coordinate
math; worker scheduling; hide/restore; and cooperative shutdown.

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall -q app tests tools
```

Automated adapters may test native call contracts using doubles; they do not test
the Windows compositor, DPI, input routing, or real global shortcuts. Real OCR
smoke testing is separate and optional during core-only development.

Latest Linux results (2026-09-19): **94 passed**, Ruff passed, compilation passed,
and dependency consistency passed. The full application launched offscreen and
exited cleanly after SIGTERM. Real English PaddleOCR recognized generated sample
text twice with cached models; warm inference was 223 ms on a 700×180 image.
This is one sample, not a desktop OCR accuracy or product throughput benchmark.
See [the validation record](docs/validation/2026-09-19-linux.md).

Tests in `test_windows_contracts.py` use API doubles. They check flags, rollback,
hotkey routing/cleanup, and exclusion fallback selection; they do not satisfy a
single Windows manual checkbox. No Windows OS tests have run.

## Windows manual verification

Status: **REQUIRES WINDOWS VERIFICATION**. Nothing below has run on Windows.

- [ ] Launch and graceful shutdown.
- [ ] Transparency, visible border, topmost, movement, resize, minimum size.
- [ ] Capture coordinates at each DPI and on mixed/negative-origin monitors.
- [ ] Underlying pixels visible with no lens/control-panel contamination.
- [ ] Real OCR, confidence handling, mock output, cache, errors, and pause.
- [ ] Click-through and global shortcuts from another application.
- [ ] No obsolete output after moving/changing language/pausing.
- [ ] Sustained run and shutdown during model loading/OCR.

Detailed steps and result-record template: [`docs/WINDOWS_TESTING.md`](docs/WINDOWS_TESTING.md).
Only mark checks complete after execution; include OS build, scaling, monitor
layout, dependency versions, expected/observed results, and evidence locations.
