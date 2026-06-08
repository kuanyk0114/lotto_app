# Supabase 自動更新功能開發成果報告 (Walkthrough)

此文件記錄了針對 `lotto_app` 專案所實作的 Supabase 自動更新開獎獎號功能的變更內容與驗證結果。

## 🛠️ 變更內容 (Changes Made)

本功能透過獨立模組化與背景執行緒設計，實現了非阻塞式的自動更新機制，以下是新增及修改的檔案清單：

### 1. **[NEW] [modules/sync.py](file:///d:/我的專案/台彩程式/lotto_app/modules/sync.py)**
* **功能描述**: 負責底層與 Supabase 連線及 SQLite 資料庫的事務處理。
* **主要實作**:
  * `check_internet()`: 發送 HEAD 請求至 Supabase 連接埠以測試網路狀態，逾時設為 3 秒。
  * `calculate_sha256()`: 計算下載 CSV 位元組的雜湊校驗碼。
  * `SyncManager` 類別:
    * `get_local_version()`: 讀取 SQLite 表中 `updated_data` 記錄的最高版本 `id`。
    * `fetch_remote_updates()`: 查詢 Supabase 獲取所有比本地大的新版本清單（按 `id` 排序）。
    * `download_csv_file()`: 下載增量 CSV 的 bytes 資料。
    * `process_csv_data()`: 解析 CSV 資料，依照 `update_type`（`A`：新增、`U`：替換、`D`：刪除）轉換並執行 SQLite 語法，整個過程被包裝在 `transaction` 中。
    * `save_version_to_local()`: 將完成更新的檔案 `id` 記錄至 SQLite 以供後續追蹤。

### 2. **[NEW] [modules/sync_ui.py](file:///d:/我的專案/台彩程式/lotto_app/modules/sync_ui.py)**
* **功能描述**: 管理 Kivy 前端更新進度視窗、校驗失敗彈窗及背景線程的調度。
* **主要實作**:
  * `SyncProgressPopup`: 進度條與狀態文字彈窗。
  * `RetryConfirmPopup`: 校驗/下載失敗時提示「重新下載」或「略過更新」的雙鈕對話框。
  * `SyncWorker`: 繼承背景 Thread 的工作類，使用 `threading.Event` 來在校驗失敗時暫停執行緒並等待 UI 執行緒的用戶點選回饋。

### 3. **[MODIFY] [main.py](file:///d:/我的專案/台彩程式/lotto_app/main.py)**
* **功能描述**: 串接 App 生命週期。
* **主要實作**:
  * 導入 `sync_ui` 的 UI 元件與執行緒。
  * 在 `on_start()` 生命周期中啟動 `SyncWorker` 背景線程。
  * 提供 `show_retry_popup()`、`update_sync_ui()`、`dismiss_sync_popup()` 與 `reload_history_data()` 方法以接收背景線程對 UI 的狀態更新。

---

## 🧪 驗證與測試結果 (Validation Results)

### 1. Headless 整合測試
透過建立 `scratch/test_sync.py` 腳本對 `modules/sync.py` 進行了獨立測試。
* **測試過程**:
  1. 偵測網路成功 (`Internet status: True`)。
  2. 讀取未更新前版本 (`Local ID: 0`)，向 Supabase 獲取清單，共發現 5 個待更新檔案（版本 1 ~ 5）。
  3. 下載第一個更新檔 `202506.csv`。
  4. 比對 SHA-256 成功（本地計算值與預期值完全相符）。
  5. 寫入 SQLite 成效顯著，成功處理了 92 筆各彩種的開獎資料。
  6. 本地 `updated_data` 更新版號為 `1`。

### 2. GUI 與全流程同步測試
恢復本地資料庫為原始狀態（版本 0），並啟動應用程式跑完完整流程：
* **測試過程**:
  1. 執行 `python -u main.py` 啟動 App。
  2. 畫面上順暢跳出「系統更新」對話框，進度條隨著各 CSV 檔（`202506.csv` 到 `202510.csv`）的下載、校驗、寫入進度逐步更新。
  3. 約 5 秒內更新進度條達到 100% 並顯示「更新完成！」，隨後彈窗自動關閉，進入首頁，全程未發生 UI 卡死。
  4. 經查詢本地 SQLite `updated_data` 表，版本 1 至 5 的紀錄均完整寫入：
     ```python
     [('1', '2026-06-03 09:16:41'), ('2', '2026-06-03 09:16:42'), ('3', '2026-06-03 09:16:43'), ('4', '2026-06-03 09:16:44'), ('5', '2026-06-03 09:16:45')]
     ```
  5. 資料庫各彩種記錄數均成功遞增（以威力彩為例，從 1811 增長至 1855，累積新增 44 期開獎）。
