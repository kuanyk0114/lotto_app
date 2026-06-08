# Android APK 打包與部署實作計畫

此計畫旨在為 `lotto_app` 專案提供將 Kivy 應用程式打包為 **Android APK** 的詳細編譯流程與配置說明，方便在實體 Android 手機上進行安裝測試（包含廣告版面與版本更新功能驗證）。

## 使用者審查需求

> [!IMPORTANT]
> **1. Windows 平台打包限制**
> Kivy 的打包工具 `Buildozer` 目前**不支援**直接在 Windows 原生環境下進行編譯（因為 Android NDK 編譯工具鏈需要 Linux/macOS 環境）。因此，我們提供以下三種解決方案供您選擇：
> * **方案 A（推薦）：GitHub Actions 自動化編譯** —— 在專案中建立自動化工作流，只要將程式碼推送到 GitHub，即可在雲端免費編譯並下載 APK，完全不佔用本機資源且無需設定環境。
> * **方案 B：WSL (Windows Subsystem for Linux) 本機編譯** —— 在 Windows 下安裝 Ubuntu 子系統，並於 Linux 環境中安裝編譯依賴與執行 Buildozer。
> * **方案 C：Docker 容器編譯** —— 使用預先載有編譯環境的 Docker 鏡像進行打包。
> 
> **2. 程式庫與權限需求**
> 打包配置檔 `buildozer.spec` 中必須明確聲明以下權限與依賴包：
> * 權限：`INTERNET`（網路連線，資料同步及廣告載入必備）。
> * 依賴包：`python3`, `kivy`, `requests`, `supabase`, `postgrest`, `realtime`, `gotrue`, `storage3`, `urllib3`, `certifi`, `idna`, `charset_normalizer`（Supabase 連線同步與版本檢查所需依賴）。

---

## 預計新增與修改的檔案

### 1. [NEW] [buildozer.spec](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/buildozer.spec)
* Kivy 打包配置核心檔案，設定 App 名稱、套件包名（Package Name）、版本號、圖示、啟動畫面、權限、以及 Python 依賴清單。

### 2. [NEW] [.github/workflows/android.yml](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/.github/workflows/android.yml)
* （若選擇方案 A）配置 GitHub Actions 工作流，自動拉取程式碼、設定 Java 17、安裝 Android SDK/NDK、執行 Buildozer 並產生可下載的 APK 產物。

---

## 詳細實作步驟

### 1. 建立並調整 `buildozer.spec`
我們將建立適合本專案的 `buildozer.spec` 設定，關鍵參數如下：
```ini
[app]
# 應用程式名稱
title = 好運自己選

# 套件名稱與網域 (com.lottotaiwan.goodluck)
package.name = goodluck
package.domain = com.lottotaiwan

# 原始碼副檔名
source.include_exts = py,png,jpg,kv,ttf,json

# 依賴模組 (極為重要，若遺漏會造成 APK 啟動閃退)
requirements = python3,kivy==2.3.1,requests,supabase,postgrest,realtime,gotrue,storage3,urllib3,certifi,idna,charset_normalizer

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

### 2. 環境設定與編譯命令（以 WSL / Linux 為例）
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

### 3. 使用 GitHub Actions 免費編譯（若適用）
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
