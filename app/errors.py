"""Only these controlled messages are safe to show without leaking provider payloads."""


class LensError(Exception):
    """An actionable, public error with no screen text or secrets in its message."""


class CaptureError(LensError):
    pass


class OCRError(LensError):
    pass


class OCRInitializationError(OCRError):
    """Loading failed; wait for a user change to the region/language/provider."""


class TranslationError(LensError):
    pass


class PlatformError(LensError):
    pass
