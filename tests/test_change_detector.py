import numpy as np
import pytest

from app.capture.change_detector import ImageChangeDetector


def frame(value=0, shape=(180, 320, 3)):
    return np.full(shape, value, dtype=np.uint8)


def test_first_frame_and_explicit_commit():
    detector = ImageChangeDetector()
    assert detector.has_changed(frame())
    assert detector.has_changed(frame())  # inspection does not advance baseline
    detector.commit(frame())
    assert not detector.has_changed(frame())


def test_gradual_drift_compares_with_accepted_baseline():
    detector = ImageChangeDetector(mean_threshold=5)
    detector.commit(frame())
    assert not detector.has_changed(frame(2))
    assert not detector.has_changed(frame(4))
    assert detector.has_changed(frame(6))


def test_local_changed_word_triggers_without_large_mean_difference():
    detector = ImageChangeDetector()
    detector.commit(frame())
    changed = frame()
    changed[10:20, 20:40] = 255
    assert changed.mean() < 2
    assert detector.has_changed(changed)


def test_small_pixel_noise_is_ignored():
    detector = ImageChangeDetector()
    detector.commit(frame(100))
    noisy = frame(101)
    noisy[4, 4] = 255
    assert not detector.has_changed(noisy)


def test_shape_change_and_reset_force_ocr():
    detector = ImageChangeDetector()
    detector.commit(frame())
    assert detector.has_changed(frame(shape=(200, 320, 3)))
    detector.reset()
    assert detector.has_changed(frame())


def test_uint8_difference_does_not_overflow():
    detector = ImageChangeDetector()
    detector.commit(frame(255))
    assert detector.has_changed(frame(0))


@pytest.mark.parametrize(
    "image", [np.zeros((20, 20)), frame(shape=(0, 20, 3)), frame(shape=(20, 20, 4))]
)
def test_invalid_image_rejected(image):
    with pytest.raises(ValueError):
        ImageChangeDetector().has_changed(image)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mean_threshold": 0},
        {"pixel_threshold": 256},
        {"changed_fraction": 0},
        {"sample_size": (0, 10)},
    ],
)
def test_invalid_thresholds_rejected(kwargs):
    with pytest.raises(ValueError):
        ImageChangeDetector(**kwargs)
