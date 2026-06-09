import sys
import traceback

try:
    print("[BOOTSTRAP] 1. Importing Kivy core modules")
    sys.stdout.flush()
    from kivy.app import App
    from kivy.uix.screenmanager import Screen, ScreenManager
    from kivy.factory import Factory
    from kivy.lang import Builder
    from kivy.core.window import Window
    from kivy.core.text import LabelBase
    from kivy.clock import Clock
    from kivy.utils import get_color_from_hex
    from kivy.config import Config
    from kivy.properties import DictProperty
    
    print("[BOOTSTRAP] 2. Importing standard libraries")
    sys.stdout.flush()
    import os
    import csv
    import sqlite3
    import importlib.util
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import logging
    import threading

    print("[BOOTSTRAP] 3. Importing ssl library")
    sys.stdout.flush()
    import ssl

    print("[BOOTSTRAP] 4. Importing requests library")
    sys.stdout.flush()
    import requests

    print("[BOOTSTRAP] 5. Importing sync_ui module")
    sys.stdout.flush()
    from modules.sync_ui import SyncProgressPopup, RetryConfirmPopup, SyncWorker, AppUpdatePopup
    
    print("[BOOTSTRAP] 6. Importing PowerLotto screens")
    sys.stdout.flush()
    from modules.powerlotto import PowerLottoQueryScreen, PowerLottoResultScreen, PowerLottoSavedScreen, PowerLottoDuplicateScreen, PowerLottoDuplicateDetailScreen, PowerLottoWinningDetailsScreen
    
    print("[BOOTSTRAP] 7. Importing BigLotto screens")
    sys.stdout.flush()
    from modules.biglotto import BigLottoQueryScreen, BigLottoResultsScreen, BigLottoSavedScreen, BigLottoRepeatedNumbersScreen, BigLottoDuplicateDetailScreen, BigLottoWinningDetailsScreen
    
    print("[BOOTSTRAP] 8. Importing Lotto539 screens")
    sys.stdout.flush()
    from modules.lotto539 import Lotto539QueryScreen, Lotto539ResultScreen, Lotto539SavedScreen, Lotto539WinningDetailsScreen, Lotto539DuplicateScreen, Lotto539DuplicateDetailScreen
    
    print("[BOOTSTRAP] 9. Importing Lotto3Star & Lotto4Star screens")
    sys.stdout.flush()
    from modules.lotto3star import Lotto3StarQueryScreen, Lotto3StarResultsScreen, Lotto3StarSavedScreen, Lotto3StarRepeatedNumbersScreen, Lotto3StarDuplicateDetailScreen, Lotto3StarWinningDetailsScreen
    from modules.lotto4star import Lotto4StarQueryScreen, Lotto4StarResultsScreen, Lotto4StarSavedScreen, Lotto4StarRepeatedNumbersScreen, Lotto4StarDuplicateDetailScreen, Lotto4StarWinningDetailsScreen
    
    print("[BOOTSTRAP] 10. Importing common modules")
    sys.stdout.flush()
    from modules.common import LotteryTypeScreen  # 新增這行

    print("[BOOTSTRAP] All imports completed successfully!")
    sys.stdout.flush()
except BaseException as e:
    print("CRITICAL IMPORT ERROR DURING STARTUP:")
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
    sys.stderr.flush()
    raise e

DEBUG = True  # 全域 DEBUG 變數，控制日誌輸出 True測試 False發佈

# 通用設定（適用所有平台）
Config.set('input', 'mouse', 'mouse,disable_multitouch')  # 關閉觸摸標記
Config.set('graphics', 'show_cursor', '1')               # 顯示系統默認鼠標（僅電腦有效）

def setup_logging():
    """設定全域日誌記錄器"""
    from kivy.utils import platform
    if platform == 'android':
        print("[BOOTSTRAP] Android platform detected, skipping custom root logging setup.")
        sys.stdout.flush()
        return
        
    log_level = logging.DEBUG if DEBUG else logging.INFO
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 取得根記錄器
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 移除所有現有的處理器，避免重複添加
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 1. 設定錯誤日誌檔案處理器 (FileHandler)
    # 這個處理器不論 DEBUG 模式為何都會啟用，專門記錄錯誤
    error_handler = logging.FileHandler('error.log', 'a', 'utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    logger.addHandler(error_handler)

    # 2. 如果是 DEBUG 模式，則額外設定控制台輸出 (StreamHandler)
    if DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)
    
    logging.info("日誌系統設定完成。")
    if DEBUG:
        logging.debug("目前為除錯模式，日誌將輸出到控制台。")
    else:
        logging.info("目前為發佈模式，僅錯誤日誌會寫入 error.log。")

