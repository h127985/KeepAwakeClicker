"""Global Windows hotkeys backed by RegisterHotKey and WM_HOTKEY."""

from __future__ import annotations

import ctypes
import queue
import threading
import tkinter as tk
from ctypes import wintypes
from collections.abc import Callable

from windows_api import IS_WINDOWS


MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
VK_F8 = 0x77
VK_F12 = 0x7B

HOTKEY_RECORD_POSITION = 1
HOTKEY_EMERGENCY_STOP = 2


class HotkeyManager:
    def __init__(self) -> None:
        self._root: tk.Misc | None = None
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._events: queue.Queue[int] = queue.Queue()
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._registered_ids: list[int] = []
        self._poll_after_id: str | None = None
        self.errors: list[str] = []

    def start(self, root: tk.Misc, callbacks: dict[int, Callable[[], None]]) -> list[str]:
        self._root = root
        self._callbacks = callbacks
        self.errors = []

        if not IS_WINDOWS:
            self.errors.append("全域快捷鍵只能在 Windows 上使用。")
            return self.errors

        self._thread = threading.Thread(target=self._message_loop, name="KeepAwakeClickerHotkeys", daemon=True)
        self._thread.start()
        self._ready_event.wait(timeout=2)
        if not self._ready_event.is_set():
            self.errors.append("全域快捷鍵啟動逾時。")
            return self.errors

        self._poll_after_id = root.after(50, self._poll_events)
        return self.errors

    def stop(self) -> None:
        if self._root is not None and self._poll_after_id is not None:
            try:
                self._root.after_cancel(self._poll_after_id)
            except tk.TclError:
                pass
            self._poll_after_id = None

        self._stop_event.set()
        if IS_WINDOWS and self._thread_id is not None:
            try:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                post_thread_message = kernel32.PostThreadMessageW
                post_thread_message.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
                post_thread_message.restype = wintypes.BOOL
                post_thread_message(self._thread_id, WM_QUIT, 0, 0)
            except OSError:
                pass

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        self._thread_id = None

    def _message_loop(self) -> None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        get_current_thread_id = kernel32.GetCurrentThreadId
        get_current_thread_id.restype = wintypes.DWORD
        self._thread_id = int(get_current_thread_id())

        register_hotkey = user32.RegisterHotKey
        register_hotkey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        register_hotkey.restype = wintypes.BOOL
        unregister_hotkey = user32.UnregisterHotKey
        unregister_hotkey.argtypes = [wintypes.HWND, ctypes.c_int]
        unregister_hotkey.restype = wintypes.BOOL

        definitions = (
            (HOTKEY_RECORD_POSITION, MOD_NOREPEAT, VK_F8),
            (HOTKEY_EMERGENCY_STOP, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_F12),
        )
        for hotkey_id, modifiers, virtual_key in definitions:
            if register_hotkey(None, hotkey_id, modifiers, virtual_key):
                self._registered_ids.append(hotkey_id)
            else:
                error_code = ctypes.get_last_error()
                self.errors.append(f"無法註冊全域快捷鍵（Windows 錯誤 {error_code}）。")

        self._ready_event.set()
        message = wintypes.MSG()
        get_message = user32.GetMessageW
        get_message.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        get_message.restype = ctypes.c_int

        try:
            while not self._stop_event.is_set():
                result = get_message(ctypes.byref(message), None, 0, 0)
                if result <= 0:
                    break
                if message.message == WM_HOTKEY:
                    self._events.put(int(message.wParam))
        finally:
            for hotkey_id in self._registered_ids:
                unregister_hotkey(None, hotkey_id)
            self._registered_ids.clear()

    def _poll_events(self) -> None:
        self._poll_after_id = None
        while True:
            try:
                hotkey_id = self._events.get_nowait()
            except queue.Empty:
                break
            callback = self._callbacks.get(hotkey_id)
            if callback is not None:
                callback()

        if not self._stop_event.is_set() and self._root is not None:
            self._poll_after_id = self._root.after(50, self._poll_events)
