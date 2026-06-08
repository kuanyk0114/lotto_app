# Android APK 打包與測試任務清單

- `[x]` **1. 輕量化 REST API 重構與打包設定簡化**
    - `[x]` 修改 `modules/sync.py`，移除 `supabase` 導入，並改用 `requests` 實現 Supabase REST 與 Storage API 調用
    - `[x]` 修改 `buildozer.spec` 中的 `requirements`，簡化依賴包清單
- `[/]` **2. 設置編譯環境與執行編譯**
    - `[/]` 將程式碼提交至 GitHub，觸發 GitHub Actions 雲端自動化編譯
    - `[ ]` 下載編譯完成的 APK 檔案
- `[ ]` **3. 安裝與實機功能測試**
    - `[ ]` 將 APK 安裝至實體 Android 手機，檢查是否能正常啟動不閃退
    - `[ ]` 測試並驗證啟動時的 Supabase 資料庫同步功能是否正常運作
    - `[ ]` 測試版本更新提示功能，點擊「前往更新」確認是否可拉起瀏覽器並開啟對應商店連結
    - `[ ]` 進入彩券選號頁面，確認底部橫幅顯示深灰色的模擬廣告版位且高寬比例合適