class LotteryApp(App):
    # 彩券類型配置 (英文標識: 顯示名稱)
    LOTTERY_TYPES = {
        'power': '威力彩',
        'big': '大樂透',
        '539': '今彩539',
        '3star': '3星彩', 
        '4star': '4星彩'
    }

    def resource_path(self, relative_path):
        """獲取資源的絕對路徑"""
        base_path = os.getcwd()
        return os.path.join(base_path, relative_path)

    def build(self):
        # 註冊自定義組件
        Factory.register('LotteryImageButton', module='modules.common')
        Factory.register('AdBannerArea', module='modules.common')
        from modules.common import AdManager
        self.ad_manager = AdManager()
        
        # 檢查資料庫是否存在
        db_path = self.resource_path('data/lotto_history.db')
        if not os.path.exists(db_path):
            logging.warning("警告: 找不到資料庫文件，將使用空資料集")

        try:
            self._init_environment()
            self._check_resources()

            # 確保KV文件只加載一次
            if not hasattr(self, '_kv_loaded'):
                self._load_kv_files()
                self._kv_loaded = True
        
            # 初始化屏幕管理器
            sm = ScreenManager()
            self._register_screens(sm)
        
            # 加載威力彩歷史數據
            self.power_history = self._load_power_history()
        
            # 預加載資源
            Clock.schedule_once(self._preload_resources, 0.5)
        
            return sm
        except Exception as e:
            traceback.print_exc()
            return self._create_error_screen(str(e))

    def _load_kv_files(self):
        """加載所有KV文件，確保只加載一次"""
        kv_files = [
            'kv/common.kv',
            'kv/powerlotto.kv',
            'kv/biglotto.kv',
            'kv/lotto539.kv',
            'kv/lotto3star.kv',
            'kv/lotto4star.kv'
        ]
        
        for kv_file in kv_files:
            path = self.resource_path(kv_file)
            if os.path.exists(path):
                Builder.load_file(path)
            else:
                logging.warning(f"警告: 找不到KV文件 {path}")

        # 如果所有KV文件都找不到，使用備用界面
        if not any(os.path.exists(self.resource_path(f)) for f in kv_files):
            self._load_fallback_ui()

    def _init_environment(self):
        """初始化運行環境"""
        from kivy.utils import platform
        if platform not in ('android', 'ios'):
            Window.size = (360, 640)
        Window.clearcolor = get_color_from_hex('#121212')
        
        # 創建必要目錄
        for dir_name in ['kv', 'data', 'images', 'fonts']:
            os.makedirs(self.resource_path(dir_name), exist_ok=True)
        
        # 註冊中文字體
        font_path = self.resource_path('fonts/NotoSansTC-Regular.ttf')
        if os.path.exists(font_path):
            LabelBase.register(name='ChineseFont', fn_regular=font_path)
        else:
            logging.warning("警告：使用系統默認字體")
            # 嘗試使用其他可用字體
            available_fonts = ['simhei.ttf', 'msyh.ttc', 'arial.ttf']
            for font in available_fonts:
                if font in LabelBase._fonts:
                    LabelBase.register(name='ChineseFont', fn_regular=font)
                    logging.info(f"使用替代字體: {font}")
                    break

        # 初始化資料庫表格
        db_path = self.resource_path('data/lotto_history.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # custom_numbers 表格已移至 custom.db，此處不再創建
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"主資料庫初始化失敗: {str(e)}")
        
        # 初始化自選號資料庫
        custom_db_path = self.resource_path('data/custom.db')
        try:
            conn = sqlite3.connect(custom_db_path)
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lottery_type TEXT NOT NULL,
                num1 INTEGER, num2 INTEGER, num3 INTEGER,
                num4 INTEGER, num5 INTEGER, num6 INTEGER,
                special_num INTEGER,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            conn.close()
            logging.info("自選號資料庫初始化完成")
        except Exception as e:
            logging.error(f"自選號資料庫初始化失敗: {str(e)}")

    def _check_resources(self):
        """檢查圖片資源完整性"""
        missing = []
        required_images = [
            'logo.png',
            'power.png', 'power_pressed.png',
            'big.png', 'big_pressed.png',
            'lotto539.png', 'lotto539_pressed.png',
            'lotto3star.png', 'lotto3star_pressed.png',
            'lotto4star.png', 'lotto4star_pressed.png'
        ]
        
        for img in required_images:
            path = self.resource_path(f"images/{img}")
            if not os.path.exists(path):
                missing.append(img)
        
        if missing:
            logging.warning(f"缺少圖片資源: {missing}")
            # 創建占位圖片
            for img in missing:
                placeholder = self.resource_path(f"images/{img}")
                if not os.path.exists(placeholder):
                    with open(placeholder, 'wb') as f:
                        f.write(b'')  # 創建空文件作為占位符

    def _load_power_history(self):
        """從 SQLite 載入歷史數據"""
        db_path = self.resource_path('data/lotto_history.db')
        history = []
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.execute('PRAGMA journal_mode=WAL')   # 啟用 WAL 模式
                conn.execute('PRAGMA cache_size=-10000')  # 約10MB
                conn.execute('PRAGMA synchronous=NORMAL')  # 平衡安全與速度
                conn.row_factory = sqlite3.Row  # 使用欄位名存取
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT issue as 期別, 
                       date as 開獎日期,
                       num1 as 獎號1, num2 as 獎號2, num3 as 獎號3,
                       num4 as 獎號4, num5 as 獎號5, num6 as 獎號6,
                       special_num as 第二區
                FROM power_lotto
                ORDER BY date DESC
                ''')
                
                for row in cursor:
                    history.append({
                        '期別': row['期別'],
                        '開獎日期': row['開獎日期'],
                        '獎號': sorted([row[f'獎號{i}'] for i in range(1, 7)]),
                        '第二區': row['第二區']
                    })
                    
                conn.close()
            except Exception as e:
                logging.error(f"SQLite 讀取錯誤: {str(e)}")
        else:
            logging.warning(f"警告: 找不到資料庫文件 {db_path}")
            
        return history

    def _register_screens(self, sm):
        """動態註冊所有屏幕"""
        screens = [
            ('lottery_type', LotteryTypeScreen),
            ('power_query', PowerLottoQueryScreen),
            ('big_query', BigLottoQueryScreen),
            ('lotto539_query', Lotto539QueryScreen),
            ('3star_query', Lotto3StarQueryScreen),
            ('4star_query', Lotto4StarQueryScreen),
            ('power_result', PowerLottoResultScreen),
            ('power_saved', PowerLottoSavedScreen),
            ('power_duplicate', PowerLottoDuplicateScreen),
            ('power_duplicate_detail', PowerLottoDuplicateDetailScreen),
            ('power_winning_details', PowerLottoWinningDetailsScreen),
            ('biglotto', BigLottoQueryScreen),
            ('biglotto_results', BigLottoResultsScreen),
            ('biglotto_saved', BigLottoSavedScreen),
            ('biglotto_repeated_numbers', BigLottoRepeatedNumbersScreen),
            ('biglotto_duplicate_detail', BigLottoDuplicateDetailScreen),
            ('biglotto_winning_details', BigLottoWinningDetailsScreen),
            ('lotto539_result', Lotto539ResultScreen),
            ('lotto539_saved', Lotto539SavedScreen),
            ('lotto539_winning_details', Lotto539WinningDetailsScreen),
            ('lotto539_duplicate', Lotto539DuplicateScreen),
            ('lotto539_duplicate_detail', Lotto539DuplicateDetailScreen),
            ('lotto3star', Lotto3StarQueryScreen),
            ('lotto3star_results', Lotto3StarResultsScreen),
            ('lotto3star_saved', Lotto3StarSavedScreen),
            ('lotto3star_repeated_numbers', Lotto3StarRepeatedNumbersScreen),
            ('lotto3star_duplicate_detail', Lotto3StarDuplicateDetailScreen),
            ('lotto3star_winning_details', Lotto3StarWinningDetailsScreen),
            ('lotto4star', Lotto4StarQueryScreen),
            ('lotto4star_results', Lotto4StarResultsScreen),
            ('lotto4star_saved', Lotto4StarSavedScreen),
            ('lotto4star_repeated_numbers', Lotto4StarRepeatedNumbersScreen),
            ('lotto4star_duplicate_detail', Lotto4StarDuplicateDetailScreen),
            ('lotto4star_winning_details', Lotto4StarWinningDetailsScreen)
        ]
        
        for name, screen_class in screens:
            try:
                screen = screen_class(name=name)
                sm.add_widget(screen)
                logging.info(f"成功加載屏幕: {name}")
            except Exception as e:
                logging.error(f"加載屏幕失敗 {name}: {str(e)}")
                # 修正錯誤處理中的導入
                from kivy.uix.screenmanager import Screen
                from kivy.uix.label import Label
                error_screen = Screen(name=name)
                error_label = Label(
                    text=f"屏幕加載錯誤: {str(e)}",
                    font_name='ChineseFont',
                    color=(1, 0, 0, 1),
                    halign='center',
                    valign='middle'
                )
                error_screen.add_widget(error_label)
                sm.add_widget(error_screen)
                logging.info(f"已創建錯誤占位屏幕: {name}")

    def _preload_resources(self, dt):
        """後台預加載資源"""
        from kivy.core.image import Image as CoreImage
        # Mapping to English filenames
        img_mapping = {
            'power': 'power',
            'big': 'big',
            '539': 'lotto539',
            '3star': 'lotto3star',
            '4star': 'lotto4star'
        }
        for name in img_mapping:
            try:
                img_path = self.resource_path(f"images/{img_mapping[name]}.png")
                CoreImage(img_path, mipmap=True)
            except Exception as e:
                logging.error(f"預加載圖片失敗: {str(e)}")

    def _load_fallback_ui(self):
        """備用文字界面"""
        Builder.load_string('''
