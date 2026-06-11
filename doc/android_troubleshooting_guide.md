# Android 打包與觸控事件排錯解決指南

本文件記錄了 `lotto_app` 專案在打包為 Android APK 時所遇到的各類「閃退」、「畫面比例不對」及「彩球點選無反應」等問題，並詳細整理了其原因與對應的解決方案，以便日後維護與參考。

---

## 目錄
1. [Supabase SDK 與 Rust 編譯失敗問題 (打包閃退/編譯失敗)](#1-supabase-sdk-與-rust-編譯失敗問題-打包閃退編譯失敗)
2. [Android 畫面過小問題 (視窗大小設定)](#2-android-畫面過小問題-視窗大小設定)
3. [找不到圖片資源錯誤 (資源路徑與檔名同步)](#3-找不到圖片資源錯誤-資源路徑與檔名同步)
4. [預載資料庫未打包問題 (SQLite no such table 錯誤)](#4-預載資料庫未打包問題-sqlite-no-such-table-錯誤)
5. [選號查詢畫面點擊彩球無反應問題 (座標系統與碰撞偵測)](#5-選號查詢畫面點擊彩球無反應問題-座標系統與碰撞偵測)
6. [觸控事件重複分發導致選取抵消問題 (Double Touch)](#6-觸控事件重複分發導致選取抵消問題-double-touch)
7. [重複查詢結果列表滑動誤觸進入詳情問題 (ScrollView Touch-Down Click-Through)](#7-重複查詢結果列表滑動誤觸進入詳情問題-scrollview-touch-down-click-through)

---

## 1. Supabase SDK 與 Rust 編譯失敗問題 (打包閃退/編譯失敗)

### 📌 問題描述
在 GitHub Actions 雲端打包或本地使用 Buildozer 打包時，編譯流程在編譯 Supabase SDK 依賴套件（特別是 `pydantic-core`）時報錯崩潰。
* **原因**：Supabase Python SDK 依賴 `pydantic` 與 `pydantic-core`，其中包含大量 Rust C-extensions（需要 Rust 編譯器）。Android 目標環境的交叉編譯（Cross-Compilation）在沒有複雜的 Rust 工具鏈設定下無法順利編譯 Rust 二進位檔。

### 💡 解決方案
* **重構為輕量化 REST API 方案**：
  完全移除 `supabase` Python SDK，改用 Python 內建/標準的 `requests` 庫直接調用 Supabase 提供之標準 REST API 與 Storage API 來處理數據與檔案下載。
* **重構位置**：`modules/sync.py`
* **打包依賴簡化**：
  在 `buildozer.spec` 中，將 `requirements` 內的 `supabase` 等複雜包移除，只保留：
  ```ini
  requirements = python3,kivy==2.3.1,sqlite3,openssl,requests,urllib3,certifi,idna,chardet
  ```

---

## 2. Android 畫面過小問題 (視窗大小設定)

### 📌 問題描述
APK 安裝至 Android 實機啟動後，App 畫面被壓縮在螢幕左下角一個極小的區域內。
* **原因**：在 `main.py` 中，為了配合桌面測試環境，設定了 `Window.size = (360, 640)`，但沒有限制平台。這導致在 Android 高解析度實機上，Kivy 也強制將整個顯示視窗縮小為固定像素，無法自適應螢幕解析度。

### 💡 解決方案
* **平台判斷限制**：
  在 `main.py` 進行環境初始化時，加入 `platform` 判斷，限制只有在非行動裝置平台（非 Android 與 iOS）才強制調整視窗大小：
  ```python
  from kivy.utils import platform
  
  # 僅限桌面端限制視窗大小，Android / iOS 行動端使用系統預設全螢幕
  if platform not in ('android', 'ios'):
      Window.size = (360, 640)
  ```

---

## 3. 找不到圖片資源錯誤 (資源路徑與檔名同步)

### 📌 問題描述
在 Android 裝置上啟動 App 進入主畫面時發生閃退，檢查日誌顯示 `Error loading <images/4星彩.png>` 等錯誤。
* **原因**：原本的圖片資源與代碼引用了中文檔名。進行英文重構後，雖然本地圖片已被修改，但代碼的最新變更（`main.py` 與 `kv/common.kv` 等）未及時提交與推送至 GitHub，導致 GitHub Actions 打包時仍以中文名稱讀取，進而找不到對應資源閃退。

### 💡 解決方案
* **資源英文命名標準化**：
  將專案中的所有圖片資源統一採用小寫英文命名（例如 `power.png`, `big.png`, `lotto539.png`），並確保 Python 代碼、KV 佈局檔案與實體檔案的檔名完全一致且已推送至 Git 遠端儲存庫。

---

## 4. 預載資料庫未打包問題 (SQLite no such table 錯誤)

### 📌 問題描述
APK 啟動後，在執行歷史紀錄查詢或同步時拋出 SQLite 錯誤：`no such table: power_lotto`。
* **原因**：`buildozer.spec` 檔案中的 `source.include_exts` 預設只包含了 `py,png,jpg,kv,ttf,json`。這導致預載歷史中獎資料的 SQLite 庫檔案 `data/lotto_history.db` 被過濾掉，沒有被打包進最終的 APK 中，程式執行時找不到該資料庫表。

### 💡 解決方案
* **修改包含副檔名配置**：
  在 `buildozer.spec` 檔案中，將 `db` 加入打包副檔名名單：
  ```ini
  source.include_exts = py,png,jpg,kv,ttf,json,db
  ```

---

## 5. 選號查詢畫面點擊彩球無反應問題 (座標系統與碰撞偵測)

### 📌 問題描述
使用者點擊選號查詢畫面中的彩球，彩球毫無反應、無法選取；在畫面上做拖曳/滑動時，卻能偶爾選到。
* **原因**：
  1. **座標系不一致 (Android DPI 縮放與翻轉)**：Android 裝置具有高屏幕密度（`density > 1`），且存在頂部狀態列和底部虛擬導覽列。Kivy 內部的碰撞檢測預設是以底部為原點，而觸控系統可能以頂部為原點，或是座標未正確乘以 `density` 縮放，導致 `collide_point` 判斷點擊座標在按鈕外部。
  2. **事件派發問題**：原 `BallButton` 的 MRO 繼承鏈與事件派發在 Kivy `ButtonBehavior` 中可能因為微小的手指滑動而被誤判為 Drag 手勢，導致 `on_press` 始終不被觸發。

### 💡 解決方案
* **步驟 A：強迫全螢幕配置**
  在 `buildozer.spec` 中設置 `fullscreen = 1`，消除導覽列帶來的座標原點偏移。
* **步驟 B：覆寫 `collide_point` 進行坐標自適應**
  在 `BallButton` 中，自訂碰撞檢測邏輯，提供 density 縮放與 Y 軸翻轉的 fallback 坐標計算：
  ```python
  def collide_point(self, x, y):
      # 1. 標準碰撞檢測
      if self.x <= x <= self.right and self.y <= y <= self.top:
          return True
          
      # 2. 高 DPI / Y 軸翻轉防錯判定
      try:
          from kivy.metrics import Metrics
          from kivy.core.window import Window
          density = Metrics.density
          if density and density != 1.0:
              sx = x * density
              # Y軸翻轉轉換
              sy_inv = Window.height - (y * density)
              if self.x <= sx <= self.right and self.y <= sy_inv <= self.top:
                  return True
      except Exception:
          pass
      return False
  ```
* **步驟 C：改用自定義 Grab 事件分發**
  不要使用 `ButtonBehavior` 的 `on_press`。直接接管觸控的三個底層生命週期，並將觸控事件抓取（Grab）以防事件擴散：
  * `on_touch_down`：若碰撞，調用 `touch.grab(self)` 鎖定觸控，並返回 `True` 阻斷。
  * `on_touch_move`：若為 grabbed，直接返回 `True` 阻斷。
  * `on_touch_up`：若為 grabbed，調用 `touch.ungrab(self)`，在釋放點碰撞時切換狀態，並返回 `True`。

---

## 6. 觸控事件重複分發導致選取抵消問題 (Double Touch)

### 📌 問題描述
在接管了觸控事件並自訂 `grab` 鎖定後，Android 實機上彩球仍然偶爾出現點擊無效的狀況。
* **原因**：日誌分析顯示，在 Android 觸控屏幕上，一次單擊會觸發**兩次幾乎完全相同且間隔僅 3 毫秒**的觸控事件鏈（包含兩次 down 與兩次 up）。這是因為 Kivy 內合同時啟用了 `androidinput`（原生觸控事件）與 `mousetouch`（滑鼠模擬觸控事件）。
* 因為兩次觸控都被判定成功，彩球狀態經歷了兩次連續的反轉：`False` ➔ `True` ➔ `False`，使得選取效果被完全抵消。

### 💡 解決方案
* **加入觸控冷卻防重送機制 (Debounce Cooldown)**：
  在 `BallButton.__init__` 中初始化 `self._last_touch_time = 0.0`。
  在 `on_touch_down` 判定中引入 **0.1 秒 (100ms)** 的冷卻閥值，若兩次點擊的間隔時間小於 0.1 秒，則直接判定為系統重複事件，予以忽略：
  ```python
  def on_touch_down(self, touch):
      collide = self.collide_point(*touch.pos)
      if collide:
          import time
          current_time = time.time()
          if current_time - self._last_touch_time < 0.1:
              # 忽略 100ms 內的重複系統分發觸控
              return False
          self._last_touch_time = current_time
          touch.grab(self)
          return True
      return False
  ```
  這可以 100% 消除重複事件的干擾，同時保持人類最高速連續點擊的流暢性。

---

## 7. 重複查詢結果列表滑動誤觸進入詳情問題 (ScrollView Touch-Down Click-Through)

### 📌 問題描述
在各彩種的「重複X碼查詢結果列表」中，當用戶以手指滑動欲捲動 ScrollView 查看其他頁面時，會誤點到手指剛接觸的那筆記錄，直接進入了查看重複記錄詳情頁面，導致無法正常滑動列表。
* **原因**：原本的列表項目使用的是普通 `BoxLayout` 容器，並直接將點擊詳情邏輯綁定到其 `on_touch_down` 事件。在 Kivy 事件傳遞中，滑動操作的起始按壓會立刻觸發該項目的 `on_touch_down` 並切換螢幕，導致 `ScrollView` 無法攔截該觸控手勢。

### 💡 解決方案
* **步驟 A：實作 ClickableBoxLayout 混合類別**
  在 `modules/common.py` 中，定義一個繼承自 `ButtonBehavior` 與 `BoxLayout` 的類別，使佈局具備按鈕的觸控 Grabbing / Scrolling 攔截能力：
  ```python
  from kivy.uix.behaviors import ButtonBehavior
  from kivy.uix.boxlayout import BoxLayout

  class ClickableBoxLayout(ButtonBehavior, BoxLayout):
      pass
  ```
* **步驟 B：改用 `on_release` 響應點擊**
  將各彩種結果列表中（例如 `biglotto.py`、`lotto3star.py` 等的 `_create_duplicate_item`）的容器 `BoxLayout` 替換為 `ClickableBoxLayout`，並將事件綁定從 `on_touch_down` 改為 `on_release`：
  ```python
  # 原程式碼：
  # box = BoxLayout(...)
  # box.bind(on_touch_down=lambda instance, touch: self._handle_duplicate_item_click(instance, touch, item))
  
  # 修改後：
  box = ClickableBoxLayout(...)
  box.bind(on_release=lambda instance: self._handle_duplicate_item_click(instance, item))
  ```
* **步驟 C：簡化回呼函式**
  移除回呼中不再需要的 `touch` 參數和 `collide_point` 檢測，裝載由 `ButtonBehavior` 自動處理的觸控釋放判定（當被 ScrollView 搶奪觸控後，觸控被 `ungrab`，因此不會觸發項目點擊）：
  ```python
  def _handle_duplicate_item_click(self, instance, item):
      self.show_duplicate_details(item['numbers'])
  ```
