"""Non-blocking fixed-interval click scheduling for Tkinter."""

from __future__ import annotations

import math
import time
import tkinter as tk
from collections.abc import Callable

from windows_api import click_at


class AutoClicker:
    def __init__(
        self,
        root: tk.Misc,
        on_countdown: Callable[[int | None], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        self._root = root
        self._on_countdown = on_countdown
        self._on_error = on_error
        self._after_id: str | None = None
        self._running = False
        self._x = 0
        self._y = 0
        self._interval = 30
        self._deadline = 0.0
        self._last_displayed: int | None = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self, x: int, y: int, interval_seconds: int) -> None:
        if self._running:
            return
        self._x = x
        self._y = y
        self._interval = interval_seconds
        self._deadline = time.monotonic() + interval_seconds
        self._running = True
        self._last_displayed = None
        self._schedule_tick()

    def stop(self) -> None:
        self._running = False
        if self._after_id is not None:
            try:
                self._root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        self._last_displayed = None
        self._on_countdown(None)

    def _schedule_tick(self) -> None:
        if self._running:
            # A short tick keeps the displayed second accurate without
            # blocking Tkinter or accumulating long-term timer drift.
            self._after_id = self._root.after(100, self._tick)

    def _tick(self) -> None:
        self._after_id = None
        if not self._running:
            return

        remaining = max(0, int(math.ceil(self._deadline - time.monotonic())))
        if remaining != self._last_displayed:
            self._last_displayed = remaining
            self._on_countdown(remaining)

        if time.monotonic() >= self._deadline:
            try:
                click_at(self._x, self._y)
            except Exception as error:  # pragma: no cover - Windows-only path
                self._running = False
                self._on_countdown(None)
                self._on_error(error)
                return
            self._deadline = time.monotonic() + self._interval
            self._last_displayed = None

        self._schedule_tick()
