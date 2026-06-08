# Android APK 打包與測試任務清單

- `[x]` **1. 建立設定與打包配置文件**
    - `[x]` 建立 `buildozer.spec` 並配置專案依賴包（Kivy, Supabase, Requests 等）與網路權限
    - `[x]` 建立 `.github/workflows/android.yml`（若選擇 GitHub Actions 自動化打包方案）
- `[/]` **2. 設置編譯環境與執行編譯**
    - `[ ]` 在編譯環境（WSL/Ubuntu 或 GitHub Actions 雲端容器）中安裝編譯所需的 Linux 系統依賴庫與 JDK 17
    - `[ ]` 執行 Buildozer 初始化並下載 Android SDK/NDK
    - `[ ]` 執行 `buildozer android debug` 進行 APK 編譯打包，並取得最終安裝包
- `[ ]` **3. 安裝與實機功能測試**
    - `[ ]` 將 APK 安裝至實體 Android 手機，檢查是否能正常啟動不閃退
    - `[ ]` 測試並驗證啟動時的 Supabase 資料庫同步功能是否正常運作
    - `[ ]` 測試版本更新提示功能，點擊「前往更新」確認是否可拉起瀏覽器並開啟對應商店連結
    - `[ ]` 進入彩券選號頁面，確認底部橫幅顯示深灰色的模擬廣告版位且高寬比例合適
