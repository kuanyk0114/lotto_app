# Supabase 自動更新開獎獎號實作計畫

此計畫旨在為 `lotto_app` 實作啟動時自動連線 Supabase 伺服器，下載並更新歷史開獎獎號（包含威力彩、大樂透、今彩539、3星彩、4星彩）的功能。

## 使用者審查需求

> [!IMPORTANT]
> **1. 線程安全與 UI 非阻塞設計**
> 網路連線與資料庫更新均為耗時操作。為了避免 Kivy 畫面凍結，本實作將使用 **Python 執行緒 (Threading)** 在背景執行更新，並透過 `kivy.clock.Clock` 將更新進度、失敗重試彈窗安全地投遞至主 UI 執行緒。
>
> **2. 更新資料的正確性驗證**
> 下載的 CSV 檔案將在本地計算 **SHA-256 總和校驗碼**，並與 Supabase `data_list.checksum` 比對。若不符將觸發 Kivy 詢問彈窗供使用者決定是否重試，確保本地 SQLite 的資料一致性。
>
> **3. 交易安全性 (Transaction Safety)**
> 為了防範更新途中遭遇斷電或異常中斷導致資料庫損毀，CSV 寫入本地 SQLite 將在同一交易 (Transaction) 中執行，出錯時自動執行 `rollback()`。

---

## 預計修改與新增的檔案

### 1. [NEW] [sync.py](file:///d:/我的專案/台彩程式/lotto_app/modules/sync.py)
負責網路偵測、連接 Supabase、下載 CSV、SHA-256 驗證及解析 CSV 寫入 SQLite。

### 2. [MODIFY] [main.py](file:///d:/我的專案/台彩程式/lotto_app/main.py)
在 App 啟動的 `on_start()` 生命週期中掛載更新背景線程，並呼叫對應的 UI 進度與提示 Popup。

---

## 詳細實作步驟

### 1. 建立同步模組：`modules/sync.py`

此模組將包含以下功能：
* **`check_internet()`**: 發送輕量級 HTTP HEAD 請求至 Supabase URL，設定 timeout 為 3 秒，若失敗則判定為無網路。
* **`calculate_sha256(data_bytes)`**: 計算下載位元組的 SHA-256 雜湊值。
* **`SyncManager` 類別**:
  * 屬性：`db_path` (本地歷史資料庫路徑)、`supabase_url`、`supabase_key`、`bucket_id`。
  * **`get_local_version()`**: 讀取本地 `updated_data` 表的最新 `id`（若表為空或不存在，回傳 `0`）。
  * **`fetch_remote_updates(local_id)`**: 初始化 Supabase 客戶端，查詢 `data_list` 中 `id` 大於 `local_id` 的所有記錄，按 `id` 升序排列。
  * **`download_csv_file(file_name)`**: 從 Supabase Storage 的 `lotto_new_number` 下載指定 CSV 檔案的 bytes。
  * **`process_csv_data(csv_data_bytes, update_type)`**:
    * 解碼為 `utf-8-sig`（處理 BOM）並利用 `csv.reader` 讀取每行資料。
    * 根據「遊戲名稱」過濾空行與欄位長度：
      * `威力彩`: `power_lotto`，13個欄位
      * `大樂透`: `big_lotto`，13個欄位（特別號為 13 欄）
      * `今彩539`: `lotto_539`，11個欄位
      * `三星彩`: `lotto_3star`，9個欄位
      * `四星彩`: `lotto_4star`，10個欄位
    * 根據 `update_type` 生成 SQL 語法：
      * **`A` (新增)**: `INSERT OR IGNORE INTO {table} (...) VALUES (...)`
      * **`U` (更新/替換)**: `INSERT OR REPLACE INTO {table} (...) VALUES (...)`（利用 `issue` 的 UNIQUE 限制覆寫舊資料）
      * **`D` (刪除)**: `DELETE FROM {table} WHERE issue = ?`
  * **`save_version_to_local(version_id)`**: 將成功的檔案 `id` 與目前時間寫入本地 `updated_data` 表。

### 2. 擴充主程式啟動流程：`main.py`

* 導入 `modules.sync` 中建立的 `SyncManager`、`check_internet`。
* 新增 `on_start(self)` 方法，延遲 0.2 秒啟動背景更新任務（避免畫面初始化與連線卡在一起）。
* **UI 回饋機制實作**:
  * 建立更新專用的 Kivy Popup，顯示「正在偵測網路...」、「正在下載 [檔案名稱]...」、「正在校驗 SHA-256...」、「正在更新資料庫...」等狀態。
  * 當校驗失敗時，透過線程同步物件（如 `threading.Event`）將背景線程暫停，彈出詢問 Popup。
    * 使用者點選 **是**: 事件解鎖，重試下載。
    * 使用者點選 **否**: 中斷更新流程，解鎖背景線程，關閉更新 Popup，進入主畫面。

---

## 資料結構對照與防錯

### CSV 欄位對應資料庫一覽
| 彩券類型 | 英文識別 | SQLite 資料表 | CSV 欄位數量 | 欄位列表 |
| :--- | :--- | :--- | :---: | :--- |
| **威力彩** | `power` | `power_lotto` | 13 | 遊戲名稱, 期別, 開獎日期, 銷售總額, 銷售注數, 總獎金, 獎號1~6, 第二區 |
| **大樂透** | `big` | `big_lotto` | 13 | 遊戲名稱, 期別, 開獎日期, 銷售總額, 銷售注數, 總獎金, 獎號1~6, 特別號 (special_num) |
| **今彩539** | `539` | `lotto_539` | 11 | 遊戲名稱, 期別, 開獎日期, 銷售總額, 銷售注數, 總獎金, 獎號1~5 |
| **三星彩** | `3star` | `lotto_3star` | 9 | 遊戲名稱, 期別, 開獎日期, 銷售總額, 銷售注數, 總獎金, 佰位, 拾位, 個位 |
| **四星彩** | `4star` | `lotto_4star` | 10 | 遊戲名稱, 期別, 開獎日期, 銷售總額, 銷售注數, 總獎金, 仟位, 佰位, 拾位, 個位 |

---

## 驗證計畫

### 1. 網路斷線驗證
* 拔除網路線/關閉 Wi-Fi 啟動 App，確認是否會立刻略過更新、順暢進入主選單，且不彈出 any 網路報錯。

### 2. 正常更新驗證
* 連接網路，將本地 `updated_data` 表的記錄清空或設為較低版本（例如 `id` 設為空）。
* 啟動 App，確認會依序下載 `202506.csv` ~ `202510.csv`，顯示下載與寫入進度，最終自動進入主程式。
* 進入主程式後，分別查詢各彩種，確認各彩種最新開獎日期已成功推進至 **2025 年 10 月**。
* 確認本地 SQLite 的 `updated_data` 中，最新版本 `id` 已被寫入為 `5`。

### 3. 校驗碼失敗重試驗證
* 在代碼中模擬 SHA-256 驗證失敗的情況。
* 確認 App 會跳出對話框問「是否重新下載？」。
* 點選「否」：確認立即中斷更新，順暢進入主畫面。
* 點選「是」：確認重新執行下載該檔，若校驗通過則繼續完成更新。
