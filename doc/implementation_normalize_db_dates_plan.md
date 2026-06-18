# 資料庫日期格式標準化與查詢索引優化計劃

此計劃旨在解決資料庫中 `date` 欄位未補零導致 SQLite 字串排序錯亂的問題，並透過標準化日期格式與建立索引，提升開獎號碼查詢的效能。

## 待解決的問題

1. **日期排序錯亂**：資料庫中存在非補零日期字串（如 `2008/1/24`、`2007/1/2`），導致 SQLite 使用 `ORDER BY date DESC` 時會產生錯誤的字串排序結果。
2. **缺少威力彩索引**：`DatabaseManager` 中的 `_initialize_indexes` 初始化方法未幫 `power_lotto` 的 `date` 欄位建立索引。
3. **未發揮索引效能**：`recentprize.py` 因為日期未標準化，只能在 Python 端全表讀取並進行排序與 `LIMIT 30` 截取，耗費額外的記憶體和 CPU。

---

## 預期變更

### 1. 資料庫日期格式遷移 (Migration)
* 撰寫一次性的資料庫更新腳本 `scratch/normalize_db_dates.py`：
  * 讀取五大彩種表（`power_lotto`, `big_lotto`, `lotto_539`, `lotto_3star`, `lotto_4star`）中的所有 `date` 欄位。
  * 將非標準的日期（例如 `2008/1/2` 或 `2008-1-2`）統一轉換為補零的 `YYYY/MM/DD` 格式（例如 `2008/01/02`）。
  * 將變更寫回資料庫。

### 2. 補上威力彩資料庫索引
#### [MODIFY] [common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py)
* 在 `_initialize_indexes` 方法中的 `index_queries` 列表中，補上威力彩的 `date` 索引建置語句：
  ```sql
  "CREATE INDEX IF NOT EXISTS idx_powerlotto_date ON power_lotto(date);"
  ```

### 3. 優化近期獎號查詢
#### [MODIFY] [recentprize.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/recentprize.py)
* 修改 `load_recent_prizes` 查詢語句，直接在 SQL 中完成排序與分頁：
  ```sql
  SELECT issue, date, {cols} FROM {table} ORDER BY date DESC, issue DESC LIMIT 30
  ```
* 移除 Python 端手動全表載入、解析 `datetime` 與排序的邏輯，直接讀取這 30 筆已經排好序的資料渲染 UI。

---

## 驗證計劃

### 手動驗證
1. 執行遷移腳本，檢查資料庫中的日期是否皆正確轉換為 10 位數的 `YYYY/MM/DD` 格式。
2. 啟動應用程式，切換至「近期獎號查詢」畫面，確認威力彩、大樂透、今彩 539、3星彩、4星彩的近 30 期獎號順序是否完全正確，且無資料缺失。
3. 檢查 log，確認 `DatabaseManager` 能成功建立威力彩的 `idx_powerlotto_date` 索引。
