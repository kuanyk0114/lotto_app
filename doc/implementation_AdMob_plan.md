# 廣告與手機引流（橫幅+插頁）與平台相容性實作計畫

此計畫旨在為 `lotto_app` 實作跨平台的 **橫幅廣告 (Banner)** 與 **插頁廣告 (Interstitial)** 機制。
* **橫幅廣告 (Banner)**：
  * **Windows 桌面端**：顯示「下載手機版 APP，引流至手機端」的宣傳按鈕。
  * **Android / iOS 行動端**：預留高 `dp(50)` 的區塊並顯示「Google AdMob 測試廣告（橫幅）」作為未來載入原生 AdMob 廣告的佔位空間。
* **插頁廣告 (Interstitial)**：
  * **觸發時機**：使用者在各彩種「查詢結果頁面」點擊「返回」或「回彩券選擇」時觸發。為防止過度打擾，可設定計數器（例如：每查詢 2 次觸發 1 次）。
  * **Windows 桌面端**：彈出一個全螢幕的精美手機推廣 PopUp，印有手機版特色與下載 QR Code。
  * **Android / iOS 行動端**：觸發 AdMob 插頁廣告加載與展示（測試期顯示模擬廣告）。

## 使用者審查需求

> [!IMPORTANT]
> **1. 跨平台相容性與 AdManager 統一管理**
> 我們將於 `modules/common.py` 中建立一個全域的 `AdManager` 類別，統一封裝廣告的載入、顯示與計數邏輯，並使用 `kivy.utils.platform` 做平台分流，確保程式碼具備跨平台編譯能力。
> 
> **2. 預留廣告空間之畫面**
> * **橫幅廣告 (Banner)**：佈署於 APP 主選單與各彩種的「選號查詢頁面」最底部。
> * **插頁廣告 (Interstitial)**：於「結果頁面」返回時偵測計數並觸發。

## 開放性問題

> [!NOTE]
> 目前下載連結預設為 Google Play 商店首頁，在未來您的手機版 App 上架後，可以隨時替換為實際的商店專屬網址。

---

## 預計修改的檔案

### 1. [MODIFY] [modules/common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py)
* 導入 `kivy.graphics.Rectangle` 繪製背景。
* 新增 `AdBannerArea(BoxLayout)` 類別（橫幅廣告與推廣按鈕）。
* 新增 `AdManager` 類別，管理插頁廣告計數與呼叫方法 `show_interstitial()`。
* 新增 `MobileInterstitialPopup(Popup)` 類別（Windows 專用的全螢幕手機推廣彈窗，作為插頁廣告模擬）。
* 修改 `BaseResultScreen.go_back()`，加入插頁廣告觸發呼叫。
* 修改 `BaseRepeatedNumbersScreen.back_to_query()`，加入插頁廣告觸發呼叫。
* 新增 `get_store_url()` 函數與 `ANDROID_STORE_URL`、`IOS_STORE_URL` 常數，自適應 Android/iOS 雙平台商店網址。

### 2. [MODIFY] [main.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/main.py)
* 於 `build()` 中向 `Factory` 註冊 `AdBannerArea`。
* 在 `LotteryApp` 初始化 `AdManager` 實例，方便全域呼叫。

### 3. [MODIFY] 各 KV 檔案（`common.kv`, `powerlotto.kv` 等）
* 於對應的主選單與查詢畫面最底部加入 `AdBannerArea`。
* 調整 `kv/common.kv` 的主選單版面元件高度、內距與間距，以避免在 Windows 桌面視窗中頂部「好運自己選」標題被遮蔽。

### 4. [MODIFY] [modules/sync_ui.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/sync_ui.py)
* 更改版本檢查彈出視窗點擊「前往更新」時的下載連結，由硬編碼替換為動態調用 `get_store_url()`，使其自適應當前運行系統平台。

---

## 詳細實作步驟

### 1. 實作 `AdManager` 與彈窗於 `modules/common.py`
```python
class AdManager:
    def __init__(self):
        self.query_count = 0
        self.trigger_threshold = 2  # 每 2 次返回觸發 1 次廣告
        
    def show_interstitial(self, on_close_callback=None):
        self.query_count += 1
        if self.query_count % self.trigger_threshold == 0:
            # 顯示廣告
            from kivy.utils import platform
            if platform in ('android', 'ios'):
                # 呼叫 AdMob 插頁廣告（測試期顯示 Log/模擬）
                pass
            else:
                # Windows 彈出全螢幕推廣視窗
                popup = MobileInterstitialPopup(on_close=on_close_callback)
                popup.open()
                return True
        if on_close_callback:
            on_close_callback()
        return False
```

### 2. 修改返回邏輯
在結果畫面的返回按鈕事件中，包裝返回動作：
```python
def go_back(self):
    # 先觸發插頁廣告，廣告關閉後再執行實際的返回
    app = App.get_running_app()
    app.ad_manager.show_interstitial(on_close_callback=self._real_go_back)
```

---

## 驗證計畫

### 1. Windows 端橫幅與插頁廣告驗證
* 啟動 App，確認底部橫幅顯示正常。
* 進入威力彩選號，隨便選號點擊查詢，然後點擊「返回」。重複此操作，確認每第 2 次返回時，會彈出全螢幕的手機版推廣介紹（包含 QR Code 與關閉按鈕）。
* 點擊關閉，確認能順利返回查詢畫面。

### 2. 模擬行動端 AdMob 廣告空間驗證
* 在代碼中暫時將平台偵測改為 `'android'` 進行模擬測試，確認底部橫幅變為深灰色，且顯示 `[ Google AdMob 測試廣告 (橫幅) ]`。