<LotteryTypeScreen>:
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: '請安裝資源文件'
            font_name: 'ChineseFont'
''')

    def _create_error_screen(self, error_msg):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(
            text='應用初始化錯誤',
            font_name='ChineseFont',
            color=(1, 0, 0, 1)
        ))
        layout.add_widget(Label(
            text=error_msg,
            font_name='ChineseFont'
        ))
        return layout

    def on_start(self):
        """Called when Kivy starts running and window is displayed."""
        self.sync_popup = SyncProgressPopup()
        self.sync_popup.open()
        
        worker = SyncWorker(self)
        self.sync_thread = threading.Thread(target=worker.run)
        self.sync_thread.daemon = True
        self.sync_thread.start()

    def show_retry_popup(self, file_name, worker):
        """Show the download retry/skip confirmation popup on the main thread."""
        popup = RetryConfirmPopup(
            file_name=file_name,
            on_yes=lambda: worker.set_user_decision('retry'),
            on_no=lambda: worker.set_user_decision('abort')
        )
        popup.open()

    def show_update_popup(self, remote_ver, worker):
        """Show the app version update confirmation popup on the main thread."""
        popup = AppUpdatePopup(
            remote_ver=remote_ver,
            on_later=lambda: worker.set_user_decision('later'),
            on_update=lambda: worker.set_user_decision('update')
        )
        popup.open()

    def update_sync_ui(self, status, value, detail):
        """Update progress popup content safely from worker thread."""
        if hasattr(self, 'sync_popup') and self.sync_popup:
            self.sync_popup.update_status(status, value, detail)

    def dismiss_sync_popup(self):
        """Dismiss progress popup safely."""
        if hasattr(self, 'sync_popup') and self.sync_popup:
            self.sync_popup.dismiss()
            self.sync_popup = None

    def reload_history_data(self):
        """Reload lottery history cache after successful sync."""
        try:
            self.power_history = self._load_power_history()
            logging.info("Successfully reloaded power lotto history data after sync.")
        except Exception as e:
            logging.error(f"Error reloading history data: {e}")

if __name__ == '__main__':
    try:
        setup_logging()
        LotteryApp().run()
    except BaseException as e:
        import traceback
        import sys
        print("CRITICAL RUNTIME ERROR:")
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        sys.stderr.flush()
        raise e