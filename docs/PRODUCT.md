# Translation Lens

## Problem and users

People encounter untranslated games, desktop software, documents, and web content.
A movable lens offers an alternative to copying text or repeatedly taking screenshots.
Potential users include gamers, people using untranslated software, foreign-language
readers, and language learners.

## Core experience

Place a transparent, bordered lens over content, resize it, select source and target
languages, and start. Read output in a panel inside the lens. Switch between Edit
and Click-through modes; the latter permits interacting with the underlying app.
A separate control panel remains accessible. Ctrl+Shift+T starts/pauses;
Ctrl+Shift+L changes mode; Esc cancels an active move/resize or returns to Edit.

## Local MVP

One always-on-top lens; real bounded capture; inexpensive visual change detection;
real local OCR; conservative normalization; text deduplication; bounded memory cache;
mock translation; responsive controls; recoverable errors and privacy-safe logging.
The mock explicitly labels its output and does not perform linguistic translation.
Source Auto uses the configured OCR model; automatic OCR model/language detection is
a future feature. OCR language is a separate startup setting.

## Non-goals

Accounts, backend services, payments, telemetry, advanced text replacement, multiple
lenses, retained OCR history, and cloud deployment are outside this MVP.
Linux desktop support and exclusive-fullscreen game capture are not MVP commitments.

## Future

Better OCR/layout, per-span translation positioning, settings persistence, automatic
language detection, offline translation, contextual dialogue, terminology dictionaries,
subtitle/gaming modes, and optional commercial services. Privacy remains explicit:
local images, opt-in online text translation, no automatic image/history storage.

## Prototype status

The first implementation and Linux automated/real-OCR checks are complete. This
demonstrates the portable components and widget logic; native Windows acceptance
is still open. The output panel displays a labeled mock result, with no real
linguistic translation or original-text replacement. Shipping a Windows release
requires the unchecked tests in `WINDOWS_TESTING.md`, including real pixel capture.
