# Translation Lens: agent instructions

Read this file and `PROGRESS.md` before changing the project.

- Build a local, Windows 10/11 translation lens. Linux is a development/test host,
  not a change of target platform. Python 3.11+; recommend 3.12 for OCR dependencies.
- Keep GUI code in `app/ui`, orchestration in `app/pipeline`, and Windows APIs in
  `app/platform`. OCR and translation providers must not import GUI modules.
- Use typed, small components and dependency injection. Keep screenshots in memory.
- Never run OCR/translation in the GUI thread. Permit one in-flight job; discard
  results after geometry, language, pause, or mode changes using revision tokens.
- Use real region capture and OCR. Only the translation provider is intentionally
  mocked in the MVP. Test doubles belong in tests, never in the production path.
- Never store screenshots/OCR history by default or log recognized text unless the
  user explicitly enables text logging. Never commit credentials, models, or venvs.
- No accounts, billing, cloud infrastructure, analytics, or advanced text replacement.
- Preserve useful existing work; make small logical changes. Record significant
  choices in `DECISIONS.md`. Do not commit/push unless requested.
- Before completion run `.venv/bin/python -m pytest`,
  `.venv/bin/python -m ruff check .`, and `.venv/bin/python -m compileall -q app tests tools`.
  On Windows use `.venv\Scripts\python.exe` instead. Qt tests run offscreen.
- Run the desktop with `python -m app.main`; see `DEVELOPMENT.md` for dependencies.
- For each meaningful task update documentation and `PROGRESS.md` with actual
  commands, results, remaining work, and limitations.
- Definition of done: implemented, relevant checks pass, errors investigated,
  documentation/current task updated. Use **IMPLEMENTED**, **TESTED ON LINUX**,
  **TESTED ON WINDOWS**, **REQUIRES WINDOWS VERIFICATION**, or **NOT IMPLEMENTED**
  precisely. Windows checks remain unchecked until executed on Windows.
- Do not infer Windows success from offscreen tests, API stubs, or Linux screenshots.
- Paddle 3 ignores `lang` if any explicit model name is supplied: English sets both
  mobile models; other languages use Paddle's language-based model resolution.
  Recheck `tools.ocr_smoke` and its language regression tests when changing this.
