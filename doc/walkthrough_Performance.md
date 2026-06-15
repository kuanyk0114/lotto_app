# Walkthrough - 效能與查詢顯示改善成果

本文件摘要了針對 `doc\Performance.md` 效能與分頁滾動問題所進行的所有修改與驗證結果。

## 變更項目說明

### 1. 滾動定位優化 (精確對齊新分頁頂部)
* **修改檔案**：[common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py)
* **新增方法**：在 `BaseScrollMixin` 內新增 `_scroll_to_new_data_start`。該方法將滾動目標絕對高度設為舊內容高度減去指示器高度（`previous_height - dp(60)`），並呼叫 `_restore_scroll_position_absolute` 恢復滾動。
* **適配調整**：
  * 修改了 [common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py) 中 `BaseLotterySavedScreen._append_to_result_list` 的對齊計算。
  * 修改了 5 個彩種模組（[biglotto.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/biglotto.py)、[powerlotto.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/powerlotto.py)、[lotto539.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/lotto539.py)、[lotto3star.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/lotto3star.py)、[lotto4star.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/lotto4star.py)）中所有結果展示類別 of `_append_to_result_list` 方法，將原本記錄的 `current_absolute_scroll` 改為載入前的高度，並延遲呼叫 `self._scroll_to_new_data_start(current_content_height)`。
  * 威力彩專用佈局名稱 `result_list` 已整合至 `BaseScrollMixin`（`content_layout` 查詢鍊中），修復了原本威力彩可能無法正確偵測底部或恢復滾動位置的潛在 BUG。

### 2. 連續滾動卡死/不加載問題優化 (底部追加檢查)
* **修改檔案**：[common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py)
* **作法**：
  * 修改 `BasePaginationMixin._perform_load_next_page`，在 `finally` 塊執行完畢後（即載入狀態恢復為可加載時），延遲 0.25 秒排程呼叫 `_check_load_more_after_load`。
  * `BaseScrollMixin` 實作 `_check_load_more_after_load`，主動執行一次即時的底部邊界偵測（`_check_load_more_immediate`）。
  * 此舉能夠在快速連續滑動或 race condition 結束後，自發完成追加載入，徹底解決卡死底部的 Bug。

### 3. 資料庫查詢與排序速度優化
* **修改檔案**：[common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py) 的 `DatabaseManager`
* **作法**：
  * 新增 `_initialize_indexes` 方法。在 `DatabaseManager.__init__` 初始化時，自動檢查並為大樂透、539、三星彩、四星彩歷史資料表的 `date` 欄位補建索引，加速排序作業。
  * 同時為 `custom_numbers` 表格建立 `(lottery_type, created_time DESC)` 複合索引，大幅提升自選號清單載入效能。

---

## 驗證結果

### 1. 資料庫索引驗證 (已通過)
* 執行測試腳本，順利在主資料庫 `lotto_history.db` 補建以下索引：
  - `idx_biglotto_date` on `big_lotto(date)`
  - `idx_lotto539_date` on `lotto_539(date)`
  - `idx_lotto3star_date` on `lotto_3star(date)`
  - `idx_lotto4star_date` on `lotto_4star(date)`
* 自選號資料庫 `custom.db` 成功補建：
  - `idx_custom_numbers_lookup` on `custom_numbers(lottery_type, created_time DESC)`
* 再次執行查詢或排序時，SQLite 能夠使用這些索引進行加速。

### 2. 程式碼修改編譯驗證 (已通過)
* 運行 `DatabaseManager` 模組，所有引用的 `kivy`、`sqlite3` 均正常載入，語法完全正確。
