"""Tkinter user interface for KeepAwakeClicker."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from auto_clicker import AutoClicker
from hotkeys import HOTKEY_EMERGENCY_STOP, HOTKEY_RECORD_POSITION, HotkeyManager
from keep_awake import KeepAwakeController
from settings import load_settings, save_settings
from windows_api import get_cursor_pos


class KeepAwakeClickerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("防休眠與自動點擊工具")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        values = load_settings()
        self.prevent_sleep = tk.BooleanVar(value=values["prevent_sleep"])
        self.prevent_display = tk.BooleanVar(value=values["prevent_display"])
        self.auto_click = tk.BooleanVar(value=values["auto_click"])
        self.x_value = tk.StringVar(value=str(values["x"]))
        self.y_value = tk.StringVar(value=str(values["y"]))
        self.interval_value = tk.StringVar(value=str(values["interval"]))
        self.status_value = tk.StringVar(value="已停止")
        self.next_click_value = tk.StringVar(value="--")

        self.keep_awake = KeepAwakeController()
        self.auto_clicker = AutoClicker(root, self._update_countdown, self._click_error)
        self.hotkeys = HotkeyManager()
        self._closing = False

        self._build_ui()
        hotkey_errors = self.hotkeys.start(
            root,
            {
                HOTKEY_RECORD_POSITION: self.record_current_position,
                HOTKEY_EMERGENCY_STOP: self.emergency_stop,
            },
        )
        if hotkey_errors:
            self.root.after(100, lambda: self._show_hotkey_warning(hotkey_errors))

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        power_frame = ttk.LabelFrame(frame, text="電源設定", padding=10)
        power_frame.grid(row=0, column=0, sticky="ew")
        ttk.Checkbutton(
            power_frame,
            text="防止電腦進入睡眠",
            variable=self.prevent_sleep,
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            power_frame,
            text="防止螢幕自動關閉",
            variable=self.prevent_display,
        ).grid(row=1, column=0, sticky="w")

        click_frame = ttk.LabelFrame(frame, text="自動點擊", padding=10)
        click_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        self.auto_click_checkbutton = ttk.Checkbutton(
            click_frame,
            text="啟用自動點擊",
            variable=self.auto_click,
        )
        self.auto_click_checkbutton.grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(click_frame, text="點擊位置").grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 3))
        ttk.Label(click_frame, text="X：").grid(row=2, column=0, sticky="e")
        self.x_entry = ttk.Entry(click_frame, width=12, textvariable=self.x_value)
        self.x_entry.grid(row=2, column=1, sticky="w")
        ttk.Label(click_frame, text="Y：").grid(row=2, column=2, sticky="e", padx=(10, 0))
        self.y_entry = ttk.Entry(click_frame, width=12, textvariable=self.y_value)
        self.y_entry.grid(row=2, column=3, sticky="w")

        self.position_button = ttk.Button(
            click_frame,
            text="取得目前滑鼠位置",
            command=self.record_current_position,
        )
        self.position_button.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        ttk.Label(click_frame, text="點擊間隔").grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 3))
        ttk.Label(click_frame, text="每").grid(row=5, column=0, sticky="e")
        self.interval_entry = ttk.Entry(click_frame, width=12, textvariable=self.interval_value)
        self.interval_entry.grid(row=5, column=1, sticky="w")
        ttk.Label(click_frame, text="秒點擊一次").grid(row=5, column=2, columnspan=2, sticky="w", padx=(6, 0))

        button_frame = ttk.Frame(click_frame)
        button_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        self.start_button = ttk.Button(button_frame, text="開始", command=self.start)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        status_frame = ttk.Frame(frame)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(status_frame, text="狀態：").grid(row=0, column=0, sticky="w")
        ttk.Label(status_frame, textvariable=self.status_value).grid(row=0, column=1, sticky="w")
        ttk.Label(status_frame, text="下次點擊：").grid(row=1, column=0, sticky="w")
        ttk.Label(status_frame, textvariable=self.next_click_value).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="F8：記錄目前滑鼠位置").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Label(frame, text="Ctrl+Shift+F12：緊急停止").grid(row=4, column=0, sticky="w", pady=(3, 0))

    def _show_hotkey_warning(self, errors: list[str]) -> None:
        if not self._closing:
            messagebox.showwarning("快捷鍵提醒", "\n".join(errors), parent=self.root)

    def _parse_integer(self, value: str, field_name: str) -> int | None:
        try:
            parsed = int(value.strip())
        except (AttributeError, TypeError, ValueError):
            if field_name == "interval":
                messagebox.showerror("輸入錯誤", "請輸入有效的點擊間隔。", parent=self.root)
            else:
                messagebox.showerror("輸入錯誤", "請輸入有效的滑鼠座標。", parent=self.root)
            return None

        if not -(2**31) <= parsed <= 2**31 - 1:
            if field_name == "interval":
                messagebox.showerror("輸入錯誤", "請輸入有效的點擊間隔。", parent=self.root)
            else:
                messagebox.showerror("輸入錯誤", "請輸入有效的滑鼠座標。", parent=self.root)
            return None
        if field_name == "interval" and parsed < 1:
            messagebox.showerror("輸入錯誤", "點擊間隔至少需要 1 秒。", parent=self.root)
            return None
        return parsed

    def _read_values(self) -> tuple[int, int, int] | None:
        x = self._parse_integer(self.x_value.get(), "x")
        y = self._parse_integer(self.y_value.get(), "y")
        interval = self._parse_integer(self.interval_value.get(), "interval")
        if x is None or y is None or interval is None:
            return None
        return x, y, interval

    def start(self) -> None:
        values = self._read_values()
        if values is None:
            return
        x, y, interval = values

        try:
            self.keep_awake.apply(self.prevent_sleep.get(), self.prevent_display.get())
            if self.auto_click.get():
                self.auto_clicker.start(x, y, interval)
            else:
                self.next_click_value.set("--")
        except Exception as error:
            self.auto_clicker.stop()
            self.keep_awake.disable()
            messagebox.showerror("啟動失敗", str(error), parent=self.root)
            return

        self.status_value.set("執行中")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.x_entry.configure(state="disabled")
        self.y_entry.configure(state="disabled")
        self.interval_entry.configure(state="disabled")
        self.auto_click_checkbutton.configure(state="disabled")

    def stop(self) -> None:
        self._stop_all()

    def emergency_stop(self) -> None:
        if not self._closing:
            self._stop_all()

    def _stop_all(self) -> None:
        self.auto_clicker.stop()
        self.keep_awake.disable()
        self.status_value.set("已停止")
        self.next_click_value.set("--")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.x_entry.configure(state="normal")
        self.y_entry.configure(state="normal")
        self.interval_entry.configure(state="normal")
        self.auto_click_checkbutton.configure(state="normal")

    def _update_countdown(self, remaining: int | None) -> None:
        self.next_click_value.set("--" if remaining is None else f"{remaining} 秒")

    def _click_error(self, error: Exception) -> None:
        self._stop_all()
        messagebox.showerror("自動點擊失敗", str(error), parent=self.root)

    def record_current_position(self) -> None:
        try:
            x, y = get_cursor_pos()
        except Exception as error:
            if not self._closing:
                messagebox.showerror("取得位置失敗", str(error), parent=self.root)
            return
        self.x_value.set(str(x))
        self.y_value.set(str(y))

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.auto_clicker.stop()
        self.hotkeys.stop()
        self.keep_awake.disable()
        try:
            save_settings(
                {
                    "prevent_sleep": self.prevent_sleep.get(),
                    "prevent_display": self.prevent_display.get(),
                    "auto_click": self.auto_click.get(),
                    "x": self._safe_setting_int(self.x_value.get(), 0),
                    "y": self._safe_setting_int(self.y_value.get(), 0),
                    "interval": self._safe_setting_int(self.interval_value.get(), 30, minimum=1),
                }
            )
        finally:
            self.root.destroy()

    @staticmethod
    def _safe_setting_int(value: str, fallback: int, minimum: int = -(2**31)) -> int:
        try:
            parsed = int(value.strip())
            if minimum <= parsed <= 2**31 - 1:
                return parsed
        except (AttributeError, TypeError, ValueError):
            pass
        return fallback
