"""Windows API wrappers used by KeepAwakeClicker.

The module is safe to import on non-Windows development machines. Windows
DLLs are loaded only when a Windows-only function is called.
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes


IS_WINDOWS = sys.platform == "win32"

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

PROCESS_PER_MONITOR_DPI_AWARE = 2


if IS_WINDOWS:
    ULONG_PTR = wintypes.WPARAM

    class POINT(ctypes.Structure):
        _fields_ = (("x", wintypes.LONG), ("y", wintypes.LONG))

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = (
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        )

    class INPUT_UNION(ctypes.Union):
        _fields_ = (("mi", MOUSEINPUT),)

    class INPUT(ctypes.Structure):
        _anonymous_ = ("union",)
        _fields_ = (("type", wintypes.DWORD), ("union", INPUT_UNION))
else:
    POINT = None
    INPUT = None


_kernel32 = None
_user32 = None
_shcore = None


def _require_windows() -> None:
    if not IS_WINDOWS:
        raise OSError("此功能只能在 Windows 上執行。")


def _load_libraries() -> tuple[ctypes.WinDLL, ctypes.WinDLL]:
    global _kernel32, _user32
    _require_windows()
    if _kernel32 is None:
        _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _user32 = ctypes.WinDLL("user32", use_last_error=True)
    return _kernel32, _user32


def _last_error(message: str) -> OSError:
    error_code = ctypes.get_last_error()
    if error_code:
        return OSError(error_code, f"{message} (Windows 錯誤 {error_code})")
    return OSError(message)


def set_thread_execution_state(prevent_sleep: bool, prevent_display: bool) -> None:
    """Set or clear the current process' Windows execution requirements."""

    kernel32, _ = _load_libraries()
    set_state = kernel32.SetThreadExecutionState
    set_state.argtypes = [wintypes.DWORD]
    set_state.restype = wintypes.DWORD

    if prevent_sleep:
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        if prevent_display:
            flags |= ES_DISPLAY_REQUIRED
    else:
        flags = ES_CONTINUOUS

    if set_state(flags) == 0:
        raise _last_error("無法設定 Windows 電源狀態")


def get_cursor_pos() -> tuple[int, int]:
    """Return the cursor position in the Windows virtual desktop."""

    _, user32 = _load_libraries()
    get_pos = user32.GetCursorPos
    get_pos.argtypes = [ctypes.POINTER(POINT)]
    get_pos.restype = wintypes.BOOL

    point = POINT()
    if not get_pos(ctypes.byref(point)):
        raise _last_error("無法取得目前滑鼠位置")
    return int(point.x), int(point.y)


def set_cursor_pos(x: int, y: int) -> None:
    """Move the cursor to a virtual-desktop coordinate without DPI scaling."""

    _, user32 = _load_libraries()
    set_pos = user32.SetCursorPos
    set_pos.argtypes = [wintypes.INT, wintypes.INT]
    set_pos.restype = wintypes.BOOL

    if not set_pos(int(x), int(y)):
        raise _last_error("無法移動滑鼠")


def left_click() -> None:
    """Send a physical left-button click through SendInput."""

    _, user32 = _load_libraries()
    send_input = user32.SendInput
    send_input.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    send_input.restype = wintypes.UINT

    for flags in (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP):
        mouse_input = INPUT(
            type=0,
            union=INPUT_UNION(
                mi=MOUSEINPUT(
                    dx=0,
                    dy=0,
                    mouseData=0,
                    dwFlags=flags,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )
        if send_input(1, ctypes.byref(mouse_input), ctypes.sizeof(INPUT)) != 1:
            raise _last_error("無法送出滑鼠點擊")


def click_at(x: int, y: int) -> None:
    """Move to a coordinate and send a left click."""

    set_cursor_pos(x, y)
    time.sleep(0.05)
    left_click()


def set_per_monitor_dpi_awareness() -> bool:
    """Enable Per Monitor DPI Aware V2, with a Windows 10 fallback."""

    if not IS_WINDOWS:
        return False

    global _user32, _shcore
    if _user32 is None:
        _load_libraries()

    try:
        set_context = _user32.SetProcessDpiAwarenessContext
    except AttributeError:
        set_context = None

    if set_context is not None:
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = wintypes.BOOL
        # -4 is DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2.
        if set_context(ctypes.c_void_p(-4)):
            return True

    try:
        if _shcore is None:
            _shcore = ctypes.WinDLL("shcore", use_last_error=True)
        set_awareness = _shcore.SetProcessDpiAwareness
        set_awareness.argtypes = [ctypes.c_int]
        set_awareness.restype = ctypes.HRESULT
        # S_OK and E_ACCESSDENIED (already configured by an external manifest)
        # both mean that the process has a usable DPI mode.
        result = set_awareness(PROCESS_PER_MONITOR_DPI_AWARE)
        return result in (0, 0x80070005)
    except (AttributeError, OSError):
        return False
