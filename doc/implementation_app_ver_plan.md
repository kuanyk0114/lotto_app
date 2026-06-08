# App 版本檢查與更新提示實作計畫

此計畫旨在為 `lotto_app` 實作啟動時自動比對本地與 Supabase 的 APP 版本（`app_ver` 表的 `ver_num` 欄位）的功能。若偵測到新版本，則跳出提示視窗建議使用者更新，並提供「稍後」與「前往更新」的選項。

## 使用者審查需求

> [!IMPORTANT]
> **1. 非阻塞設計**
> 為了保持與既有 Supabase 同步的一致性，版本檢查與比對亦會在 `SyncWorker` 背景執行緒中執行。當發現新版本時，透過線程同步鎖（`threading.Event`）暫停背景執行緒，彈出更新提示視窗，待使用者選擇後再行恢復。
> 
> **2. 商店網址配置**
> 「前往更新」按鈕會呼叫 `get_store_url()` 函數。系統會依據運行平台動態判定：在 Android 上開啟 Google Play 商店，在 iOS 上開啟 App Store 商店，其餘系統返回預設網址。上架後，您只需在設定常數中填入專屬的 APP 商店下載連結即可。

## 開放性問題

> [!NOTE]
> 目前版本比對邏輯預設支援點號分隔格式（例如：`1.0`、`1.0.1`、`2.0`），這可以涵蓋絕大多數的版本命名規則。

---

## 預計修改的檔案

### 1. [MODIFY] [sync.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/sync.py)
* 新增 `get_local_app_version()`: 讀取本地 `data/lotto_history.db` 中的 `app_ver` 資料表，取得目前版本。
* 新增 `fetch_remote_app_version()`: 連線 Supabase 的 `app_ver` 資料表，取得最新發佈的版本。

### 2. [MODIFY] [sync_ui.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/sync_ui.py)
* 新增 `AppUpdatePopup` 類別: Kivy 彈窗組件，顯示版本更新提示與「稍後」、「前往更新」按鈕。
* 新增版本比較輔助函數 `is_newer_version(local, remote)`: 用於判定遠端版本是否較新。
* 修改 `SyncWorker`:
  * 在 `run()` 流程的網路連線成功後，插入版本檢查步驟。
  * 偵測到新版本時，調度 UI 執行緒顯示 `AppUpdatePopup`，並等待使用者決定。
  * 不論使用者選擇「稍後」還是「前往更新」，皆會繼續執行後續的歷史獎號同步流程，確保資料不中斷。

### 3. [MODIFY] [main.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/main.py)
* 新增 `show_update_popup()` 方法: 於主執行緒中開啟 `AppUpdatePopup` 彈窗。

---

## 詳細實作步驟

### 1. 修改 `modules/sync.py`
在 `SyncManager` 內實作版本查詢方法：
```python
def get_local_app_version(self):
    """
    從本地 SQLite 的 app_ver 表讀取版本號，預設回傳 '1.0'
    """
    ...
    
def fetch_remote_app_version(self):
    """
    連線 Supabase 讀取 app_ver 表中的最新版本號
    """
    ...
```

### 2. 修改 `modules/sync_ui.py`
定義 `AppUpdatePopup` 類別：
* 使用與 `RetryConfirmPopup` 相似的美觀字型與配色樣式。
* 綁定「稍後」呼叫 `worker.set_user_decision('later')`。
* 綁定「前往更新」呼叫 `webbrowser.open(get_store_url())`（動態獲取當前運作平台的商店連結），並呼叫 `worker.set_user_decision('update')`。

在 `SyncWorker.run()` 中插入檢查：
```python
# 1. 偵測網路...
# 2. 檢查程式版本...
local_app = self.sync_manager.get_local_app_version()
try:
    remote_app = self.sync_manager.fetch_remote_app_version()
    if remote_app and is_newer_version(local_app, remote_app):
        # 彈出更新確認視窗
        decision = self.ask_user_update(remote_app)
        if decision == 'update':
            logger.info("使用者選擇前往更新")
except Exception as e:
    logger.error(f"版本檢查失敗: {e}")
    # 忽略錯誤繼續同步獎號，避免影響使用
```

---

## 驗證計畫

### 1. 模擬測試
* 於測試腳本中，人工將本地資料庫的 `app_ver` 修改為較舊版本（如 `0.9`）。
* 啟動 APP，確認在開始更新前會跳出「有新版本發佈」的提示視窗。

### 2. 按鈕行為驗證
* **點擊「稍後」**: 彈窗應關閉，接著正常跑完 Supabase 獎號更新，並進入 APP 主畫面。
* **點擊「前往更新」**: 彈窗應關閉，並自動開啟瀏覽器前往設定的商店網址，同時繼續背景同步並順利進入 APP。
