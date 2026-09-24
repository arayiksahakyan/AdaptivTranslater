import threading

import numpy as np

from app.ocr.base import OCRResult


class FakeCapture:
    def __init__(self):
        self.image = np.zeros((80, 120, 3), dtype=np.uint8)
        self.calls = 0
        self.error = None
        self.closed = False
        self.threads = []

    def capture(self, region):
        self.calls += 1
        self.threads.append(threading.get_ident())
        if self.error is not None:
            raise self.error
        return self.image.copy()

    def close(self):
        self.closed = True
        self.threads.append(threading.get_ident())


class FakeOCR:
    def __init__(self):
        self.text = "Hello world!"
        self.confidence = 0.99
        self.calls = 0
        self.error = None
        self.closed = False
        self.threads = []

    def recognize(self, image):
        self.calls += 1
        self.threads.append(threading.get_ident())
        if self.error is not None:
            raise self.error
        return [OCRResult(self.text, self.confidence, ((0, 0), (80, 0), (80, 25), (0, 25)))]

    def close(self):
        self.closed = True
        self.threads.append(threading.get_ident())


class FakeTranslator:
    provider_id = "custom"

    def __init__(self):
        self.calls = []
        self.error = None

    def translate(self, text, source, target):
        self.calls.append((text, source, target))
        if self.error is not None:
            raise self.error
        return f"{target}: {text}"
