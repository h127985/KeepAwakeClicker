"""Power-state control for the KeepAwakeClicker application."""

from __future__ import annotations

from windows_api import IS_WINDOWS, set_thread_execution_state


class KeepAwakeController:
    def __init__(self) -> None:
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def apply(self, prevent_sleep: bool, prevent_display: bool) -> None:
        set_thread_execution_state(prevent_sleep, prevent_display)
        self._active = prevent_sleep

    def disable(self) -> None:
        if not IS_WINDOWS:
            self._active = False
            return
        try:
            set_thread_execution_state(False, False)
        finally:
            self._active = False
