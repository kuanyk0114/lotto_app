# 05 API 文檔 (lotto_app)

本文件詳細說明 `lotto_app` 專案內部 Python 模組類別介面 API 以及外部 Supabase REST API 通訊協定。

---

## 🐍 1. 內部 Python 模組核心 API

### 1.1 `modules/common.py`

#### `BasePaginationMixin` (分頁邏輯基類)
提供所有彩種 Screen 類別繼承，負責動態分頁展示與滾動位置管理。
* **屬性 (Properties)**：
  - `current_page` (NumericProperty): 當前載入頁碼（從 0 開始）。
  - `page_size` (NumericProperty): 每頁載入筆數，預設為 30 筆。
  - `all_results` (ListProperty): 完整查詢結果清單。
  - `displayed_results` (ListProperty): 當前畫面已渲染的結果清單。
  - `has_more_data` (BooleanProperty): 是否尚有未載入的資料。
* **核心方法**：
  - `_initialize_pagination()`: 初始化分頁參數並重置滾動位置。
  - `load_more_data()`: 觸發加載下一頁資料並更新 UI。
  - `_restore_scroll_position_absolute(target_absolute_scroll, scroll_view)`: 根據絕對距離精確恢復滾動位置。

#### `LotteryTypeScreen(Screen)` (主畫面控制類)
* **方法**：
  - `show_privacy_policy()`: 彈出隱私權政策與法律免責聲明視窗，動態讀取並渲染 `隱私權政策及免責聲明/服務條款與法律免責聲明隱私權政策.md`。

---

### 1.2 彩種業務模組類別 (如 `PowerLottoScreen`, `BigLottoScreen`, `Lotto539Screen`)

各彩種畫面類別皆實現以下統一的核心業務方法：

* `query_numbers()`
  - **描述**：讀取使用者在選號盤上選取的號碼，執行 SQL 比對查詢包含該號碼組合的歷史紀錄。
  - **輸入**：UI 選中號碼狀態。
  - **輸出**：更新 `all_results` 並觸發分頁渲染。

* `show_duplicate_numbers()`
  - **描述**：執行歷史開開獎重複號碼分析（如威力彩/大樂透 6 碼重複、539 5 碼重複）。
  - **輸出**：彈出重複號碼統計清單。

* `check_details()`
  - **描述**：比對選滿之注數在歷史各期的詳細中獎情況與金額。
  - **驗證**：若號碼數量未選滿，自動調用 `show_popup` 提示使用者選滿號碼。

* `save_custom_numbers()`
  - **描述**：將當前選號盤號碼寫入 `data/custom.db` 的 `custom_numbers` 表格。

* `load_custom_numbers()`
  - **描述**：讀取 `custom.db` 歷史儲存號碼，彈出視窗供使用者點選帶入或長按刪除。

---

## ☁️ 2. 外部 Supabase REST API 通訊協定

App 透過 HTTP REST API 與 Supabase 雲端後端進行資料增量同步與版本比對。

* **基底 URL**：`https://wyyiyuinfgbqbeykenin.supabase.co`
* **驗證標頭 (Headers)**：
  - `apikey: sb_publishable_WKf4yO8K_3xP6q---1j-Ww_emFIPiXe`
  - `Authorization: Bearer sb_publishable_WKf4yO8K_3xP6q---1j-Ww_emFIPiXe`

---

### 2.1 查詢可更新檔案清單

* **端點**：`GET /rest/v1/data_list`
* **查詢參數**：`select=*&order=created_at.asc`
* **響應範例 (JSON)**：
```json
[
  {
    "id": "20240625_01",
    "file_name": "lotto_update_20240625.csv",
    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "update_type": "A",
    "created_at": "2024-06-25T18:00:00Z"
  }
]
```

---

### 2.2 下載開獎號碼 CSV 增量檔案

* **端點**：`GET /storage/v1/object/public/lotto_new_number/{file_name}`
* **響應格式**：`text/csv`
* **CSV 內容資料結構**：
```csv
遊戲名稱,期別,開獎日期,銷售總額,銷售注數,總獎金,獎號1,獎號2,獎號3,獎號4,獎號5,獎號6,第二區
威力彩,113000051,2024-06-24,85420100,427100,210000000,1,8,14,27,30,35,2
```

---

### 2.3 App 版本號檢測

* **端點**：`GET /rest/v1/app_ver`
* **查詢參數**：`select=*&order=ver_date.desc&limit=1`
* **響應範例 (JSON)**：
```json
[
  {
    "ver_num": "1.1.0",
    "ver_date": "2024-06-26"
  }
]
```
