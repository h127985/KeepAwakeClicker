# 防休眠與自動點擊工具

KeepAwakeClicker 是一個適用於 Windows 10 x64 與 Windows 11 x64 的桌面工具，使用 Tkinter 與 Windows API 提供防休眠及固定位置自動點擊功能。

## 使用方式

從 [GitHub Releases](https://github.com/h127985/KeepAwakeClicker/releases) 下載 `KeepAwakeClicker.exe`，在 Windows 10 x64 或 Windows 11 x64 直接執行，不需要另行安裝 Python 或 .NET。

執行 `KeepAwakeClicker.exe` 後，可以設定：

- 防止電腦進入睡眠
- 防止螢幕自動關閉
- 固定滑鼠點擊位置與點擊間隔
- 以「取得目前滑鼠位置」或全域快捷鍵 F8 記錄座標

按下「開始」後，程式使用 Windows `SetThreadExecutionState` 維持電源狀態，並使用 `SetCursorPos` 與 `SendInput` 執行固定位置左鍵點擊。按下「停止」或 `Ctrl+Shift+F12` 會取消排程並完整恢復電源狀態。

座標使用 Windows 虛擬桌面座標，因此支援多螢幕、負座標與 Windows DPI Scaling。程式不會自行換算座標比例。

設定檔位置：

```text
%APPDATA%\KeepAwakeClicker\settings.json
```

## 本機開發

程式本身只使用 Python 標準函式庫；打包工具使用 PyInstaller。建議使用 Python 3.12。

以下 EXE 打包指令必須在 Windows 執行；macOS 可編輯原始碼，並使用 GitHub Actions 建置 Windows 版本。

```bash
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name KeepAwakeClicker main.py
```

輸出檔案會位於：

```text
dist/KeepAwakeClicker.exe
```

## GitHub Actions

`.github/workflows/build-windows.yml` 會在推送到 `main` 或手動觸發時，使用 `windows-latest` 與 Python 3.12 建立 Windows x64 EXE，並上傳 `KeepAwakeClicker-Windows-x64` Artifact。

## Roadmap

KeepAwakeClicker is currently an early-stage project. Planned areas of development include:

- Improve automated testing and regression coverage
- Improve multi-monitor and DPI behavior validation
- Expand configurable hotkeys and input actions
- Improve application lifecycle and error handling
- Provide pre-built Windows releases
- Explore cross-device keyboard/mouse control and KVM-related functionality

The longer-term goal is to evolve the project from a lightweight keep-awake and auto-click utility into a more general open-source desktop input automation tool.

跨裝置控制與 KVM 目前僅為探索方向，尚未實作。預先建置的 Windows 版本將透過上述 Releases 頁面提供。

## 授權

本專案採用 [MIT License](LICENSE)。Copyright (c) 2026 h127985。
