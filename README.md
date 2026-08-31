# 防休眠與自動點擊工具

KeepAwakeClicker 是一個適用於 Windows 10 x64 與 Windows 11 x64 的桌面工具，使用 Tkinter 與 Windows API 提供防休眠及固定位置自動點擊功能。

## 使用方式

執行 `KeepAwakeClicker.exe` 後，可以設定：

- 防止電腦進入睡眠
- 防止螢幕自動關閉
- 固定滑鼠點擊位置與點擊間隔
- 以「取得目前滑鼠位置」或全域快捷鍵 F8 記錄座標

按下「開始」後，程式使用 Windows `SetThreadExecutionState` 維持電源狀態，並使用 `SetCursorPos` 與 `SendInput` 執行固定位置左鍵點擊。按下「停止」或 `Ctrl+Shift+F12` 會取消排程並完整恢復電源狀態。

座標使用 Windows 虛擬桌面座標，因此支援多螢幕、負座標與 Windows DPI Scaling。程式不會自行換算座標比例。

設定檔位置：

```text
%APPDATA%\\KeepAwakeClicker\\settings.json
```

## 本機開發

程式本身只使用 Python 標準函式庫；打包工具使用 PyInstaller。建議使用 Python 3.12。

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
