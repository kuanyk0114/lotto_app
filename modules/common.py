from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.properties import DictProperty, NumericProperty, StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
import sqlite3
import os
import threading
from contextlib import contextmanager
import logging
logger = logging.getLogger(__name__)



def show_popup(title, text):
    content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
    
    # 支援多行文字顯示
    text_label = Label(
        text=text, 
        font_name='ChineseFont', 
        font_size=dp(16),
        text_size=(None, None),  # 讓文字自動調整寬度
        halign='center',
        valign='middle'
    )
    content.add_widget(text_label)
    
    close_button = Button(text='關閉', font_name='ChineseFont', size_hint_y=None, height=dp(50))
    content.add_widget(close_button)

    popup = Popup(title=title,
                  title_font='ChineseFont',
                  content=content,
                  size_hint=(0.7, 0.3))
    
    close_button.bind(on_press=popup.dismiss)
    popup.open()


class DatabaseManager:
    """統一的資料庫管理類別"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            # 主資料庫（開獎歷史）
            self.main_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto_history.db')
            # 自選號資料庫
            self.custom_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'custom.db')
            # 保持向後相容性
            self.db_path = self.main_db_path
            self.initialized = True
    
    @contextmanager
    def get_connection(self, db_type='main'):
        """取得指定資料庫連接的上下文管理器"""
        conn = None
        try:
            if db_type == 'custom':
                # 確保自選號資料庫存在
                self._ensure_custom_db_exists()
                conn = sqlite3.connect(self.custom_db_path)
            else:
                conn = sqlite3.connect(self.main_db_path)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _ensure_custom_db_exists(self):
        """確保自選號資料庫和表格存在"""
        logger.debug(f"檢查自選號資料庫: {self.custom_db_path}")
        logger.debug(f"資料庫是否存在: {os.path.exists(self.custom_db_path)}")
        
        if not os.path.exists(self.custom_db_path):
            # 創建資料庫和表格
            logger.info("創建新的自選號資料庫...")
            conn = sqlite3.connect(self.custom_db_path)
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
            logger.info(f"已創建自選號資料庫: {self.custom_db_path}")
        else:
            # 檢查表格是否存在
            logger.debug("檢查現有資料庫中的表格...")
            conn = sqlite3.connect(self.custom_db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='custom_numbers'
            """)
            table_exists = cursor.fetchone()
            logger.debug(f"custom_numbers 表格是否存在: {table_exists is not None}")
            
            if not table_exists:
                # 表格不存在，創建它
                logger.info("創建 custom_numbers 表格...")
                cursor.execute('''
                CREATE TABLE custom_numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lottery_type TEXT NOT NULL,
                    num1 INTEGER, num2 INTEGER, num3 INTEGER,
                    num4 INTEGER, num5 INTEGER, num6 INTEGER,
                    special_num INTEGER,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                conn.commit()
                logger.info("已在現有資料庫中創建 custom_numbers 表格")
            else:
                logger.debug("custom_numbers 表格已存在")
            conn.close()
    
    def execute_query(self, query, params=None):
        """執行查詢並返回結果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_insert(self, query, params=None):
        """執行插入操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def execute_delete(self, query, params=None):
        """執行刪除操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def execute_custom_query(self, query, params=None):
        """執行自選號資料庫查詢"""
        logger.debug(f"執行自選號查詢 - 資料庫路徑: {self.custom_db_path}")
        logger.debug(f"SQL查詢: {query}")
        logger.debug(f"參數: {params}")
        
        with self.get_connection('custom') as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            logger.debug(f"查詢結果: {len(result)} 筆資料")
            return result
    
    def execute_custom_insert(self, query, params=None):
        """執行自選號資料庫插入"""
        logger.debug(f"執行自選號插入 - 資料庫路徑: {self.custom_db_path}")
        logger.debug(f"SQL查詢: {query}")
        logger.debug(f"參數: {params}")
        
        with self.get_connection('custom') as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def execute_custom_delete(self, query, params=None):
        """執行自選號資料庫刪除"""
        with self.get_connection('custom') as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount

class ResultBall(BoxLayout):
    """結果顯示用的彩球組件"""
    number = NumericProperty(0)
    area = NumericProperty(1)  # 1=第一區, 2=第二區
    selected = BooleanProperty(False)  # 是否在自選號中
    lotto_type = StringProperty('powerlotto') # 'powerlotto' or 'biglotto'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(30), dp(30))
        self.bind(
            number=self.update_canvas,
            area=self.update_canvas,
            selected=self.update_canvas,
            pos=self.update_canvas,
            size=self.update_canvas
        )
        Clock.schedule_once(self.update_canvas, 0.1)

    def update_canvas(self, *args):
        """更新彩球外觀"""
        self.canvas.before.clear()

        with self.canvas.before:
            # 調試輸出（可以移除）
            # logger.debug(f"ResultBall: number={self.number}, selected={self.selected}, area={self.area}, lotto_type='{self.lotto_type}'")
            
            # 預設顏色
            color_hex = '#FFC107'  # 預設黃色
            
            if self.lotto_type in ('power', 'powerlotto'):
                if self.area == 1:
                    color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃
                else:
                    color_hex = '#448AFF' if self.selected else '#80DEEA' # 深藍/青
            elif self.lotto_type in ['biglotto', 'big']:
                if self.area == 2:  # 特別號
                    color_hex = '#448AFF' if self.selected else '#80DEEA' # 藍/青
                else:  # 一般號
                    color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃
            elif self.lotto_type in ['lotto539', '539']:
                color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃
            elif self.lotto_type in ['lotto3star', 'lotto4star', '3star', '4star']:
                color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃

            # logger.debug(f"最終顏色: {color_hex}")
            Color(*get_color_from_hex(color_hex))
            d = min(self.width, self.height) * 0.9
            x = self.x + (self.width - d) / 2
            y = self.y + (self.height - d) / 2
            Ellipse(pos=(x, y), size=(d, d))

        if not self.children:
            label = Label(
                text=str(self.number),
                font_name='ChineseFont',
                font_size=dp(12),
                color=(0, 0, 0, 1),
                bold=True
            )
            self.add_widget(label)
class ClickableBoxLayout(ButtonBehavior, BoxLayout):
    pass


class BallButton(ButtonBehavior, Label):
    selected = BooleanProperty(False)
    area = NumericProperty(1)
    lotto_type = StringProperty('powerlotto') # 'powerlotto', 'biglotto', 'lotto539', 'lotto3star', 'lotto4star'
    position = StringProperty('')  # 用於三星彩和四星彩的位置標識 ('hundreds', 'tens', 'units', 'thousands')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = 'ChineseFont'
        self.font_size = dp(16)
        self.color = (0, 0, 0, 1)  # 黑色字體
        self.bold = True
        self.halign = 'center'
        self.valign = 'middle'
        self._last_touch_time = 0.0  # 用於過濾 Android 重複觸控事件的冷卻時間
        self.bind(pos=self.update_canvas, size=self.update_canvas, selected=self.update_canvas)
        self.update_canvas()

    def set_text(self, text):
        """安全地設置球組件的文字，與舊代碼相容"""
        self.text = text

    def collide_point(self, x, y):
        # 1. 標準碰撞檢測（適用於電腦桌面端及正常 Android 裝置）
        if self.x <= x <= self.right and self.y <= y <= self.top:
            return True
            
        # 2. 針對部分高解析度 Android 裝置的座標系統不一致（觸控座標為 dp，但元件座標為像素）進行匹配
        try:
            from kivy.metrics import Metrics
            from kivy.core.window import Window
            
            density = Metrics.density
            if density and density != 1.0:
                # 測試縮放後的座標
                sx = x * density
                sy = y * density
                if self.x <= sx <= self.right and self.y <= sy <= self.top:
                    return True
                    
                # 測試縮放且 Y 軸翻轉後的座標（Android 螢幕頂部為原點 vs Kivy 螢幕底部為原點）
                sy_inv = Window.height - (y * density)
                if self.x <= sx <= self.right and self.y <= sy_inv <= self.top:
                    return True
        except Exception as e:
            logger.error(f"BallButton collide_point 錯誤: {e}")
            
        return False


    def on_touch_down(self, touch):
        collide = self.collide_point(*touch.pos)
        logger.debug(f"[BallTouch] {self.lotto_type} BallButton {self.text} on_touch_down: pos={touch.pos}, collide={collide}")
        if collide:
            import time
            current_time = time.time()
            if current_time - self._last_touch_time < 0.1:
                logger.debug(f"[BallTouch] {self.lotto_type} BallButton {self.text} on_touch_down ignored (cooldown: {current_time - self._last_touch_time:.4f}s)")
                return False
            self._last_touch_time = current_time
            touch.grab(self)
            return True
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            collide = self.collide_point(*touch.pos)
            logger.debug(f"[BallTouch] {self.lotto_type} BallButton {self.text} on_touch_up: pos={touch.pos}, collide={collide}, grabbed=True")
            if collide:
                logger.debug(f"[BallTouch] {self.lotto_type} BallButton {self.text} CLICKED! Toggling selected from {self.selected} to {not self.selected}")
                self.selected = not self.selected
            return True
        return False


    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # 根據不同彩種設定顏色
            if self.lotto_type in ('power', 'powerlotto'):
                if self.area == 1:
                    color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃
                else:
                    color_hex = '#448AFF' if self.selected else '#80DEEA' # 深藍/青
            elif self.lotto_type in ['biglotto', 'big']:
                if self.area == 2:  # 特別號
                    color_hex = '#448AFF' if self.selected else '#80DEEA' # 深藍/青
                else:  # 一般號
                    color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃
            elif self.lotto_type in ['lotto539', '539']:
                color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃
            elif self.lotto_type in ['lotto3star', 'lotto4star', '3star', '4star']:
                color_hex = '#FF5722' if self.selected else '#FFC107' # 橙紅/琥珀黃
            else:
                # 預設顏色
                color_hex = '#FF5722' if self.selected else '#FFC107'
                
            Color(*get_color_from_hex(color_hex))
            d = min(self.width, self.height)
            Ellipse(pos=(self.center_x - d / 2, self.center_y - d / 2), size=(d, d))


# 在 common.py 頂部新增以下類別
class LoadingPopup(Popup):
    """通用載入提示框，所有彩種共用"""
    def __init__(self, title='查詢中', **kwargs):
        super().__init__(**kwargs)
        self.title = title
        # 根據文字長度動態調整寬度，最小0.5，最大0.8
        title_length = len(title)
        width_ratio = max(0.5, min(0.8, 0.4 + title_length * 0.02))
        self.size_hint = (width_ratio, 0.3)
        self.auto_dismiss = False
        
        # 動態顯示的點
        self.dot_count = 1
        self.max_dots = 5
        self.animation_event = None
    
    def on_open(self):
        """打開彈窗時啟動動畫"""
        self.animation_event = Clock.schedule_interval(self.update_loading_text, 0.3)
    
    def update_loading_text(self, dt):
        """更新載入文字"""
        self.dot_count = (self.dot_count % self.max_dots) + 1
        self.ids.loading_label.text = self.title + '.' * self.dot_count
    
    def on_dismiss(self):
        """取消動畫計時器"""
        if self.animation_event:
            Clock.unschedule(self.animation_event)
        return super().on_dismiss()


class LotteryImageButton(ButtonBehavior, Image):
    """高級圖片按鈕組件"""
    source_normal = StringProperty('')
    source_down = StringProperty('')
    animation_scale = NumericProperty(1.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            source_normal=self._update_texture,
            source_down=self._update_texture
        )
        Clock.schedule_once(self._update_texture, 0.1)
    
    def _update_texture(self, *args):
        if self.source_normal:
            self.source = self.source_normal
    
    def on_press(self):
        self.source = self.source_down if self.source_down else self.source_normal
        anim = Animation(animation_scale=0.95, duration=0.08, t='out_quad')
        anim.start(self)
    
    def on_release(self):
        self.source = self.source_normal
        anim = Animation(animation_scale=1.0, duration=0.4, t='out_elastic')
        anim.start(self)


class BaseLotteryQueryScreen(Screen):
    """基礎彩種查詢界面 - 包含共用的查詢、儲存、載入邏輯"""
    
    def on_touch_down(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_up(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DatabaseManager()
        self.loading_popup = None
        
    # 抽象屬性，子類必須實作
    @property
    def lottery_type(self):
        """彩種類型標識"""
        raise NotImplementedError("子類必須實作 lottery_type 屬性")
    
    @property
    def table_name(self):
        """資料庫表名"""
        raise NotImplementedError("子類必須實作 table_name 屬性")
    
    @property
    def max_numbers(self):
        """最大選號數量"""
        raise NotImplementedError("子類必須實作 max_numbers 屬性")
    
    def get_selected_numbers(self):
        """取得選中的號碼 - 子類實作"""
        raise NotImplementedError("子類必須實作 get_selected_numbers 方法")
    
    def validate_selection(self):
        """驗證選號是否有效 - 子類可覆寫"""
        numbers = self.get_selected_numbers()
        if not numbers:
            return False, "請至少選擇1個號碼"
        return True, ""
    
    def save_custom_numbers(self):
        """統一的自選號儲存邏輯"""
        logger.debug(f"=== 通用方法被調用 ===")
        logger.debug(f"彩種: {self.lottery_type}")
        logger.debug(f"類別: {self.__class__.__name__}")
        logger.warning(f"⚠️ 警告：這是通用方法，不是威力彩專用方法！")
        
        # 檢查是否有專門的儲存驗證方法
        if hasattr(self, 'validate_for_save'):
            is_valid, error_msg = self.validate_for_save()
        else:
            is_valid, error_msg = self.validate_selection()
            
        if not is_valid:
            logger.warning(f"驗證失敗: {error_msg}")
            show_popup('提示', error_msg)
            return
        
        try:
            numbers = self.get_selected_numbers()
            logger.debug(f"選中的號碼: {numbers}")
            
            # 準備插入參數
            params = [self.lottery_type] + list(numbers)
            logger.debug(f"插入參數: {params}")
            
            # 根據號碼數量構建SQL
            placeholders = ', '.join(['?'] * len(numbers))
            columns = ', '.join([f'num{i+1}' for i in range(len(numbers))])
            
            query = f'''
                INSERT INTO custom_numbers (lottery_type, {columns})
                VALUES (?{', ?' * len(numbers)})
            '''
            logger.debug(f"SQL查詢: {query}")
            
            # 檢查 db_manager 是否存在
            if not hasattr(self, 'db_manager'):
                logger.error("❌ 錯誤: 沒有 db_manager 屬性")
                show_popup('錯誤', '資料庫管理器未初始化')
                return
                
            logger.debug(f"db_manager 類型: {type(self.db_manager)}")
            
            # 使用自選號資料庫
            result = self.db_manager.execute_custom_insert(query, params)
            logger.info(f"插入結果 ID: {result}")
            show_popup('成功', '自選號碼已儲存')
        except Exception as e:
            logger.exception(f"❌ 儲存錯誤: {str(e)}")
            show_popup('錯誤', f'通用方法儲存失敗: {e}')
    
    def query_history(self):
        """統一的歷史查詢邏輯"""
        is_valid, error_msg = self.validate_selection()
        if not is_valid:
            show_popup("查詢失敗", error_msg)
            return
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title=f'{self.get_lottery_display_name()}查詢中')
        self.loading_popup.open()
        
        # 延遲執行查詢
        Clock.schedule_once(lambda dt: self._perform_query(), 0.1)
    
    def _perform_query(self):
        """執行查詢並跳轉到結果頁面"""
        try:
            # 準備查詢參數
            query_params = self.prepare_query_params()
            
            # 傳遞參數到結果屏幕
            result_screen_name = self.get_result_screen_name()
            result_screen = self.manager.get_screen(result_screen_name)
            result_screen.query_params = query_params
            result_screen.sort_order = 'DESC'  # 統一使用大寫，與其他彩種一致
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
            # 切換到結果屏幕
            self.manager.current = result_screen_name
        except Exception as e:
            error_msg = f"查詢失敗: {str(e)}"
            logger.error(error_msg)
            self.loading_popup.dismiss()
            show_popup("錯誤", error_msg)
    
    def prepare_query_params(self):
        """準備查詢參數 - 子類可覆寫"""
        return {'numbers': self.get_selected_numbers()}
    
    def get_lottery_display_name(self):
        """取得彩種顯示名稱 - 子類可覆寫"""
        lottery_names = {
            'power': '威力彩',
            'big': '大樂透', 
            '539': '今彩539',
            '3star': '三星彩',
            '4star': '四星彩'
        }
        return lottery_names.get(self.lottery_type, '彩券')
    
    def get_result_screen_name(self):
        """取得結果頁面名稱 - 子類可覆寫"""
        screen_names = {
            'power': 'power_result',
            'big': 'biglotto_results',
            '539': 'lotto539_result',
            '3star': 'lotto3star_result',
            '4star': 'lotto4star_result'
        }
        return screen_names.get(self.lottery_type, 'result')
    
    def show_saved_numbers(self):
        """顯示已儲存的自選號"""
        saved_screen_names = {
            'power': 'power_saved',
            'big': 'biglotto_saved',
            '539': 'lotto539_saved',
            '3star': 'lotto3star_saved',
            '4star': 'lotto4star_saved'
        }
        screen_name = saved_screen_names.get(self.lottery_type)
        if screen_name:
            self.manager.current = screen_name


class BaseLotterySavedScreen(Screen):
    """基礎自選號管理界面 - 支援分頁顯示"""
    saved_numbers = ListProperty([])
    
    def on_touch_down(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_up(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DatabaseManager()
        
        # 分頁相關屬性
        self.page_size = 20  # 每頁顯示20筆自選號
        self.current_page = 0
        self.all_results = []  # 完整的自選號列表
        self.displayed_results = []  # 當前顯示的自選號
        self.has_more_data = False
        self.is_loading_more = False
        self.is_scrolling = False
        self._scroll_events_disabled = False
    
    @property
    def lottery_type(self):
        """彩種類型標識"""
        raise NotImplementedError("子類必須實作 lottery_type 屬性")
    
    def on_pre_enter(self):
        """進入屏幕前加載數據"""
        self.load_saved_numbers()
        self.populate_saved_list()
    
    def load_saved_numbers(self):
        """從資料庫載入自選號並初始化分頁"""
        self.saved_numbers = []
        self.all_results = []
        
        try:
            query = '''
                SELECT id, num1, num2, num3, num4, num5, num6, special_num, created_time
                FROM custom_numbers 
                WHERE lottery_type = ?
                ORDER BY created_time DESC
            '''
            # 使用自選號資料庫
            rows = self.db_manager.execute_custom_query(query, (self.lottery_type,))
            
            for row in rows:
                # 過濾掉 None 值，但保留特別號的處理
                numbers = [row[i] for i in range(1, 7) if row[i] is not None]  # num1-num6
                special_num = row[7] if row[7] is not None else None  # special_num
                
                # 判斷是否需要排序
                # 三星彩和四星彩的號碼有位置順序性，不應排序
                if self.lottery_type in ['3star', '4star']:
                    final_numbers = numbers
                else:
                    final_numbers = sorted(numbers)

                item = {
                    'id': row[0],
                    'numbers': final_numbers,
                    'created_time': row[8]
                }
                # 如果有特別號
                if special_num is not None:
                    item['special'] = special_num
                
                self.saved_numbers.append(item)
                self.all_results.append(item)
                
            logger.info(f"{self.__class__.__name__} 載入自選號: 總筆數={len(self.all_results)}")
                
        except Exception as e:
            logger.exception(f"載入自選號失敗: {str(e)}")
            self.handle_database_error(e)
    
    def populate_saved_list(self):
        """初始化分頁並載入第一頁"""
        # 初始化分頁
        self._initialize_pagination()
        # 載入第一頁
        self._load_first_page()
    
    def create_saved_item_widget(self, item, index):
        """建立自選號項目widget - 子類可覆寫"""
        box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5),
            padding=(dp(10), dp(5))
        )
        
        # 號碼區域
        numbers_box = BoxLayout(
            orientation='horizontal',
            spacing=dp(5),
            size_hint_x=0.8
        )
        
        for num in item['numbers']:
            ball = ResultBall(number=num, area=1, selected=True, lotto_type=self.lottery_type)
            numbers_box.add_widget(ball)
        
        # 特別號（如果有）
        if 'special' in item:
            ball = ResultBall(number=item['special'], area=2, selected=True, lotto_type=self.lottery_type)
            numbers_box.add_widget(ball)
        
        box.add_widget(numbers_box)
        box.add_widget(Widget(size_hint_x=0.2))  # 空白區域
        
        # 綁定觸摸事件
        box.bind(on_touch_down=lambda instance, touch, idx=index: 
                self.on_saved_number_touch(instance, touch, idx))
        
        return box
    
    def on_saved_number_touch(self, instance, touch, index):
        """處理自選號觸摸事件"""
        if instance.collide_point(*touch.pos) and touch.button == 'left':
            if touch.is_double_tap:
                self.use_saved_number(index)
                return True
            elif not touch.is_mouse_scrolling:
                touch.ud['saved_number_index'] = index
                touch.ud['long_press_trigger'] = Clock.schedule_once(
                    lambda dt: self._handle_long_press(touch, index), 1
                )
                return True
        return False
    
    def _handle_long_press(self, touch, index):
        """處理長按事件"""
        if 'saved_number_index' in touch.ud:
            self.show_delete_confirmation(index)
            del touch.ud['saved_number_index']
    
    def on_touch_up(self, touch):
        """處理觸摸釋放事件"""
        super().on_touch_up(touch)
        
        if hasattr(touch, 'ud') and 'saved_number_index' in touch.ud:
            if 'long_press_trigger' in touch.ud:
                Clock.unschedule(touch.ud['long_press_trigger'])
                del touch.ud['long_press_trigger']
            
            if 'long_press_triggered' not in touch.ud:
                index = touch.ud['saved_number_index']
                self.use_saved_number(index)
            
            del touch.ud['saved_number_index']
        return True
    
    def show_delete_confirmation(self, index):
        """顯示刪除確認對話框"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        target = self.saved_numbers[index]
        numbers_text = ', '.join(map(str, target['numbers']))
        if 'special' in target:
            numbers_text += f" (特別號: {target['special']})"
        
        numbers_label = Label(
            text=f"號碼: {numbers_text}",
            font_name='ChineseFont',
            halign='center'
        )
        content.add_widget(numbers_label)
        
        content.add_widget(Label(
            text='確定要刪除此自選號嗎？',
            font_name='ChineseFont',
            font_size=dp(16),
            halign='center'
        ))
        
        btn_box = BoxLayout(spacing=10, size_hint_y=None, height=dp(50))
        btn_yes = Button(
            text='確定刪除',
            font_name='ChineseFont',
            background_color=get_color_from_hex('#FF5252')
        )
        btn_no = Button(
            text='取消',
            font_name='ChineseFont'
        )
        
        btn_box.add_widget(btn_no)
        btn_box.add_widget(btn_yes)
        content.add_widget(btn_box)
        
        popup = Popup(
            title_font='ChineseFont',
            title='請確認',
            title_size=dp(18),
            content=content,
            size_hint=(0.7, 0.3),
            separator_height=0,
            background_color=(1, 1, 1, 1)
        )
        
        btn_no.bind(on_press=popup.dismiss)
        btn_yes.bind(on_press=lambda x: self._confirm_delete(index, popup))
        popup.open()
    
    def _confirm_delete(self, index, popup):
        """確認刪除操作"""
        popup.dismiss()
        if 0 <= index < len(self.saved_numbers):
            self._delete_from_database(index)
            self.load_saved_numbers()
            self.populate_saved_list()
    
    def _delete_from_database(self, index):
        """從資料庫刪除指定自選號"""
        try:
            record_id = self.saved_numbers[index].get('id')
            if record_id:
                query = 'DELETE FROM custom_numbers WHERE id = ?'
                # 使用自選號資料庫
                self.db_manager.execute_custom_delete(query, (record_id,))
        except Exception as e:
            logger.exception(f"刪除失敗: {str(e)}")
            show_popup("錯誤", "刪除自選號時發生錯誤")
    
    def use_saved_number(self, index):
        """使用選中的自選號 - 子類必須實作"""
        raise NotImplementedError("子類必須實作 use_saved_number 方法")
    
    def back_to_query(self):
        """返回查詢界面 - 子類可覆寫"""
        query_screen_names = {
            'power': 'power_query',
            'big': 'biglotto',
            '539': 'lotto539_query',
            '3star': 'lotto3star',
            '4star': 'lotto4star'
        }
        screen_name = query_screen_names.get(self.lottery_type)
        if screen_name:
            self.manager.current = screen_name
    
    # ==================== 分頁相關方法實現 ====================
    
    def _initialize_pagination(self):
        """初始化分頁設定"""
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = len(self.all_results) > self.page_size
        self.is_loading_more = False
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if not self.all_results:
            self.displayed_results = []
            self.has_more_data = False
        else:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.has_more_data = len(self.all_results) > self.page_size
            self.current_page = 1
        
        self._update_result_list()
    
    def _perform_load_next_page(self):
        """載入下一頁資料"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        self.is_loading_more = True
        
        # 計算下一頁的資料範圍
        start_index = len(self.displayed_results)
        end_index = min(start_index + self.page_size, len(self.all_results))
        
        if start_index < len(self.all_results):
            new_records = self.all_results[start_index:end_index]
            self.displayed_results.extend(new_records)
            self.current_page += 1
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            
            # 更新UI
            self._append_to_result_list(new_records)
        
        self.is_loading_more = False
    
    def on_scroll_start(self, scroll_view, touch):
        """滾動開始事件"""
        self.is_scrolling = True
    
    def on_scroll_move(self, scroll_view, touch):
        """滾動移動事件"""
        pass
    
    def on_scroll_end(self, scroll_view, touch):
        """滾動結束事件"""
        self.is_scrolling = False
        
        # 檢查是否滾動到底部
        if scroll_view.scroll_y <= 0.1 and self.has_more_data and not self.is_loading_more:
            Clock.schedule_once(lambda dt: self._perform_load_next_page(), 0.1)
    
    def handle_database_error(self, error):
        """處理資料庫錯誤"""
        logger.error(f"資料庫錯誤: {str(error)}")
        show_popup('錯誤', f'資料庫操作失敗: {str(error)}')
    
    def handle_ui_error(self, error):
        """處理UI錯誤"""
        logger.error(f"UI錯誤: {str(error)}")
        show_popup('錯誤', f'界面更新失敗: {str(error)}')
    
    def _update_result_list(self):
        """更新結果列表（分頁版本）- 實現基類抽象方法"""
        try:
            saved_list = self.ids.saved_list
            saved_list.clear_widgets()
            
            if not self.displayed_results:
                saved_list.add_widget(Label(
                    text="沒有儲存的自選號",
                    font_name='ChineseFont',
                    font_size=dp(18),
                    color=get_color_from_hex('#FF0000'),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(100)
                ))
                return

            # 顯示當前已載入的所有資料
            total_height = 0
            for index, item in enumerate(self.displayed_results):
                box = self.create_saved_item_widget(item, index)
                saved_list.add_widget(box)
                total_height += dp(50)
            
            # 添加載入更多指示器
            self._add_load_more_indicator()
            
            # 設定總高度
            saved_list.height = total_height + (dp(60) if self.has_more_data else 0)
            
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 更新結果列表錯誤: {str(e)}")
            self.handle_ui_error(e)

    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            saved_list = self.ids.saved_list
            
            # 保存當前滾動位置
            scroll_view = None
            current_absolute_scroll = 0
            
            # 尋找ScrollView - 在自選號頁面中通過screen.ids.scroll_view訪問
            if hasattr(self, 'ids') and hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
            
            if scroll_view:
                content_height_before = saved_list.height
                viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, content_height_before - viewport_height)
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 添加新記錄
            start_index = len(self.displayed_results) - len(new_records)
            for i, item in enumerate(new_records):
                box = self.create_saved_item_widget(item, start_index + i)
                saved_list.add_widget(box)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 更新總高度
            total_height = len(self.displayed_results) * dp(50)
            saved_list.height = total_height + (dp(60) if self.has_more_data else 0)
            
            # 恢復滾動位置
            if scroll_view:
                Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll, scroll_view), 0.1)
                
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 追加結果錯誤: {str(e)}")
            self.handle_ui_error(e)

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'saved_list'):
            return
            
        load_more_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            padding=(dp(10), dp(10))
        )
        
        # 根據是否還有更多資料設定不同的文字和透明度
        if self.has_more_data:
            text = "滑動到底部載入更多"
            opacity = 0.7
        else:
            text = "已顯示全部資料"
            opacity = 0.5
        
        load_more_label = Label(
            text=text,
            font_name='ChineseFont',
            font_size=dp(14),
            color=get_color_from_hex('#888888'),
            halign='center',
            valign='middle',
            opacity=opacity
        )
        load_more_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        
        load_more_box.add_widget(load_more_label)
        self.ids.saved_list.add_widget(load_more_box)
        
        # 儲存引用以便後續更新
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'saved_list') and self.load_more_indicator in self.ids.saved_list.children:
            self.ids.saved_list.remove_widget(self.load_more_indicator)

    def _restore_scroll_position_absolute(self, target_absolute_scroll, scroll_view):
        """恢復到指定的絕對滾動位置"""
        try:
            content_height = self.ids.saved_list.height
            viewport_height = scroll_view.height
            
            if content_height > viewport_height:
                max_scroll_distance = content_height - viewport_height
                new_scroll_y = 1 - (target_absolute_scroll / max_scroll_distance)
                new_scroll_y = max(0, min(1, new_scroll_y))
                scroll_view.scroll_y = new_scroll_y
            else:
                scroll_view.scroll_y = 1
                
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 恢復滾動位置錯誤: {str(e)}")


class LotteryTypeScreen(Screen):
    """主菜單界面"""
    btn_states = DictProperty({'power':1, 'big':1, '539':1, '3star':1, '4star':1})
    
    def on_touch_down(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_up(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._init_buttons, 0.5)
    
    def _init_buttons(self, dt):
        """初始化按鈕狀態"""
        for btn_type in self.btn_states:
            btn = self.ids.get(f"{btn_type}_btn")
            if btn:
                btn.disabled = False
                Animation(opacity=1, duration=0.6).start(btn)
    
    def show_privacy_policy(self):
        """顯示隱私權政策及免責聲明彈窗"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        
        # 標題
        title_label = Label(
            text='隱私權政策及免責聲明',
            font_name='ChineseFont',
            font_size=dp(18),
            bold=True,
            size_hint_y=None,
            height=dp(40),  # 增加標題高度
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle'
        )
        content.add_widget(title_label)
        
        # 滾動區域
        scroll = ScrollView()
        scroll_content = BoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None, padding=(dp(15), dp(10)))
        scroll_content.bind(minimum_height=scroll_content.setter('height'))
        
        # 內容結構
        content_sections = [
            {
                'title': '免責聲明：',
                'items': [
                    '本APP使用之彩券歷史資料來源自台灣彩券官網公開資訊，僅供參考用途，台灣彩券公司不保證資料正確性，實際開獎結果以台灣彩券公司公告為準。',
                    '本APP與台灣彩券公司無關，所提供分析結果僅供參考。',
                    '使用本APP即表示您同意上述條款。如有疑問請聯繫開發者。'
                ]
            },
            {
                'title': '隱私權政策：',
                'items': [
                    '本APP不會收集任何個人資料。',
                    '所有選號記錄僅儲存在您的裝置本地。',
                    '我們不會將您的使用資料傳送到外部伺服器。',
                    '本APP僅讀取公開的彩券開獎資料。'
                ]
            }
        ]
        
        for section in content_sections:
            # 添加區段標題
            section_title = Label(
                text=section['title'],
                font_name='ChineseFont',
                font_size=dp(16),
                bold=True,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 0.5, 1),  # 淡黃色標題
                halign='left',
                valign='middle'
            )
            def update_title_text_size(instance, value):
                instance.text_size = (instance.width - dp(30), None)
            section_title.bind(width=update_title_text_size)
            scroll_content.add_widget(section_title)
            
            # 添加區段內容
            for item in section['items']:
                label = Label(
                    text=item,
                    font_name='ChineseFont',
                    font_size=dp(14),
                    halign='left',
                    valign='top',
                    size_hint_y=None,
                    height=dp(80) if len(item) > 50 else dp(40),
                    color=(1, 1, 1, 1)
                )
                # 設定文字自動換行
                def update_text_size(instance, value):
                    instance.text_size = (instance.width - dp(30), None)
                label.bind(width=update_text_size)
                scroll_content.add_widget(label)
            
            # 添加區段間距
            spacer = Label(
                text='',
                size_hint_y=None,
                height=dp(10)
            )
            scroll_content.add_widget(spacer)
        
        scroll.add_widget(scroll_content)
        content.add_widget(scroll)
        
        # 關閉按鈕
        close_button = Button(
            text='我已了解',
            font_name='ChineseFont',
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#2196F3')
        )
        content.add_widget(close_button)
        
        # 創建彈窗
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.95, 0.85),  # 增加彈窗大小
            separator_height=0,
            background_color=(0.2, 0.2, 0.2, 1)
        )
        
        close_button.bind(on_press=popup.dismiss)
        popup.open()


# ==================== 新增的共用基類 ====================

class BasePaginationMixin:
    """分頁顯示功能基類"""
    
    # 分頁相關屬性
    current_page = NumericProperty(0)
    page_size = NumericProperty(30)
    all_results = ListProperty([])  # 完整查詢結果
    displayed_results = ListProperty([])  # 當前顯示的結果
    has_more_data = BooleanProperty(False)
    is_loading_more = BooleanProperty(False)
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > self.page_size
        logger.debug(f"{self.__class__.__name__} 分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"{self.__class__.__name__} 第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self.has_more_data = False
            self._update_result_list()  # 顯示無資料
    
    def _load_next_page(self):
        """載入下一頁資料"""
        if self.is_loading_more or not self.has_more_data:
            return
        
        self.is_loading_more = True
        self._show_loading_indicator()
        Clock.schedule_once(lambda dt: self._perform_load_next_page(), 0.2)
    
    def _perform_load_next_page(self):
        """實際執行下一頁載入"""
        try:
            start_index = len(self.displayed_results)
            end_index = min(start_index + self.page_size, len(self.all_results))
            
            if start_index < len(self.all_results):
                # 添加下一頁資料
                next_page_data = self.all_results[start_index:end_index]
                self.displayed_results.extend(next_page_data)
                self.current_page += 1
                
                # 更新顯示
                self._append_to_result_list(next_page_data)
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_results)
                
                logger.debug(f"{self.__class__.__name__} 載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 載入下一頁錯誤: {str(e)}")
            self.handle_ui_error(e) if hasattr(self, 'handle_ui_error') else show_popup("錯誤", "載入更多資料失敗")
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()
    
    def _update_result_list(self):
        """更新結果列表 - 子類必須實現"""
        raise NotImplementedError("子類必須實現 _update_result_list 方法")
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 子類必須實現"""
        raise NotImplementedError("子類必須實現 _append_to_result_list 方法")
    
    def _show_loading_indicator(self):
        """顯示載入更多指示器"""
        if hasattr(self, 'load_more_label'):
            self.load_more_label.text = "載入中..."
            self.load_more_label.opacity = 1
    
    def _hide_loading_indicator(self):
        """隱藏載入更多指示器"""
        if hasattr(self, 'load_more_label'):
            if self.has_more_data:
                self.load_more_label.text = "滑動到底部載入更多"
                self.load_more_label.opacity = 0.7
            else:
                self.load_more_label.text = "已顯示全部資料"
                self.load_more_label.opacity = 0.5


class BaseScrollMixin:
    """滾動檢測和管理基類"""
    
    # 滾動相關屬性
    is_scrolling = BooleanProperty(False)
    _scroll_events_disabled = BooleanProperty(False)

    def on_leave(self):
        """離開屏幕時的清理，釋放背景定時器"""
        if hasattr(self, '_inertia_timer') and self._inertia_timer:
            Clock.unschedule(self._inertia_timer)
            self._inertia_timer = None
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"{self.__class__.__name__} 離開頁面，清理滾動狀態與定時器 (BaseScrollMixin)")
        if hasattr(super(), 'on_leave'):
            super().on_leave()
    
    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時記錄觸摸信息"""
        logger.debug(f"{self.__class__.__name__} on_scroll_start 被調用")
        
        # 檢查是否禁用滾動事件
        if self._scroll_events_disabled:
            logger.debug(f"{self.__class__.__name__} 滾動事件被禁用，忽略滾動開始")
            return
        
        # 避免定時器洩漏：若有舊的慣性定時器，立即取消它
        if hasattr(self, '_inertia_timer') and self._inertia_timer:
            Clock.unschedule(self._inertia_timer)
            self._inertia_timer = None
            
        # 記錄觸摸開始位置和時間
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start
        logger.debug(f"{self.__class__.__name__} 觸摸開始: 位置{touch.pos}, 時間{touch.time_start}")
    
    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        logger.debug(f"{self.__class__.__name__} on_scroll_move 被調用")
        
        # 檢查是否禁用滾動事件
        if self._scroll_events_disabled:
            return
        
        # 檢查是否有觸摸開始記錄
        if not hasattr(self, '_touch_start_pos') or not hasattr(self, '_touch_start_time'):
            return
        
        # 計算移動距離
        if self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            # 提高閾值並避免重複設定
            if distance > 30 and not self.is_scrolling:  # 提高到30像素
                Clock.schedule_once(lambda dt: self._set_scrolling_state(True), 0.1)
                logger.debug(f"{self.__class__.__name__} 檢測到滑動，移動距離: {distance:.1f}px")
    
    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多並重新啟用排序按鈕"""
        logger.debug(f"{self.__class__.__name__} on_scroll_end 被調用")
        
        # 檢查是否禁用滾動事件
        if self._scroll_events_disabled:
            logger.debug(f"{self.__class__.__name__} 滾動事件被禁用，忽略滾動結束")
            return
        
        # 計算總移動距離和時間
        if hasattr(self, '_touch_start_pos') and hasattr(self, '_touch_start_time'):
            if self._touch_start_pos:
                dx = abs(touch.pos[0] - self._touch_start_pos[0])
                dy = abs(touch.pos[1] - self._touch_start_pos[1])
                distance = (dx * dx + dy * dy) ** 0.5
                duration = touch.time_start - self._touch_start_time
                
                logger.debug(f"{self.__class__.__name__} 觸摸結束: 移動距離{distance:.1f}px, 持續時間{duration:.2f}s")
                
                # 如果有滑動，需要等待慣性滾動結束
                if distance > 30:
                    # 開始監控慣性滾動
                    self._start_inertia_monitoring(scroll_view)
                    logger.debug(f"{self.__class__.__name__} 開始監控慣性滾動")
        
        # 清除觸摸記錄
        self._touch_start_pos = None
        self._touch_start_time = None
        
        # 立即檢查是否需要載入更多（不等慣性滾動結束）
        self._check_load_more_immediate(scroll_view)
    
    def _start_inertia_monitoring(self, scroll_view):
        """開始監控慣性滾動"""
        # 避免定時器洩漏：若有舊的定時器，先取消它
        if hasattr(self, '_inertia_timer') and self._inertia_timer:
            Clock.unschedule(self._inertia_timer)
            self._inertia_timer = None
            
        # 記錄當前滾動位置
        self._last_scroll_y = scroll_view.scroll_y
        self._inertia_check_count = 0
        
        # 啟動並儲存定時器引用，以利於下一次滑動時取消
        self._inertia_timer = Clock.schedule_interval(self._check_inertia_scroll, 0.1)
    
    def _check_inertia_scroll(self, dt):
        """檢查慣性滾動是否結束"""
        if not hasattr(self.ids, 'scroll_view'):
            self._inertia_timer = None
            return False
        
        scroll_view = self.ids.scroll_view
        current_scroll_y = scroll_view.scroll_y
        
        # 計算滾動位置變化
        scroll_change = abs(current_scroll_y - self._last_scroll_y)
        self._inertia_check_count += 1
        
        logger.debug(f"{self.__class__.__name__} 慣性檢查 {self._inertia_check_count}: 位置變化 {scroll_change:.4f}")
        
        # 如果滾動位置變化很小，認為慣性滾動結束
        if scroll_change < 0.001:  # 位置變化小於0.001
            logger.debug(f"{self.__class__.__name__} 慣性滾動結束，啟用排序功能")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            
            # 檢查是否需要載入更多
            self._check_load_more(scroll_view)
            
            self._inertia_timer = None
            return False  # 停止定時檢查
        
        # 更新上次位置
        self._last_scroll_y = current_scroll_y
        
        # 最多檢查30次（3秒），避免無限檢查
        if self._inertia_check_count >= 30:
            logger.warning(f"{self.__class__.__name__} 慣性檢查超時，強制啟用排序功能")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            self._inertia_timer = None
            return False
        
        return True  # 繼續檢查
    
    def _set_scrolling_state(self, is_scrolling):
        """設定滾動狀態並更新按鈕"""
        self.is_scrolling = is_scrolling
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = is_scrolling
        logger.debug(f"{self.__class__.__name__} 設定滾動狀態: {is_scrolling}, 按鈕禁用: {is_scrolling}")
    
    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料（不等慣性滾動結束）"""
        if not hasattr(self, 'has_more_data') or not self.has_more_data or getattr(self, 'is_loading_more', False):
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_layout = getattr(self.ids, 'results_layout', None) or getattr(self.ids, 'duplicate_list', None) or getattr(self.ids, 'detail_list', None)
        if content_layout:
            content_height = content_layout.height
            viewport_height = scroll_view.height
            current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
            remaining_content = content_height - current_scroll_pos - viewport_height
            
            # 當剩餘內容少於1.5個螢幕高度時開始載入
            if remaining_content <= viewport_height * 1.5:
                logger.debug(f"{self.__class__.__name__} 立即檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
                if hasattr(self, '_load_next_page'):
                    self._load_next_page()
    
    def _check_load_more(self, scroll_view):
        """檢查是否需要載入更多資料（慣性滾動結束後的補充檢查）"""
        if not hasattr(self, 'has_more_data') or not self.has_more_data or getattr(self, 'is_loading_more', False):
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_layout = getattr(self.ids, 'results_layout', None) or getattr(self.ids, 'duplicate_list', None) or getattr(self.ids, 'detail_list', None)
        if content_layout:
            content_height = content_layout.height
            viewport_height = scroll_view.height
            current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
            remaining_content = content_height - current_scroll_pos - viewport_height
            
            # 當剩餘內容少於1.5個螢幕高度時開始載入
            if remaining_content <= viewport_height * 1.5:
                logger.debug(f"{self.__class__.__name__} 慣性滾動結束後檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
                if hasattr(self, '_load_next_page'):
                    self._load_next_page()
    
    def _disable_scroll_events(self):
        """暫時禁用滾動事件檢測"""
        self._scroll_events_disabled = True
        logger.debug(f"{self.__class__.__name__} 暫時禁用滾動事件")
    
    def _enable_scroll_events(self):
        """重新啟用滾動事件檢測並確保排序功能可用"""
        self._scroll_events_disabled = False
        # 確保排序功能恢復可用狀態
        Clock.schedule_once(lambda dt: self._ensure_sort_enabled(), 0.1)
        logger.debug(f"{self.__class__.__name__} 重新啟用滾動事件")
    
    def _ensure_sort_enabled(self):
        """確保排序功能處於可用狀態"""
        self.is_scrolling = False
        logger.debug(f"{self.__class__.__name__} 確保排序功能可用")

    def _restore_scroll_position_absolute(self, target_absolute_scroll):
        """恢復到指定的絕對滾動位置"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                content_layout = getattr(self.ids, 'results_layout', None) or getattr(self.ids, 'duplicate_list', None) or getattr(self.ids, 'detail_list', None)
                if content_layout:
                    content_height = content_layout.height
                    viewport_height = scroll_view.height
                    if content_height > viewport_height:
                        max_scroll_distance = content_height - viewport_height
                        new_scroll_y = 1 - (target_absolute_scroll / max_scroll_distance)
                        new_scroll_y = max(0, min(1, new_scroll_y))
                        scroll_view.scroll_y = new_scroll_y
                    else:
                        scroll_view.scroll_y = 1
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 恢復滾動位置錯誤: {str(e)}")

    def _reset_scroll_to_top(self):
        """重置滾動位置到頂部"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                # 先停止任何正在進行的滾動
                self._stop_scrolling()
                # 使用多次延遲確保UI完全更新後執行
                Clock.schedule_once(lambda dt: self._force_scroll_to_top(), 0.2)
                Clock.schedule_once(lambda dt: self._force_scroll_to_top(), 0.4)
                Clock.schedule_once(lambda dt: self._force_scroll_to_top(), 0.6)
                logger.debug(f"{self.__class__.__name__} 滾動位置已重置到頂部")
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 重置滾動位置錯誤: {str(e)}")

    def _stop_scrolling(self):
        """停止當前的滾動動作"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                # 取消任何正在進行的動畫
                Animation.cancel_all(scroll_view)
                # 立即設定位置
                scroll_view.scroll_y = 1
                logger.debug(f"{self.__class__.__name__} 停止滾動動作並立即重置")
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 停止滾動錯誤: {str(e)}")

    def _force_scroll_to_top(self):
        """強制滾動到頂部"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                # 停止任何動畫
                Animation.cancel_all(scroll_view)
                
                # 使用Animation強制滾動到頂部
                anim = Animation(scroll_y=1, duration=0.1)
                anim.start(scroll_view)
                
                # 同時直接設定位置
                scroll_view.scroll_y = 1
                
                logger.debug(f"{self.__class__.__name__} 強制滾動位置: {scroll_view.scroll_y}")
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 強制滾動錯誤: {str(e)}")


class BaseSortMixin:
    """排序管理基類"""
    
    sort_order = StringProperty('DESC')
    enable_sort = BooleanProperty(True)  # 控制是否啟用排序（重複X碼查詢頁面設為False）
    
    def toggle_sort_order(self):
        """切換排序方式並重新查詢"""
        logger.debug(f"{self.__class__.__name__} 排序按鈕被點擊，滾動狀態: {getattr(self, 'is_scrolling', False)}")
        
        # 檢查是否啟用排序功能
        if not self.enable_sort:
            logger.debug(f"{self.__class__.__name__} 排序功能被禁用")
            return
        
        # 檢查是否在滾動中
        if getattr(self, 'is_scrolling', False):
            logger.debug(f"{self.__class__.__name__} 滾動中，忽略排序請求")
            return
        
        logger.debug(f"{self.__class__.__name__} 開始執行排序")
        loading_popup = LoadingPopup(title='重新排序中')
        loading_popup.open()
        
        Clock.schedule_once(lambda dt: self._perform_sort(loading_popup), 0.1)
    
    def _perform_sort(self, loading_popup):
        """實際執行排序的方法（分頁版本）"""
        try:
            # 切換排序方式
            self.sort_order = 'ASC' if self.sort_order == 'DESC' else 'DESC'
            
            # 更新按鈕文字
            if hasattr(self.ids, 'sort_btn'):
                self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
            
            # 重新排序完整資料
            reverse_order = (self.sort_order == 'DESC')
            if hasattr(self, 'all_results') and self.all_results:
                # 根據不同的資料類型進行排序
                if '日期物件' in self.all_results[0]:
                    # 有日期物件的排序
                    self.all_results.sort(key=lambda x: x['日期物件'], reverse=reverse_order)
                elif '開獎日期' in self.all_results[0]:
                    # 有開獎日期的排序
                    from datetime import datetime
                    self.all_results.sort(key=lambda x: datetime.strptime(x['開獎日期'], '%Y/%m/%d'), reverse=reverse_order)
                else:
                    # 其他類型的排序（如重複號碼按次數排序）
                    if 'count' in self.all_results[0]:
                        self.all_results.sort(key=lambda x: x['count'], reverse=True)  # 重複次數總是降序
            
            logger.debug(f"{self.__class__.__name__} 排序: sort_order={self.sort_order}, reverse={reverse_order}")
            
            # 重新初始化分頁
            if hasattr(self, '_initialize_pagination'):
                self._initialize_pagination()
                self._load_first_page()
            
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 排序錯誤: {str(e)}")
        finally:
            # 關閉載入彈窗
            loading_popup.dismiss()
            # 在所有操作完成後，使用最簡單的方法重置
            Clock.schedule_once(lambda dt: self._simple_reset_scroll(), 0.5)
    
    def _simple_reset_scroll(self):
        """簡單有效的滾動重置方法"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                
                # 停止所有動畫
                Animation.cancel_all(scroll_view)
                
                # 暫時禁用滾動事件檢測，避免重置時觸發滾動事件
                if hasattr(self, '_disable_scroll_events'):
                    self._disable_scroll_events()
                
                # 使用Animation確保平滑重置
                anim = Animation(scroll_y=1.0, duration=0.3)
                if hasattr(self, '_enable_scroll_events'):
                    anim.bind(on_complete=lambda *args: self._enable_scroll_events())
                anim.start(scroll_view)
                
                logger.debug(f"{self.__class__.__name__} 使用動畫重置到頂部")
        except Exception as e:
            logger.exception(f"{self.__class__.__name__} 簡單重置錯誤: {str(e)}")


class BaseErrorHandlingMixin:
    """錯誤處理基類"""
    
    def handle_database_error(self, error):
        """統一的資料庫錯誤處理"""
        error_msg = f"資料庫錯誤: {str(error)}"
        logger.error(error_msg)
        self.log_error(error, "database")
        self.show_error_popup("資料庫錯誤", "資料庫操作失敗，請稍後再試")
    
    def handle_ui_error(self, error):
        """統一的UI錯誤處理"""
        error_msg = f"UI錯誤: {str(error)}"
        logger.error(error_msg)
        self.log_error(error, "ui")
        self.show_error_popup("介面錯誤", "介面操作失敗，請稍後再試")
    
    def show_error_popup(self, title, message):
        """統一的錯誤彈窗"""
        show_popup(title, message)
    
    def log_error(self, error, context):
        """記錄錯誤日誌"""
        error_info = f"[{context}] {self.__class__.__name__}: {str(error)}"
        logger.exception(error_info)


class BaseDatabaseMixin:
    """資料庫抽象基類"""
    
    @property
    def table_name(self):
        """子類必須實現：返回對應的資料庫表名"""
        raise NotImplementedError("子類必須實現 table_name 屬性")
    
    @property
    def number_columns(self):
        """子類必須實現：返回號碼欄位列表"""
        raise NotImplementedError("子類必須實現 number_columns 屬性")
    
    @property
    def special_column(self):
        """子類可選實現：返回特別號欄位名（如果有）"""
        return None
    
    def build_query(self, selected_numbers):
        """基於子類提供的表名和欄位構建查詢"""
        try:
            # 構建基本查詢
            query = f"SELECT * FROM {self.table_name} WHERE "
            conditions = []
            
            # 為每個選中的號碼添加條件
            for num in selected_numbers:
                # 檢查一般號碼欄位
                num_conditions = [f"{col} = ?" for col in self.number_columns]
                
                # 如果有特別號欄位，也加入檢查
                if self.special_column:
                    num_conditions.append(f"{self.special_column} = ?")
                
                # 組合條件（任一欄位匹配即可）
                conditions.append(f"({' OR '.join(num_conditions)})")
            
            # 所有選中號碼都必須匹配
            query += " AND ".join(conditions)
            query += f" ORDER BY date {getattr(self, 'sort_order', 'DESC')}"
            
            return query, list(selected_numbers) * len(self.number_columns + ([self.special_column] if self.special_column else []))
            
        except Exception as e:
            self.handle_database_error(e) if hasattr(self, 'handle_database_error') else logger.exception(f"查詢構建錯誤: {str(e)}")
            return None, []
    
    def get_prize_info(self, matched_nums, special_matched):
        """獲取獎別信息 - 子類應該覆寫此方法"""
        return '未中獎', ''


class BaseAdvancedResultScreen(Screen, BasePaginationMixin, BaseScrollMixin, 
                              BaseSortMixin, BaseErrorHandlingMixin, BaseDatabaseMixin):
    """統合所有功能的基類"""
    
    def on_touch_down(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.manager and self.manager.current != self.name:
            return False
        return super().on_touch_up(touch)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化資料庫路徑
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto_history.db')
    
    def on_pre_enter(self):
        """進入屏幕前的初始化"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        
        # 重置排序為預設降序（除非子類有特殊設定）
        if not hasattr(self, '_sort_initialized'):
            self.sort_order = 'DESC'
            self._sort_initialized = True
        
        logger.debug(f"{self.__class__.__name__} 進入頁面，初始化滾動狀態: {self.is_scrolling}, 排序: {self.sort_order}")
        
        # 重置滾動位置到頂部
        self._reset_scroll_to_top()
    



class AdBannerArea(BoxLayout):
    """
    橫幅廣告/手機引流區塊
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(50)
        
        from kivy.utils import platform
        if platform in ('android', 'ios'):
            # 行動端：預留高度 50dp 深色背景，顯示 AdMob 模擬廣告
            with self.canvas.before:
                Color(*get_color_from_hex('#212121'))
                self.rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_rect, size=self._update_rect)
            
            self.add_widget(Label(
                text="[ Google AdMob 測試廣告 (橫幅) ]",
                font_name="ChineseFont",
                font_size=dp(12),
                color=get_color_from_hex('#FFC107'),
                halign='center',
                valign='middle'
            ))
        else:
            # Windows 桌面端：顯示引流橫幅按鈕
            with self.canvas.before:
                Color(*get_color_from_hex('#1565C0'))  # 精緻藍色
                self.rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_rect, size=self._update_rect)
            
            btn = Button(
                text="📱 用手機版更方便！點擊下載手機版，隨時隨地對獎 ➔",
                font_name="ChineseFont",
                font_size=dp(13),
                color=get_color_from_hex('#FFFFFF'),
                background_color=(0, 0, 0, 0),  # 透明以顯示背景色
                bold=True
            )
            btn.bind(on_release=self.show_redirect_popup)
            self.add_widget(btn)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def show_redirect_popup(self, instance):
        """顯示下載手機版的彈窗"""
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        
        msg_label = Label(
            text="📱 好運自己選 - 行動版下載\n\n請掃描下方二維碼，或點擊下載按鈕下載 Android/iOS App！\n提供最即時的開獎更新與隨時對獎服務！",
            font_name='ChineseFont',
            font_size=dp(14),
            halign='center',
            valign='middle',
            size_hint_y=0.4
        )
        msg_label.bind(size=lambda inst, sz: setattr(inst, 'text_size', sz))
        content.add_widget(msg_label)
        
        # 模擬二維碼區域
        qr_box = BoxLayout(orientation='vertical', size_hint_y=0.4)
        qr_label = Label(
            text="[ 📥 請掃描此處 QR Code 下載 ]\n(預設跳轉 Google Play 商店)",
            font_name='ChineseFont',
            font_size=dp(14),
            color=get_color_from_hex('#FFC107'),
            halign='center'
        )
        qr_box.add_widget(qr_label)
        content.add_widget(qr_box)
        
        # 按鈕
        btn_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.2)
        btn_close = Button(
            text="稍後",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#757575')
        )
        btn_download = Button(
            text="前往商店下載",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#4CAF50')
        )
        btn_box.add_widget(btn_close)
        btn_box.add_widget(btn_download)
        content.add_widget(btn_box)
        
        popup = Popup(
            title="下載手機版 App",
            title_font="ChineseFont",
            content=content,
            size_hint=(0.85, 0.5)
        )
        
        btn_close.bind(on_release=popup.dismiss)
        btn_download.bind(on_release=lambda x: self.open_download(popup))
        popup.open()

    def open_download(self, popup):
        popup.dismiss()
        import webbrowser
        webbrowser.open(get_store_url())


class MobileInterstitialPopup(Popup):
    """
    Windows 桌面端專屬的「全螢幕手機推廣彈窗」，模擬行動端插頁廣告。
    """
    def __init__(self, on_close=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "✨ 精選推薦 ✨"
        self.title_font = "ChineseFont"
        self.title_size = dp(16)
        self.size_hint = (0.9, 0.8)  # 接近全螢幕
        self.auto_dismiss = False
        self.on_close_callback = on_close
        
        # 畫背景
        with self.canvas.before:
            Color(*get_color_from_hex('#1A237E')) # 高質感深藍色背景
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # 標題
        main_title = Label(
            text="📱 下載手機 APP，體驗完整選號對獎功能！",
            font_name="ChineseFont",
            font_size=dp(16),
            color=get_color_from_hex('#FFC107'),
            bold=True,
            size_hint_y=0.15
        )
        layout.add_widget(main_title)
        
        # 特色介紹
        features_text = (
            "1. 【自動連線更新】：自動下載最新歷史開獎資料！\n"
            "2. 【隨身好運選】：搖一搖手機快速推薦幸運球號！\n"
            "3. 【即時對獎通知】：開獎第一時間，中獎主動提醒！\n"
            "4. 【雲端選號同步】：Windows 選號，手機直接隨身查！"
        )
        features_label = Label(
            text=features_text,
            font_name="ChineseFont",
            font_size=dp(13),
            color=get_color_from_hex('#E0E0E0'),
            halign="left",
            valign="middle",
            size_hint_y=0.4
        )
        features_label.bind(size=lambda inst, sz: setattr(inst, 'text_size', (sz[0], None)))
        layout.add_widget(features_label)
        
        # 模擬 QR Code 區
        qr_box = BoxLayout(orientation="vertical", size_hint_y=0.3)
        qr_label = Label(
            text="[ 📥 掃描此處 QR Code 馬上裝機 ]\n(支援 Android 5.0+ / iOS 12.0+)",
            font_name="ChineseFont",
            font_size=dp(13),
            color=get_color_from_hex('#FFEB3B'),
            halign="center"
        )
        qr_box.add_widget(qr_label)
        layout.add_widget(qr_box)
        
        # 按鈕區
        btn_box = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint_y=0.15)
        btn_close = Button(
            text="關閉廣告",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#757575')
        )
        btn_go = Button(
            text="前往 Google Play 下載",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#2196F3'),
            bold=True
        )
        btn_box.add_widget(btn_close)
        btn_box.add_widget(btn_go)
        layout.add_widget(btn_box)
        
        btn_close.bind(on_release=self.close_and_resume)
        btn_go.bind(on_release=self.go_to_store)
        
        self.content = layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def close_and_resume(self, instance):
        self.dismiss()
        if self.on_close_callback:
            self.on_close_callback()

    def go_to_store(self, instance):
        self.dismiss()
        import webbrowser
        webbrowser.open(get_store_url())
        if self.on_close_callback:
            self.on_close_callback()


class AdManager:
    """
    統一管理橫幅與插頁廣告載入、顯示與計數邏輯的管理器。
    """
    def __init__(self):
        self.query_count = 0
        self.trigger_threshold = 2  # 每 2 次返回觸發 1 次廣告

    def show_interstitial(self, on_close_callback=None):
        """
        嘗試顯示插頁廣告。
        如果觸發了廣告，會在廣告關閉後呼叫 on_close_callback。
        如果未觸發廣告，會直接呼叫 on_close_callback。
        """
        self.query_count += 1
        logger.info(f"AdManager: Interstitial query count = {self.query_count}")
        
        if self.query_count % self.trigger_threshold == 0:
            logger.info("AdManager: Interstitial threshold reached. Triggering ad...")
            from kivy.utils import platform
            if platform in ('android', 'ios'):
                # 行動端：模擬 AdMob 插頁廣告（測試期直接觸發回呼，並在 log 記錄）
                logger.info("[AdMob Mobile] Mock Interstitial Ad triggered and closed.")
                if on_close_callback:
                    on_close_callback()
                return True
            else:
                # Windows 桌面端：彈出全螢幕推廣視窗
                popup = MobileInterstitialPopup(on_close=on_close_callback)
                popup.open()
                return True
        
        # 未達到觸發次數，直接執行返回邏輯
        if on_close_callback:
            on_close_callback()
        return False


# ==========================================
# 商店下載與更新網址設定（將來上架後請替換為您 App 的真實連結）
# ==========================================
ANDROID_STORE_URL = "https://play.google.com/store"
IOS_STORE_URL = "https://apps.apple.com"
DEFAULT_STORE_URL = "https://play.google.com/store"

def get_store_url():
    """
    根據當前運行平台，返回對應的應用程式商店網址。
    """
    from kivy.utils import platform
    if platform == 'android':
        return ANDROID_STORE_URL
    elif platform == 'ios':
        return IOS_STORE_URL
    else:
        return DEFAULT_STORE_URL