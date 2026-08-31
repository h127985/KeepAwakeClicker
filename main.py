"""Application entry point for KeepAwakeClicker."""

from __future__ import annotations

import tkinter as tk

from ui import KeepAwakeClickerApp
from windows_api import set_per_monitor_dpi_awareness


def main() -> None:
    set_per_monitor_dpi_awareness()
    root = tk.Tk()
    KeepAwakeClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
