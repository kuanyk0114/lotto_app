# 09 系統文件總覽與導覽 (lotto_app)

歡迎來到「**好運自己選**」（lotto_app）系統文件中心！本資料夾（`doc/`）完整收錄了本專案所有的需求分析、畫面設計、使用說明、技術架構、API 規範、測試計劃、部署指南與 KV 檔案整合報告。

以下為所有系統文檔的完整導覽目錄，點選連結即可直接查閱詳細內容：

---

## 📚 系統文件目錄索引

### 📄 1. [01_開發需求清單.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/01_%E9%96%8B%E7%99%BC%E9%9C%80%E6%B1%82%E6%B8%85%E5%96%AE.md)
* **內容**：專案目標定位、三大平台支援範疇、五大彩種選號規則、五大核心分析功能細節、非功能性效能與資安需求。

### 📄 2. [02_模擬畫面設計.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/02_%E6%A8%A1%E6%93%AC%E7%95%AB%E9%9D%A2%E8%A8%AD%E8%A8%88.md)
* **內容**：UI/UX 視覺設計規範（暗色黃金配色、彩球渲染）、主選單畫面 Layout、各彩種選號頁面 Ascii 圖表設計、彈窗與對話框設計。

### 📄 3. [03_使用說明.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/03_%E4%BD%BF%E7%94%A8%E8%AA%AA%E6%98%8E.md)
* **內容**：使用者操作手冊、軟體安裝指引、五大功能（查詢選號、查重複號、中獎詳情、儲存/提取自選號、近期獎號）步驟解說與 FAQ。

### 📄 4. [04_技術架構文檔.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/04_%E6%8A%80%E8%A1%93%E6%9E%B6%E6%A7%8B%E6%96%87%E6%AA%94.md)
* **內容**：系統層級架構圖、Python 業務模組分工表、本地 SQLite (`lotto_history.db`, `custom.db`) Schema 設計、Supabase 雲端同步機制與觸控冷卻演算法。

### 📄 5. [05_API文檔.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/05_API%E6%96%87%E6%AA%94.md)
* **內容**：內部 Python 核心類別介面 API (`BasePaginationMixin`, 各彩種 Screen 方法) 與外部 Supabase REST API HTTP 通訊協定規格。

### 📄 6. [06_測試計劃.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/06_%E6%B8%AC%E8%A9%A6%E8%A8%88%E5%8A%83.md)
* **內容**：測試目標與環境說明、完整的測試用例矩陣表（包含邊界測試、分頁測試、長按刪除防護、100ms 觸控冷卻驗證等）。

### 📄 7. [07_部署指南.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/07_%E9%83%A8%E7%BD%B2%E6%8C%87%E5%8D%97.md)
* **內容**：Windows 桌面版 PyInstaller 打包流程、Android Buildozer 腳本配置、實機執行排錯與高 DPI 畫面縮小等疑難排解手冊。

### 📄 8. [08_KV檔案整合報告.md](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/doc/08_KV%E6%AA%94%E6%A1%88%E6%95%B4%E5%90%88%E5%A0%B1%E5%91%8A.md)
* **內容**：Kivy Language 佈局檔案架構、`common.kv` 與彩種專屬 KV 檔案解析、UI 屬性與 Python 事件綁定機制。

---

## 🛠️ 專案維護資訊

* **開發語言**：Python 3.11+
* **前端框架**：Kivy 2.3.1
* **資料庫**：SQLite (Local) / Supabase PostgreSQL (Cloud)
