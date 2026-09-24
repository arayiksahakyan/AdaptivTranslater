"""Explicit online setup only: python -m tools.install_translation_model en ru."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import Any

from app.errors import TranslationError
from app.translation.argos_local import load_argos, resolve_translator
from app.translation.provider import validate_languages


def install_model(
    source: str, target: str, package: Any, prepare_sentences: Callable[[str], None],
    report: Callable[[str], None] = print,
) -> None:
    """Inject package/download operations so tests never fetch real models."""
    validate_languages(source, target)
    if source == "auto" or source == target:
        raise TranslationError("Choose two different explicit language codes, for example en ru.")
    report("Updating the Argos package index (Internet required)…")
    package.update_package_index()
    installed = next(
        (p for p in package.get_installed_packages()
         if p.type == "translate" and p.from_code == source and p.to_code == target), None,
    )
    if installed is None:
        from packaging.version import Version

        available = [
            p for p in package.get_available_packages()
            if p.type == "translate" and p.from_code == source and p.to_code == target
            and Version(p.argos_version) <= Version("1.11.0")
        ]
        if not available:
            raise TranslationError(
                f"No compatible direct Argos package for {source} → {target}. "
                "Install each leg of an available intermediate path explicitly; "
                "see DEVELOPMENT.md. No translation model was downloaded."
            )
        selected = max(available, key=lambda p: Version(p.package_version))
        report(f"Downloading {source} → {target} (may be hundreds of MB)…")
        package.install_from_path(selected.download())
    else:
        report("Translation package already installed; checking sentence model.")
    report("Preparing the local sentence model (may download a small auxiliary model)…")
    prepare_sentences(source)


def prepare_sentence_model(source: str) -> None:
    from argostranslate.sbd import MiniSBDSentencizer
    from minisbd import SBDetect, models

    code = MiniSBDSentencizer.LANGUAGE_CODE_MAPPING.get(source, source)
    if code not in models.list_models():
        code = "en"  # Same explicit fallback as the pinned Argos implementation.
    SBDetect(code, use_gpu=False)  # Download here only, and verify ONNX initialization.


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("target")
    args = parser.parse_args(argv)
    try:
        validate_languages(args.source, args.target)
        load_argos()
        from argostranslate import package

        install_model(args.source, args.target, package, prepare_sentence_model)
        # Confirm the installed direct/pivot translation has all local resources.
        resolve_translator(args.source, args.target)
    except TranslationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ImportError:
        print("Install dependencies: python -m pip install -r requirements-translation.txt",
              file=sys.stderr)
        return 1
    except Exception:
        print("Model setup failed. Check network, disk space and translation dependencies. "
              "Rerun this command to retry; see DEVELOPMENT.md.", file=sys.stderr)
        return 1
    print(f"Installed and ready: {args.source} → {args.target}. Restart Translation Lens. "
          "Optional verification: python -m tools.translation_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
