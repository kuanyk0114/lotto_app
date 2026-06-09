# 台灣彩券 APP 系統文件導覽 (doc/readme.md)

本資料夾（`doc/`）存放了本專案的所有核心系統架構說明、歷史開發實作計畫、任務清單、驗證紀錄以及排錯指南。以下是所有文件（`.md`）的分類與詳細說明，方便日後維護與查閱。

---

## 📁 系統架構與專案背景

### 1. [architecture.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/architecture.md)
* **用途**：專案核心架構說明書。
* **內容**：
  * 技術棧（Python、Kivy、SQLite、Supabase）與運行環境要求。
  * 專案實體目錄結構（包括圖片、字型、模組與佈局檔案描述）。
  * **本地 SQLite 資料庫 (`data/lotto_history.db`) 綱要（Schema）**：詳細記錄威力彩、大樂透、今彩539、三星彩、四星彩歷史獎號表，以及自選儲存表的欄位定義。
  * **遠端 Supabase PostgreSQL 資料表與 Storage Buckets** 結構與 API 金鑰說明。

### 2. [context.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/context.md)
* **用途**：專案背景知識與業務邏輯上下文。
* **內容**：詳細介紹各類彩券（威力彩、大樂透、539、三星彩、四星彩）的選號規則、開獎頻率與兌獎機制，並列出開發中需要遵循的業務邊界與 UI 設計規範。

---

## 🛠️ 排錯與疑難排解 (實機部署必看)

### 3. [android_troubleshooting_guide.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/android_troubleshooting_guide.md)
* **用途**：**Android 打包與實機運行排錯手冊**。
* **內容**：收錄專案在打包 APK 以及 Android 實機上運行的所有重大 Bug 及其修復方法：
  * Supabase SDK 因 Rust 依賴編譯失敗的重構對策。
  * Android 畫面縮小成左下角小視窗的適應性修正。
  * 檔名中英文化未同步造成的加載閃退。
  * SQLite 資料庫打包遺漏的 `buildozer.spec` 配置。
  * 高 DPI 螢幕的觸控點擊偏移與 Y 軸翻轉碰撞防錯。
  * 行動端雙重觸控事件重複分發（Double Touch）導致選取狀態相互抵消的 **100ms 觸控冷卻防重送解決方案**。

---

## 📋 歷史開發實作計畫 (Implementation Plans)
這部分檔案記錄了專案各個功能模組開發前制定的技術方案，供重構時參考：

### 4. [implementation_AdMob_plan.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/implementation_AdMob_plan.md)
* **用途**：Google AdMob 橫幅廣告與桌面端推廣插頁彈窗的實作計畫。

### 5. [implementation_Android_plan.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/implementation_Android_plan.md)
* **用途**：Android 打包環境配置與網路 API 輕量化 REST API 的替代實作方案。

### 6. [implementation_SupaBase_plan.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/implementation_SupaBase_plan.md)
* **用途**：整合遠端 Supabase 開獎獎號 CSV 檔案下載與 SQLite 自動增量同步更新的設計方案。

### 7. [implementation_app_ver_plan.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/implementation_app_ver_plan.md)
* **用途**：App 啟動版本檢測、強迫/彈性更新提示，以及引導跳轉商店的邏輯設計。

---

## 📝 任務清單與開發進度追蹤 (Tasks)
記錄了過去開發各功能模組時的詳細待辦事項清單：

* **8. [Supabase_todo.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/Supabase_todo.md)**（遠端資料同步待辦任務）
* **9. [task_AdMob.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/task_AdMob.md)**（廣告與引流任務清單）
* **10. [task_Android.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/task_Android.md)**（Android 打包依賴與部署任務清單）
* **11. [task_SupaBase.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/task_SupaBase.md)**（SupaBase 同步機制實作任務清單）

---

## 🔍 開發成果報告與驗證紀錄 (Walkthroughs)
記錄了功能實作完成後的程式變更與本地/實機測試結果：

* **12. [walkthrough_AdMob.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/walkthrough_AdMob.md)**（廣告與引流彈窗的程式變更與點擊率計數驗證）
* **13. [walkthrough_SupaBase.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/walkthrough_SupaBase.md)**（歷史開獎資料增量同步與 CSV 解析演算法驗證）
* **14. [walkthrough_app_ver.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/walkthrough_app_ver.md)**（版本號比對邏輯與視窗彈窗自動觸發驗證）
