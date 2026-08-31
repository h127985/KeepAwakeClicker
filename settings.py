"""Persistent user settings stored under the Windows roaming profile."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    "prevent_sleep": True,
    "prevent_display": True,
    "auto_click": False,
    "x": 0,
    "y": 0,
    "interval": 30,
}

MIN_INT32 = -(2**31)
MAX_INT32 = 2**31 - 1


def settings_path() -> Path:
    app_data = os.environ.get("APPDATA")
    if app_data:
        base = Path(app_data)
    else:
        base = Path.home() / "AppData" / "Roaming"
    return base / "KeepAwakeClicker" / "settings.json"


def _valid_int(value: Any, minimum: int = MIN_INT32, maximum: int = MAX_INT32) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum


def _normalise(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return DEFAULT_SETTINGS.copy()

    result = DEFAULT_SETTINGS.copy()
    for key in ("prevent_sleep", "prevent_display", "auto_click"):
        if isinstance(raw.get(key), bool):
            result[key] = raw[key]
    for key in ("x", "y"):
        if _valid_int(raw.get(key)):
            result[key] = raw[key]
    if _valid_int(raw.get("interval"), minimum=1):
        result["interval"] = raw["interval"]
    return result


def load_settings() -> dict[str, Any]:
    try:
        with settings_path().open("r", encoding="utf-8") as file:
            return _normalise(json.load(file))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()


def save_settings(values: dict[str, Any]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _normalise(values)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temporary.replace(path)
