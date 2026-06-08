# 廣告與手機引流（橫幅+插頁）任務清單

- `[x]` **1. 實作 `AdBannerArea`、`AdManager` 與 `MobileInterstitialPopup` (modules/common.py)**
    - `[x]` 導入 `Rectangle` 等必要的 Kivy 繪圖庫
    - `[x]` 實作 `AdBannerArea` 類別，支援平台判定（Windows 顯示引流橫幅；Android/iOS 顯示模擬 AdMob 橫幅）
    - `[x]` 實作 `MobileInterstitialPopup` 類別，為 Windows 端提供精美的全螢幕手機推廣彈窗
    - `[x]` 實作 `AdManager` 類別，管理插頁廣告計數與開啟邏輯
- `[x]` **2. 註冊組件與初始化 AdManager (main.py)**
    - `[x]` 於 `build()` 方法中向 `Factory` 註冊 `AdBannerArea`
    - `[x]` 在 `LotteryApp` 初始化時建立 `self.ad_manager = AdManager()` 實例
- `[x]` **3. 在介面中配置橫幅版位與返回邏輯 (KV 檔案與 python 邏輯)**
    - `[x]` 在 `kv/common.kv` 的 `LotteryTypeScreen` 加入 `AdBannerArea`
    - `[x]` 在 `kv/powerlotto.kv` 的 `PowerLottoQueryScreen` 加入 `AdBannerArea`
    - `[x]` 在 `kv/biglotto.kv`、`kv/lotto539.kv`、`kv/lotto3star.kv`、`kv/lotto4star.kv` 的查詢頁面底部加入 `AdBannerArea`
    - `[x]` 修改結果畫面的返回按鈕，使其觸發 `ad_manager.show_interstitial()` 插頁廣告邏輯
- `[x]` **4. 測試與驗證**
    - `[x]` 驗證 Windows 端的底部引流橫幅顯示，點擊能正常開啟手機版下載彈窗與開啟瀏覽器
    - `[x]` 驗證選號查詢返回時，每 2 次會跳出全螢幕插頁推廣廣告，關閉後正常返回
    - `[x]` 模擬行動端環境（將平台判定設為 `android`），驗證廣告預留高度 (50dp) 與模擬橫幅正常顯示
- `[x]` **5. 自適應 Android/iOS 商店網址與主畫面 UI 優化**
    - `[x]` 在 `modules/common.py` 中實作 `get_store_url()`，利用 `kivy.utils.platform` 自動判斷當前作業系統
    - `[x]` 將廣告橫幅、插頁廣告彈窗與版本更新更新提示的下載連結，全數由硬編碼 Play 商店替換為動態獲取的 `get_store_url()`
    - `[x]` 重新計算主畫面 `LotteryTypeScreen` 排版高度（調小 padding, spacing 與圖片高度，並縮減 grid 網格高度），解決桌面視窗中標題「好運自己選」被遮蔽的問題

