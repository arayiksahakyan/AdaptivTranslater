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

Decision: Keep MockTranslationProvider as the default offline path, and add a
separate opt-in Google Cloud provider with the same contract. Keep screenshots/cache
ephemeral; ordinary debug logs omit text. Do not implement undocumented free endpoints.
Reason: Preserve deterministic offline development while allowing real text-only
translation when the user configures a credential. Consequences: real translation
has network, billing, privacy, and provider-availability implications. Future
providers implement the same contract; commercial backend services remain planning only.

Default-provider choice superseded by ADR-008; Mock remains available.

## ADR-007 — Google Cloud Translation Basic as first real provider

Decision: Add a Google Cloud Translation Basic REST adapter using Python's standard
HTTPS client and an API key from `GOOGLE_TRANSLATE_API_KEY`. Keep Mock as the default
and expose both through an injected provider registry.

Reason: Google supports English → Russian and a broad language set through a small
JSON REST request. The request can contain only normalized OCR text, avoiding image
uploads and a heavyweight SDK in the desktop MVP. A timeout and sanitized errors fit
the existing worker/retry path.

Alternatives: DeepL (strong quality but narrower language coverage and an additional
provider-specific account), Azure Translator (similar credentials and setup), public
LibreTranslate instances (variable availability/privacy), and local Argos models
(offline but weaker quality/model packaging for this MVP).

Consequences: A Google API key, enabled API, billing, and quotas are required for
real translation. Requests may incur charges. The key is never hard-coded or logged.
Network availability and Google behavior remain runtime dependencies. Future
providers implement the same protocol and receive provider-specific cache entries.

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

## ADR-008 — Free offline Argos as preferred real development provider

Decision (2026-09-24): Add `argos-local` using Argos Translate 1.11.0, pin MiniSBD
0.9.5 for its audited local-path behavior, and default to Local / English → Russian.
Retain Mock and optional Google Cloud Basic without changing Google's API contract.
This supersedes only the default-provider choice in ADR-005/007.

Reason: The MVP needs real translation without billing verification, credentials,
an account, or a backend. Local models keep all OCR text on the computer. Existing
worker scheduling, revision cancellation, provider-aware cache, and error recovery
already support this integration. Keep runtime installation optional for core tests.

Argos's normal sentence splitting can download auxiliary models. Force OPENNMT,
CPU, and MiniSBD before importing the engine, disable Argos payload logging, and
resolve every translation leg to an existing absolute MiniSBD file before inference.
Set ONNX Runtime's telemetry opt-out before initialization and disable its telemetry
API before translation sessions; official runtime builds otherwise enable telemetry.
Only an explicit CLI installs translation/auxiliary models. Missing resources report
an actionable error with Mock available; no silent download or provider switch.
Use Argos's installed graph for pivots; retain translators for the worker lifetime.
Require restart after external model changes and explicit source selection.

Alternatives: Waiting for Google billing, undocumented public endpoints, automatically
fetching models during app startup, or older Argos/dependency downgrades. None meets
the current combination of offline privacy, explicit downloads, and dependency scope.

Dependency evidence: Official package/source inspection plus combined binary-wheel
resolution for Windows x64 Python 3.12 and Linux found no metadata conflicts with
PaddleOCR 3.3.2 / PaddlePaddle 3.2.2. No unrelated versions were downgraded. Native
PyTorch/ONNX/CTranslate2/Paddle coexistence and actual Windows output still require
real testing. Automated Argos tests use injected doubles and download no models.

Consequences: Free inference needs local disk/RAM and upfront model downloads.
Quality and speed vary by language/model; pivots may reduce quality and increase
latency. Python runtime dependencies are larger than the Argos wheel. The small
version-specific offline adapter must be re-audited when Argos/MiniSBD changes.
Native translation calls, like OCR, cannot be safely interrupted; stale results are
discarded and shutdown waits for the current call. No new backend or billing setup.

## ADR-009 — Explicit Paddle diagnostics and bounded initialization retries

Decision (2026-09-25): Preserve original OCR exceptions with `raise ... from exc`;
keep ordinary public messages/logs sanitized. Developer smoke/direct tools print
environment/cache metadata and full chained tracebacks. Share pure model options
between the adapter and direct constructor, without importing the adapter in the
direct tool. Test a CPU tensor operation before creating PaddleOCR.

Reason: Real Windows 11 / Python 3.12.3 finds the detector cache but initialization
fails with a RuntimeError hidden by `from None`. The actual cause is unknown; model
presence and a ccache warning do not diagnose it. No dependency versions change.

Use a typed initialization error and pipeline failure latch keyed by region,
languages, and provider, ignoring revisions. The existing controller increments
revisions during automatic error handling, so revision-only latching would loop.
An explicit move/resize or settings change permits one retry; repeated failures
are latched again. Pause/resume alone does not clear this latch. UI code is outside
scope and remains unchanged, including its existing retry suffix. Store only the
safe message/context, not exceptions retaining images through tracebacks. Keep
transient inference and translation retry behavior unchanged.

Consequences: Diagnostic logs include native error details and local paths by
design, but use only generated text. Direct initialization does not test inference.
Linux test/smoke success is not Windows acceptance. Windows output must guide the
next fix; do not infer dependency incompatibilities or propose speculative pins.

## Reference documentation consulted

- [Qt high-DPI behavior](https://doc.qt.io/qtforpython-6/overviews/qtdoc-highdpi.html)
- [Qt QThread worker objects](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html)
- [Windows capture affinity](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity)
- [PaddleOCR 3 OCR API](https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/pipeline_usage/OCR.html)
- [PaddleOCR 3.3.2 implementation](https://github.com/PaddlePaddle/PaddleOCR/blob/v3.3.2/paddleocr/_pipelines/ocr.py)
- [Win32 hotkey registration](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey)
- [Win32 layered windows](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features)
- [PaddlePaddle 3.2.2 Windows wheels](https://pypi.org/project/paddlepaddle/3.2.2/#files)
- [Argos Translate 1.11.0 release](https://pypi.org/project/argostranslate/1.11.0/)
- [Argos 1.11.0 sentence splitting](https://github.com/argosopentech/argos-translate/blob/v1.11.0/argostranslate/sbd.py)
- [Argos official model index](https://github.com/argosopentech/argospm-index/blob/main/index.json)
- [MiniSBD source and models](https://github.com/LibreTranslate/MiniSBD)
- [ONNX Runtime privacy controls](https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md)
