# Android APK 打包與部署實作計畫 (輕量化 REST API 方案)

此計畫旨在為 `lotto_app` 專案提供將 Kivy 應用程式打包為 **Android APK** 的詳細編譯流程與配置說明，並解決因 Supabase SDK 內 pydantic-core 依賴 Rust 編譯導致 Android 打包失敗的問題。

## 使用者審查需求

> [!IMPORTANT]
> **1. 移除 Supabase SDK 並改用輕量化 REST API**
> 原本使用的 Supabase Python SDK 依賴 `pydantic` 與 `pydantic-core`。由於 `pydantic-core` 包含 Rust C-extensions，Buildozer 無法在沒有複雜交叉編譯設定的情況下為 Android 目標編譯 Rust，這導致 GitHub Actions 上的打包流程崩潰。
> **解決方案**：我們將 `modules/sync.py` 重構為使用 Python 內建/標準的 `requests` 庫直接調用 Supabase REST API 與 Storage API，從而完全移除對 `supabase` 及其關聯套件的依賴。
> 
> **2. 簡化 `buildozer.spec` 的 `requirements`**
> 簡化後的依賴僅需要：`python3, kivy==2.3.1, sqlite3, openssl, requests, urllib3, certifi, idna, chardet`。這將極大地縮短編譯時間，並徹底消除 Rust 交叉編譯錯誤。
> 
> **3. 繼續使用 GitHub Actions 自動化編譯 (方案 A)**
> 我們將繼續使用 GitHub Actions 作為打包平台，您只需將修改推送到 GitHub，即可在雲端完成 APK 打包並下載，不佔用本機資源。

---

## 預計修改的檔案

### 1. [MODIFY] [sync.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/sync.py)
* 移除 `from supabase import create_client, Client` 導入。
* 將 `fetch_remote_app_version()`、`fetch_remote_updates()` 與 `download_csv_file()` 改寫為使用 `requests` 發送 HTTP GET 請求至 Supabase REST 與 Storage API。

### 2. [MODIFY] [buildozer.spec](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/buildozer.spec)
* 簡化 `requirements`，移除 `supabase`、`pydantic`、`httpx` 等複雜依賴包，只保留基礎網路與 Kivy 相關依賴。

---

## 詳細實作步驟

### 1. 重構 `modules/sync.py` 網路讀取
改用 HTTP 標頭 `apikey` 與 `Authorization` 進行 API 認證：
* **取得應用程式版本**:
  `GET {supabase_url}/rest/v1/app_ver`
* **取得更新清單**:
  `GET {supabase_url}/rest/v1/data_list`
* **下載 CSV 檔案**:
  `GET {supabase_url}/storage/v1/object/authenticated/{bucket_id}/{file_name}`

### 2. 更新 `buildozer.spec` requirements
修改後的設定如下：
```ini
[app]
# 應用程式名稱
title = 好運自己選

# 套件名稱與網域 (com.lottotaiwan.goodluck)
package.name = goodluck
package.domain = com.lottotaiwan

# 原始碼副檔名
source.include_exts = py,png,jpg,kv,ttf,json

# 依賴模組 (簡化後的穩定版本)
requirements = python3,kivy==2.3.1,sqlite3,openssl,requests,urllib3,certifi,idna,chardet

# 應用程式版本
version = 1.0

# 權限要求
android.permissions = INTERNET

# 支援的螢幕方向 (直向)
orientation = portrait

# (選填) 圖示與啟動畫面
# icon.filename = %(source.dir)s/images/icon.png
# presplash.filename = %(source.dir)s/images/presplash.png
```

### 3. 環境設定與編譯命令（以 WSL / Linux 為例）
1. 更新套件庫並安裝系統依賴：
   ```bash
   sudo apt update
   sudo apt install -y build-essential git zip unzip colordiff libltdl-dev libffi-dev libssl-dev autoconf autotools-dev libtool pkg-config zlib1g-dev python3-pip python3-setuptools python3-venv openjdk-17-jdk
   ```
2. 安裝 Buildozer：
   ```bash
   pip install --user buildozer
   ```
3. 初始化並編譯（第一次編譯會自動下載 Android SDK 和 NDK，約需 15-30 分鐘）：
   ```bash
   buildozer android debug
   ```
4. 編譯完成後的 APK 會存放於專案的 `bin/` 資料夾中（例如：`bin/goodluck-1.0-debug.apk`）。

### 4. 使用 GitHub Actions 免費編譯（若適用）
只要在專案中建立 `.github/workflows/android.yml`，並將程式碼上傳至 GitHub，GitHub 就會自動執行背景編譯，完工後可在 Actions 頁面直接下載簽署好的測試 APK。

---

## 驗證計畫

### 1. 安裝與啟動驗證
* 將產生的 `goodluck-1.0-debug.apk` 傳送至 Android 手機上進行安裝。
* 啟動 App，確認能順利進入載入同步畫面，無閃退現象。

### 2. 網路與資料同步驗證
* 確保手機能連上網路，觀察啟動時是否成功連接 Supabase 並更新最新開獎資料。
* 點擊「版本更新」提示，確認是否能正確叫起手機瀏覽器並跳轉至適配的 Google Play 商店網址。

### 3. 廣告版位顯示驗證
* 進入各彩種查詢頁面，確認底部橫幅顯示為深灰色的 `[ Google AdMob 測試廣告 (橫幅) ]` 模擬版位，高度比例符合預期的 50dp。
