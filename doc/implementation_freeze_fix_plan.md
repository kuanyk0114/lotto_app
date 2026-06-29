# 修復重複X碼查詢結果列表載入下一頁時 Android 畫面凍住問題

## 問題描述

所有彩種的重複X碼查詢結果列表頁，在 Android APK 上滑動到底部載入下一頁（30 筆）時，畫面會**完全凍住約 1~2 秒**，手指無法滑動。第一頁（前 30 筆）載入後的初始滑動是流暢的。Windows 桌面端無此問題。

另外，換頁後的滾動定位有時會跳到新頁的尾端，而不是新頁的開頭。

## 根因分析

透過比較**選號查詢結果頁**（不卡）和**重複X碼查詢結果頁**（會卡）的程式碼，找出以下關鍵差異：

### 選號查詢結果的 `_append_to_result_list`（不卡）
```python
# 簡單直接：移除舊指示器 → 逐筆加入 widget → 加回指示器 → 恢復滾動
self._remove_load_more_indicator()
for record in new_records:
    item_widget = self._create_result_item(record)
    self.ids.results_layout.add_widget(item_widget)
self._add_load_more_indicator()
Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(...), 0.1)
```

### 重複X碼查詢結果的 `_append_to_result_list`（會卡）
```python
# 多了三個額外操作：
# ❌ 1. 強制預計算並設定 layout 高度（觸發全部已存在 widget 的完整 relayout）
calculated_height = num_items * dp(50) + ...
self.ids.results_layout.height = calculated_height  # ← 這行觸發所有子 widget 重新佈局！

# ❌ 2. 每筆記錄之間加入分隔線 widget（額外的 BoxLayout + Canvas 繪圖）
separator = BoxLayout(size_hint_y=None, height=dp(1))
with separator.canvas:
    Color(rgba=get_color_from_hex('#888888'))
    Rectangle(pos=separator.pos, size=separator.size)

# ❌ 3. 滾動恢復延遲過短（0.05s vs 選號查詢的 0.1s）
Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(...), 0.05)
```

### 三大效能殺手

| 問題 | 影響 | 嚴重程度 |
|------|------|----------|
| **強制預計算 layout 高度** | 在新增 widget 前設定 `height`，觸發所有已存在子 widget 的完整 relayout。頁數越多（60→90→120→...），relayout 越慢 | 🔴 最嚴重 |
| **分隔線 widget** | 每頁額外 29 個 BoxLayout + 29 次 Canvas 繪圖，累積到第10頁就多了 290 個無效 widget | 🟡 中等 |
| **滾動恢復延遲 0.05s** | 可能在 widget 尚未完成渲染前就恢復滾動位置，導致定位不準 | 🟠 次要 |

## 修改方案

### 修改一：移除強制高度預計算（核心修復）

**原理**：學習選號查詢結果頁的做法 — 不主動設定 `results_layout.height`，讓 BoxLayout 根據子 widget 的 `size_hint_y=None` + `height` 自動計算高度。

**做法**：在 `_update_result_list` 和 `_append_to_result_list` 中，刪除以下程式碼：
```python
# 刪除這兩行：
calculated_height = num_items * dp(50) + max(0, num_items - 1) * dp(1) + dp(60) + (2 * num_items - 1) * dp(5)
self.ids.results_layout.height = calculated_height
```

### 修改二：移除分隔線 widget，改用 spacing

**原理**：將 `results_layout`（或 `duplicate_list`）的 `spacing` 設為 `dp(1)` 即可產生視覺分隔效果，不需要額外的 widget。

**做法**：
1. 刪除所有手動建立 separator 的程式碼
2. 確保 KV 檔案中的 layout 設定了 `spacing: dp(1)`

### 修改三：修正滾動恢復延遲

**做法**：將 `_append_to_result_list` 中的滾動恢復延遲從 `0.05` 改為 `0.1`（與選號查詢結果一致）。

## 修改清單

> [!IMPORTANT]
> 以下修改涵蓋**全部五個彩種**的重複X碼查詢結果頁面。

### 重複X碼查詢結果列表頁（RepeatedNumbers / Duplicate Screen）

---

#### [MODIFY] [lotto3star.py](file:///d:/我的專案/台彩程式/lotto_app/modules/lotto3star.py)
- `Lotto3StarRepeatedNumbersScreen._update_result_list`（~L1592）：移除 `calculated_height` 預計算和分隔線 widget
- `Lotto3StarRepeatedNumbersScreen._append_to_result_list`（~L1644）：移除 `calculated_height` 預計算、分隔線 widget，修正滾動恢復延遲

---

#### [MODIFY] [lotto4star.py](file:///d:/我的專案/台彩程式/lotto_app/modules/lotto4star.py)
- 四星彩重複X碼的 `_update_result_list`（~L1107）和 `_append_to_result_list`（~L1155）：同上修改

---

#### [MODIFY] [lotto539.py](file:///d:/我的專案/台彩程式/lotto_app/modules/lotto539.py)
- 今彩539重複X碼的 `_update_result_list`（~L2133）和 `_append_to_result_list`（~L2181）：同上修改

---

#### [MODIFY] [biglotto.py](file:///d:/我的專案/台彩程式/lotto_app/modules/biglotto.py)
- 大樂透重複X碼的 `_update_result_list`（~L724）和 `_append_to_result_list`（~L772）：同上修改

---

#### [MODIFY] [powerlotto.py](file:///d:/我的專案/台彩程式/lotto_app/modules/powerlotto.py)
- 威力彩重複X碼的 `_update_result_list`（~L1424）和 `_append_to_result_list`（~L1471）：同上修改

---

### KV 檔案（確保 layout spacing）

#### [MODIFY] 各彩種 KV 檔案中的重複X碼結果 layout
- 確認 `results_layout` / `duplicate_list` 的 `spacing` 設定為 `dp(1)` 以替代分隔線

## 驗證計劃

### Windows 測試
- 執行程式，進入各彩種重複X碼查詢，確認：
  - 第一頁正確顯示
  - 滑動到底部能正確載入下一頁
  - 換頁後滾動位置正確（不跳到尾端）
  - 項目之間有視覺分隔效果

### APK 測試
- 推送到 GitHub → 打包 APK → 安裝測試
- 確認載入下一頁時畫面不再凍住
- 確認滑動流暢度
