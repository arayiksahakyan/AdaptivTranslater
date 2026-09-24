"""Optional real English → Russian smoke; never installs/downloads models."""

from time import perf_counter

from app.errors import TranslationError
from app.translation.argos_local import ArgosLocalTranslationProvider


def main() -> int:
    provider = ArgosLocalTranslationProvider()
    try:
        for label, text in (("cold", "Hello world!"), ("warm", "This is a test.")):
            started = perf_counter()
            result = provider.translate(text, "en", "ru")
            print(f"{label}: {result} ({(perf_counter() - started) * 1000:.0f} ms)")
            if not any("а" <= letter.lower() <= "я" or letter.lower() == "ё" for letter in result):
                print("FAIL: expected Russian Cyrillic; inspect the installed model.")
                return 1
    except TranslationError as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: real local English → Russian smoke. Review translation quality manually.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
