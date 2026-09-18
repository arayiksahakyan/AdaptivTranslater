# Decisions

## ADR-001 — Windows-first PySide6 with portable core

Decision: Use Python 3.11+ and PySide6, recommend Python 3.12 for the initial OCR
environment, and keep the package at repository root.
Reason: Native desktop widgets and Qt worker integration meet the lens prototype
needs; the existing repository is empty except for its name.
Alternatives: Native C#/C++, web UI, nested `translation-lens` directory.
Consequences: Linux can verify core/widget logic; Win32 behavior needs actual
Windows tests. No claim of full Linux product support.

## ADR-002 — mss behind capture interface; native geometry/exclusion

Decision: Use bounded mss capture, physical client mapping, capture exclusion for
both windows, and an explicit hide/settle/restore fallback.
Reason: Keep initial capture small and replaceable while addressing self-capture.
Alternatives: Windows Graphics Capture now, whole-desktop capture, ignoring overlay.
Consequences: Hide mode can flicker; exclusion must be verified against actual
underlying pixels. Windows 10 builds before 2004 need hide mode. Native compositor
behavior, monitor boundaries, and protected surfaces remain Windows test gates.

## ADR-003 — Optional real PaddleOCR 3 adapter

Decision: Isolate lazy PaddleOCR initialization and CPU inference from Qt. Maintain
an optional OCR requirements file. Select OCR model language explicitly at startup.
Reason: Large native dependencies must not block deterministic core development.
Alternatives: Mandatory heavyweight install, fake OCR, legacy 2.x-only integration.
Consequences: Actual use requires OCR dependencies and models; missing resources
produce errors. Source Auto is a translation hint, not automatic script detection.

## ADR-004 — Serial background pipeline and revision tokens

Decision: One QObject/QThread owns expensive resources; one job at a time. Use a
revision counter for obsolete results, cooperative shutdown, transactional success
state for retries, and a bounded language-aware LRU cache.
Reason: Avoid GUI stalls, stale output, unbounded queues, and repeated requests.
Alternatives: UI-thread work, one thread per frame, process pools.
Consequences: Throughput is bounded by OCR; native calls cannot be safely killed.
Future providers need timeouts; process isolation can address hard cancellation later.

## ADR-005 — Deliberate mock translation and privacy defaults

Decision: Only mock translation ships initially, clearly labeled in UI/output.
Keep screenshots/cache ephemeral; ordinary debug logs omit text. Do not implement
undocumented free translation endpoints.
Reason: Prove the pipeline without fees, keys, unsafe scraping, or cloud scope.
Consequences: This prototype does not yet perform real linguistic translation.
Future providers implement the same contract; commercial services are planning only.

## ADR-006 — Explicit English mobile model pair; public mss APIs

Decision: Pin PaddleOCR 3.3.2/PaddlePaddle 3.2.2, use both explicit English mobile
model names, and use language-based resolution for other languages. Disable MKL-DNN
for the initial CPU baseline and use four inference threads. Reopen mss sessions
periodically instead of editing private monitor caches.
Reason: Inspection and real smoke execution showed Paddle ignores `lang` alongside
an explicit detector name, otherwise silently selecting a different recognizer.
mss 10.2 changed its internal cache representation. Avoid relying on either detail.
Alternatives: A large default detector/recognizer for every language, private API
mutation, or duplicating Paddle's entire language-to-model map in our application.
Consequences: English real OCR is verified on Linux; non-English inference still
needs validation. Optional OCR pins are deliberate; core dependency ranges permit
Python 3.11+ resolution, and an exact Linux snapshot records what was executed.
Recheck adapters and real inference on dependency updates. Windows remains untested.

## Reference documentation consulted

- [Qt high-DPI behavior](https://doc.qt.io/qtforpython-6/overviews/qtdoc-highdpi.html)
- [Qt QThread worker objects](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html)
- [Windows capture affinity](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity)
- [PaddleOCR 3 OCR API](https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/pipeline_usage/OCR.html)
- [PaddleOCR 3.3.2 implementation](https://github.com/PaddlePaddle/PaddleOCR/blob/v3.3.2/paddleocr/_pipelines/ocr.py)
- [Win32 hotkey registration](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey)
- [Win32 layered windows](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features)
- [PaddlePaddle 3.2.2 Windows wheels](https://pypi.org/project/paddlepaddle/3.2.2/#files)
