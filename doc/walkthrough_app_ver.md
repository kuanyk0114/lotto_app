# App 版本檢查與更新提示開發成果報告 (Walkthrough)

此文件記錄了針對 `lotto_app` 專案所實作的啟動時程式版本比對及更新提示功能的變更內容與驗證結果。

## 🛠️ 變更內容 (Changes Made)

我們在既有的 Supabase 資料庫同步更新流程中，新增了程式版本的檢查：

### 1. **[MODIFY] [modules/sync.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/sync.py)**
* 新增了兩個方法：
  * `get_local_app_version()`: 讀取本地 SQLite 歷史庫中的 `app_ver` 資料表，以取得當前程式版本號（預設為 `1.0`）。
  * `fetch_remote_app_version()`: 透過 Supabase 客戶端獲取 `app_ver` 表中的所有版本資料，並依日期（`ver_date`）降序排列取得最新的版本號。

### 2. **[MODIFY] [modules/sync_ui.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/sync_ui.py)**
* 新增了 `AppUpdatePopup` 類別，該彈窗將在偵測到新版本時顯示，帶有「稍後」與「前往更新」的選項。
* 新增了 `is_newer_version(local, remote)` 函數，支援點分隔版本號（例如 `0.9` < `1.0`）的精準比對。
* 在 `SyncWorker.run()` 啟動流程中加入版本檢查邏輯。若偵測到更新，會觸發 `ask_user_update(remote_ver)` 來暫停背景執行緒，並調度主執行緒開啟 `AppUpdatePopup`。
* 導入並使用 `modules/common.py` 中的 `get_store_url()`，將下載連結由原先硬編碼的 Google Play 改為根據運行平台（Android / iOS）動態獲取的自適應網址。

### 3. **[MODIFY] [main.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/main.py)**
* 導入了 `AppUpdatePopup`。
* 實作了 `show_update_popup()`，供 `SyncWorker` 安全地在主執行緒彈出版本更新視窗。

---

## 🧪 驗證與測試 (Validation & Testing)

1. **版本模擬**: 
   * 我們透過指令將本地 `app_ver` 資料庫欄位更新為較舊的 `'0.9'` 版本（Supabase 上的最新版本為 `'1.0'`）。
2. **啟動 APP**: 
   * 執行 `python main.py` 啟動 APP，系統將連線 Supabase 並偵測到遠端有新版本 `1.0`。
   * **結果**: 畫面會跳出「有新版本發佈」提示視窗，顯示新版本資訊。
3. **按鈕行為**:
   * **點擊「稍後」**: 關閉更新彈窗，系統順暢執行後續的歷史獎號同步並進入首頁。
   * **點擊「前往更新」**: 關閉更新彈窗，自動開啟瀏覽器依當前運作平台跳轉至正確的應用程式商店（Android 開啟 Google Play，iOS 開啟 App Store，其餘桌面平台開啟預設網址），並正常執行後續同步並進入首頁。
