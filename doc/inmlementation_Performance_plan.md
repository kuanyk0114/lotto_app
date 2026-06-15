# lotto_app 效能與查詢顯示改善計劃

本計劃針對 `doc\Performance.md` 提出的效能與分頁顯示問題，規劃了完整的優化方案。

## User Review Required

> [!IMPORTANT]
> **滾動對齊方式已確認**：
> 當加載下一分頁時，畫面將**自動滾動至新載入分頁的第一筆資料頂部**（即前一頁的底端會剛好滾出畫面頂部），讓用戶清晰、直接地閱讀新加載的號碼，此行為已與您確認。

> [!TIP]
> **資料庫索引優化**：
> 雖然歷史開獎資料庫每表筆數不多（最大約 5,800 筆），但由於目前大樂透、539、三星彩、四星彩表格皆缺乏 `date` 索引，排序（`ORDER BY date DESC`）時會觸發全表記憶體排序。
> 本計劃將在 APP 啟動時自動為相關表格的 `date` 欄位補建索引，並為自選號表格建立複合索引。

---

## Proposed Changes

### 1. 基礎滾動與分頁機制 (Kivy GUI 核心優化)

#### [MODIFY] [modules/common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py)
* **優化分頁位置對齊**：
  * 在 `BaseScrollMixin` 內新增 `_scroll_to_new_data_start(self, previous_height)` 方法。當載入新頁面時，將目標絕對滾動距離精確設為 `previous_height - dp(60)`（扣除原載入指示器高度後的舊資料底部），並調用 `_restore_scroll_position_absolute` 進行精準定位。
  * 修改 `BaseLotterySavedScreen._append_to_result_list`，使其在載入新分頁後將滾動位置恢復到 `content_height_before - dp(60)`。
* **解決連續滑動卡死問題**：
  * 在 `BasePaginationMixin._perform_load_next_page` 的 `finally` 區塊結尾，使用 `Clock.schedule_once` 在 0.25 秒後（即滾動位置恢復完成後）自動觸發一次額外的底部檢查 `_check_load_more_after_load()`。
  * 在 `BaseScrollMixin` 實作 `_check_load_more_after_load`，主動偵測是否仍處於接近底部狀態，若是則自動補載入下一頁。這將徹底解決快速連續滑動或 race condition 導致畫面卡在底部不加載的 Bug。

---

### 2. 各彩種結果顯示頁面 (適配全新滾動定位)

在以下所有結果頁面的 `_append_to_result_list` 方法中，將原本恢復滾動位置的邏輯，改為記錄載入前的內容高度並調用 `_scroll_to_new_data_start`。

#### [MODIFY] [modules/biglotto.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/biglotto.py)
* 修改 `BigLottoResultsScreen`, `BigLottoRepeatedNumbersScreen`, `BigLottoDuplicateDetailScreen`, `BigLottoWinningDetailsScreen` 的 `_append_to_result_list`。

#### [MODIFY] [modules/powerlotto.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/powerlotto.py)
* 修改 `PowerLottoResultsScreen`, `PowerLottoRepeatedNumbersScreen`, `PowerLottoDuplicateDetailScreen`, `PowerLottoWinningDetailsScreen` 的 `_append_to_result_list`。

#### [MODIFY] [modules/lotto539.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/lotto539.py)
* 修改 `Lotto539ResultsScreen`, `Lotto539RepeatedNumbersScreen`, `Lotto539DuplicateDetailScreen`, `Lotto539WinningDetailsScreen` 的 `_append_to_result_list`。

#### [MODIFY] [modules/lotto3star.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/lotto3star.py)
* 修改 `Lotto3StarResultsScreen`, `Lotto3StarRepeatedNumbersScreen`, `Lotto3StarWinningDetailsScreen` 的 `_append_to_result_list`。

#### [MODIFY] [modules/lotto4star.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/lotto4star.py)
* 修改 `Lotto4StarResultsScreen`, `Lotto4StarWinningDetailsScreen` 的 `_append_to_result_list`。

---

### 3. 資料庫查詢速度優化 (SQLite 索引優化)

#### [MODIFY] [modules/common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py) (DatabaseManager 類別)
* 在 `DatabaseManager.__init__` 或專門初始化方法中，加入自動建立索引邏輯：
  * **主開獎資料庫 (`lotto_history.db`)**：
    * `big_lotto(date)`
    * `lotto_539(date)`
    * `lotto_3star(date)`
    * `lotto_4star(date)`
  * **自選號資料庫 (`custom.db`)**：
    * `custom_numbers(lottery_type, created_time DESC)` (加速自選號列表加載與排序)
* 當 APP 啟動或首次建立連接時，執行 `CREATE INDEX IF NOT EXISTS` 語句。

---

## Verification Plan

### Automated Tests
* 本項目為 Kivy GUI 應用，主要依賴手動運行與日誌輸出進行驗證。
* 將在 `BaseScrollMixin` 與各結果頁面加載時新增詳細的 `logger.debug` 記錄，用以確認：
  * 載入前高度與換算後的滾動絕對目標位置。
  * `_check_load_more_after_load` 觸發時的剩餘高度與是否成功補載。

### Manual Verification
1. **分頁載入位置測試**：
   - 進入任意彩種（如大樂透）選號查詢，滑動至分頁底部載入下一頁。
   - 驗證畫面是否在載入完成後，自動把前一頁的資料移出頂部，且第一筆新資料剛好對齊在畫面最上方。
2. **連續快速滑動測試**：
   - 在結果頁面以極快速度連續向下滑動。
   - 驗證是否能夠順暢連續載入，不再出現卡死在底部且必須再次滑動才載入的 bug。
3. **資料庫索引確認**：
   - 重新啟動 APP 後，執行 scratch 檢查腳本，確認 `lotto_history.db` 和 `custom.db` 中的相關索引是否已成功建立。
