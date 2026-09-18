"""Linux API-double checks only; none establishes Windows-native behavior."""

import ctypes
from ctypes import wintypes
from types import SimpleNamespace

import pytest

from app.errors import PlatformError
from app.platform.windows import (
    GWL_EXSTYLE,
    WDA_EXCLUDEFROMCAPTURE,
    WM_HOTKEY,
    WS_EX_NOACTIVATE,
    WS_EX_TRANSPARENT,
    WindowsPlatform,
    _HotkeyFilter,
)


@pytest.fixture
def native(monkeypatch):
    # ctypes last-error helpers exist only on real Windows; the doubles model
    # their success values to inspect call arguments, not OS implementation.
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 0, raising=False)
    monkeypatch.setattr(ctypes, "set_last_error", lambda code: None, raising=False)
    adapter = WindowsPlatform.__new__(WindowsPlatform)
    adapter.requires_hide = False
    adapter._styles = {}
    adapter._callbacks = {}
    adapter._filter = None
    adapter._app = None
    return adapter


def test_affinity_failure_switches_to_hide_for_all_windows(native):
    calls = []

    def affinity(hwnd, value):
        calls.append((hwnd, value))
        return hwnd == 100

    native._user32 = SimpleNamespace(SetWindowDisplayAffinity=affinity)
    windows = [SimpleNamespace(winId=lambda: 100), SimpleNamespace(winId=lambda: 200)]
    notices = native.prepare_windows(windows)
    assert calls == [(100, WDA_EXCLUDEFROMCAPTURE), (200, WDA_EXCLUDEFROMCAPTURE)]
    assert native.requires_hide and notices


def test_click_through_preserves_unrelated_style_bits_and_reverts(native):
    layered = 0x00080000
    style = [layered]
    positions = []

    def set_style(hwnd, index, value):
        assert index == GWL_EXSTYLE
        previous, style[0] = style[0], value
        return previous

    native._get_style = lambda hwnd, index: style[0]
    native._set_style = set_style
    native._user32 = SimpleNamespace(SetWindowPos=lambda *args: positions.append(args) or True)
    window = SimpleNamespace(winId=lambda: 100)
    native.set_click_through(window, True)
    assert style[0] == layered | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    native.set_click_through(window, False)
    assert style[0] == layered and len(positions) == 2


def test_failed_style_refresh_rolls_back(native):
    style = [0x80000]

    def set_style(hwnd, index, value):
        previous, style[0] = style[0], value
        return previous

    native._get_style = lambda *_: style[0]
    native._set_style = set_style
    native._user32 = SimpleNamespace(SetWindowPos=lambda *_: False)
    with pytest.raises(PlatformError):
        native.set_click_through(SimpleNamespace(winId=lambda: 10), True)
    assert style[0] == 0x80000


def test_hotkey_conflict_reporting_and_registered_key_cleanup(native):
    registered, removed, filters = [], [], []

    def register(hwnd, identifier, modifiers, key):
        registered.append((hwnd, identifier, modifiers, key))
        return key == ord("T")

    native._user32 = SimpleNamespace(
        RegisterHotKey=register, UnregisterHotKey=lambda hwnd, key: removed.append(key) or True
    )
    app = SimpleNamespace(
        installNativeEventFilter=filters.append, removeNativeEventFilter=filters.remove
    )
    messages = native.register_hotkeys(app, lambda: None, lambda: None)
    assert "Ctrl+Shift+L unavailable" in messages[0]
    assert registered[0][2] & 0x4000  # MOD_NOREPEAT
    native.close()
    assert removed == [0x5101] and filters == []


def test_hotkey_native_filter_routes_only_registered_messages():
    received = []
    event_filter = _HotkeyFilter({0x5101: lambda: received.append(True)})
    message = wintypes.MSG()
    message.message = WM_HOTKEY
    message.wParam = 0x5101
    assert event_filter.nativeEventFilter(b"windows_dispatcher_MSG", ctypes.addressof(message)) == (
        True,
        0,
    )
    assert received == [True]
    message.wParam = 0xFFFF
    assert event_filter.nativeEventFilter(b"windows_dispatcher_MSG", ctypes.addressof(message)) == (
        False,
        0,
    )
