from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.properties import (
    NumericProperty, 
    StringProperty,
    ObjectProperty,
    DictProperty,
    ListProperty,
    BooleanProperty
)
from kivy.animation import Animation
from kivy.clock import Clock
import random
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle, Ellipse
import csv
import os
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
import sqlite3
import traceback
from collections import Counter
from kivy.uix.widget import Widget
from datetime import datetime
from modules.common import LoadingPopup, BallButton, ResultBall, show_popup, DatabaseManager, BaseLotteryQueryScreen, BaseLotterySavedScreen, BaseAdvancedResultScreen, ClickableBoxLayout
import logging
logger = logging.getLogger(__name__)




class Lotto539QueryScreen(BaseLotteryQueryScreen):
    """今彩539選號查詢界面"""
    selected_numbers = ListProperty([])  # 選中號碼
    
    # 實作抽象屬性
    @property
    def lottery_type(self):
        return '539'
    
    @property
    def table_name(self):
        return 'lotto_539'
    
    @property
    def max_numbers(self):
        return 5
    
    def get_selected_numbers(self):
        return list(self.selected_numbers)
    
    def validate_selection(self):
        """覆寫驗證邏輯 - 查詢時只需要至少1個號碼"""
        if not self.selected_numbers:
            return False, "請至少選擇1個號碼"
        return True, ""
    
    def validate_for_save(self):
        """儲存時的驗證邏輯"""
        if len(self.selected_numbers) != 5:
            return False, "請選擇5個號碼才能儲存"
        return True, ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.init_ui, 0.1)
    
    def init_ui(self, dt):
        """初始化選號界面"""
        # 號碼 (1-39)
        numbers_grid = self.ids.numbers_grid
        numbers_grid.clear_widgets()  # 清除可能存在的舊組件
        
        # 號碼 (1-39)，一列7球共6列
        for i in range(1, 40):  # 1到39
            btn = BallButton(text=str(i), area=1, lotto_type='lotto539')
            btn.bind(selected=self.on_ball_selected)
            numbers_grid.add_widget(btn)
    
    def on_ball_selected(self, instance, value):
        number = int(instance.text)
        if value:
            if len(self.selected_numbers) < 5:
                self.selected_numbers.append(number)
            else:
                instance.selected = False
                self.show_popup('提示', '最多只能選擇5個號碼')
        else:
            if number in self.selected_numbers:
                self.selected_numbers.remove(number)

    def clear_selection(self):
        """清除所有選取"""
        # 清除選取
        for btn in self.ids.numbers_grid.children:
            if isinstance(btn, BallButton):
                btn.selected = False
        self.selected_numbers.clear()
    
    def update_number_grid(self):
        """更新號碼網格顯示狀態 - 用於提取自選號後更新界面"""
        grid = self.ids.numbers_grid
        for child in grid.children:
            if isinstance(child, BallButton):
                number = int(child.text)
                # 暫時解除綁定，避免觸發 on_ball_selected
                child.unbind(selected=self.on_ball_selected)
                if number in self.selected_numbers:
                    child.selected = True
                else:
                    child.selected = False
                # 重新綁定
                child.bind(selected=self.on_ball_selected)
    
    # save_custom_numbers 現在由基礎類別提供
    
    # show_custom_numbers 現在由基礎類別的 show_saved_numbers 提供
    
    def check_duplicates(self):
        """查詢重複五碼"""
        self.manager.current = 'lotto539_duplicate'
    
    def query_winning_details(self):
        """查詢自選號中獎詳情"""
        if len(self.selected_numbers) != 5:
            self.show_popup('提示', '至少要選5個球號，或請先提取自選號')
            return
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='查詢中獎詳情中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_winning_details_query(), 0.1)

    def _perform_winning_details_query(self):
        """實際執行中獎詳情查詢的方法"""
        try:
            query_params = {
                'numbers': list(self.selected_numbers)
            }
            
            winning_details_screen = self.manager.get_screen('lotto539_winning_details')
            winning_details_screen.query_params = query_params
            winning_details_screen.sort_order = 'DESC'
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
            # 切換到中獎詳情屏幕
            self.manager.current = 'lotto539_winning_details'
        except Exception as e:
            error_msg = f"中獎詳情查詢失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            self.show_popup("錯誤", error_msg)
            traceback.print_exc()

    # query_history 現在由基礎類別提供
    
    def prepare_query_params(self):
        """準備查詢參數"""
        return {'numbers': sorted(self.selected_numbers)}
    
    def get_result_screen_name(self):
        """取得結果頁面名稱"""
        return 'lotto539_result'
    
    def show_popup(self, title, message):
        """顯示消息彈窗"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 添加標題
        title_label = Label(
            text=title,
            font_name='ChineseFont',
            font_size=dp(16),
            bold=True,
            color=(1, 0, 0, 1)
        )
        content.add_widget(title_label)
        
        # 添加消息內容
        message_label = Label(
            text=message,
            font_name='ChineseFont',
            font_size=dp(14)
        )
        content.add_widget(message_label)
        
        # 添加確定按鈕
        btn = Button(
            text="確定",
            size_hint_y=None,
            height=40,
            font_name='ChineseFont'
        )
        
        # 創建彈窗
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.7, 0.3),
            separator_height=0
        )
        
        # 綁定按鈕事件
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()


class Lotto539ResultScreen(BaseAdvancedResultScreen):
    """今彩539查詢結果界面"""
    query_params = DictProperty({})
    results = ListProperty([])
    stats = DictProperty({})
    user_numbers = DictProperty({})  # 存儲用戶選擇的號碼
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'lotto_539'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5']
    
    @property
    def special_column(self):
        return None  # 今彩539沒有特別號

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保今彩539查詢結果頁面預設為降序排列
        self.sort_order = 'DESC'

    def get_prize_info(self, matched_nums, special_matched):
        """今彩539特有的獎別計算邏輯（單區1-39號碼，八個獎別）"""
        if matched_nums == 5:
            return '頭獎', '頭'
        if matched_nums == 4:
            return '貳獎', '貳'
        if matched_nums == 3:
            return '參獎', '參'
        if matched_nums == 2:
            return '肆獎', '肆'
        return '未中獎', ''
    
    def _update_result_list(self):
        """更新結果列表（分頁版本）- 實現基類抽象方法"""
        try:
            # 清除結果列表
            self.ids.results_layout.clear_widgets()
            
            # 如果沒有結果，顯示提示
            if not self.displayed_results:
                no_data_label = Label(
                    text="查無符合資料",
                    font_name='ChineseFont',
                    font_size=dp(24),
                    color=(1, 0, 0, 1),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(100)
                )
                self.ids.results_layout.add_widget(no_data_label)
                return

            # 顯示當前已載入的所有資料
            for record in self.displayed_results:
                item_widget = self._create_result_item(record)
                self.ids.results_layout.add_widget(item_widget)
            
            # 添加載入更多指示器
            self._add_load_more_indicator()
            
        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539結果列表更新錯誤: {str(e)}")
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            # 保存當前滾動的絕對位置
            scroll_view = self.ids.scroll_view
            current_content_height = self.ids.results_layout.height
            current_viewport_height = scroll_view.height
            current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 添加新記錄
            for record in new_records:
                item_widget = self._create_result_item(record)
                self.ids.results_layout.add_widget(item_widget)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置（延遲執行確保UI更新完成）
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            
        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539追加結果錯誤: {str(e)}")
    
    def _create_result_item(self, record):
        """創建結果項目的UI組件 - 和大樂透保持一致"""
        from kivy.factory import Factory
        
        # 使用和大樂透相同的 ResultRow 組件
        result_row = Factory.ResultRow()
        
        # 設定今彩539特有的資料
        result_row.period = record['期別']
        result_row.date = record['開獎日期']
        result_row.numbers = record['獎號']
        result_row.special_number = None  # 今彩539沒有特別號
        result_row.award = record['獎別']
        result_row.lottery_type = 'lotto539'  # 設定彩券類型
        
        return result_row
   
    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"今彩539進入頁面，初始化滾動狀態: {self.is_scrolling}, 滾動事件啟用: {not self._scroll_events_disabled}")
        
        if self.query_params:
            self.user_numbers = {
                'numbers': self.query_params['numbers']
            }
            # 先檢查資料庫
            self.check_database()
            # 執行完整查詢並初始化分頁
            self._perform_full_query_with_pagination()
            # 重置滾動位置到頂部（新查詢）
            self._reset_scroll_to_top()
    
    def perform_query(self):
        """使用 SQLite 查詢歷史記錄"""
        app = App.get_running_app()
        selected_numbers = self.user_numbers['numbers']
    
        db_path = app.resource_path('data/lotto_history.db')
        if not os.path.exists(db_path):
            self.show_popup("錯誤", "找不到資料庫文件")
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        
            # 動態生成查詢條件
            query = f'''
            SELECT 
                issue as 期別,
                date as 開獎日期,
                num1, num2, num3, num4, num5
            FROM lotto_539
            WHERE {self._build_condition(selected_numbers)}
            '''
        
            cursor = conn.execute(query)
            matched_records = []
            selected_set = set(selected_numbers)  # 使用集合加速比對
        
            for row in cursor:
                winning_numbers = [row[f'num{i}'] for i in range(1, 6)]
                matched_count = len(selected_set & set(winning_numbers))

                # 將文字日期轉換為日期物件
                try:
                    date_obj = datetime.strptime(row['開獎日期'], '%Y/%m/%d').date()
                except ValueError:
                    try:
                        date_obj = datetime.strptime(row['開獎日期'], '%Y-%m-%d').date()
                    except ValueError:
                        date_obj = datetime.min.date()
                        logger.warning(f"警告: 無法解析日期格式: {row['開獎日期']}")
            
                matched_records.append({
                    '期別': row['期別'],
                    '開獎日期': row['開獎日期'],
                    '日期物件': date_obj,
                    '獎號': winning_numbers,
                    '獎別': self._determine_award(matched_count, len(selected_numbers))
                })

            # 依日期物件排序
            reverse_order = (self.sort_order == 'DESC')
            matched_records.sort(key=lambda x: x['日期物件'], reverse=reverse_order)
            
            conn.close()
            return matched_records
        
        except Exception as e:
            logger.exception(f"SQL 查詢錯誤: {str(e)}")
            traceback.print_exc()
            return []

    def _build_condition(self, numbers):
        """構建查詢條件"""
        if not numbers:
            return "1=0"
        return " AND ".join(
            f"({num} IN (num1, num2, num3, num4, num5))" 
            for num in numbers
        )

    def _determine_award(self, matched_count, selected_count):
        """獎別判斷 - 根據需求文件的規則"""
        # 根據需求：頭獎:自選號有五個, 貳獎:自選號有四個, 參獎:自選號有三個, 肆獎:自選號有二個
        # 這裡的"自選號有X個"應該是指匹配到的自選號數量
        if matched_count == 5:
            return '頭'
        elif matched_count == 4:
            return '貳'
        elif matched_count == 3:
            return '參'
        elif matched_count == 2:
            return '肆'
        return ''

    def _perform_full_query_with_pagination(self):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 1. 執行完整查詢（用於統計）
            self.all_results = self.perform_query()
            self.results = self.all_results  # 保持向後相容
            
            # 2. 計算統計資料（基於完整資料）
            self.calculate_stats()
            
            # 3. 初始化分頁
            self._initialize_pagination()
            
            # 4. 更新UI（統計區塊）
            self.update_ui()
            
            # 5. 載入第一頁資料
            self._load_first_page()
            
            # 6. 確保排序按鈕在查詢完成後可用
            Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 1.0)
            
        except Exception as e:
            logger.exception(f"今彩539分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        # 修正：只有當總記錄數大於每頁顯示數量時才有更多資料
        self.has_more_data = total_records > self.page_size
        
        logger.debug(f"今彩539查詢結果分頁初始化: 總筆數={total_records}, 每頁={self.page_size}, has_more_data={self.has_more_data}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"今彩539查詢結果第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆，has_more_data={self.has_more_data}")
        else:
            self.has_more_data = False
            self._update_result_list()  # 顯示無資料

    def toggle_sort_order(self):
        """切換排序方式並重新查詢"""
        logger.debug(f"今彩539排序按鈕被點擊，滾動狀態: {self.is_scrolling}")
        
        if self.is_scrolling:
            logger.debug("今彩539滾動中，忽略排序請求")
            return
        
        logger.debug("今彩539開始執行排序")
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
            self.all_results.sort(key=lambda x: x['日期物件'], reverse=reverse_order)
            logger.debug(f"今彩539排序: sort_order={self.sort_order}, reverse={reverse_order}")
            self.results = self.all_results  # 保持向後相容
            
            # 重新初始化分頁
            self._initialize_pagination()
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"今彩539排序錯誤: {str(e)}")
            traceback.print_exc()
        finally:
            # 關閉載入彈窗
            loading_popup.dismiss()
            # 在所有操作完成後，使用最簡單的方法重置
            Clock.schedule_once(lambda dt: self._simple_reset_scroll(), 0.5)

    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {
            '頭': 0, '貳': 0, '參': 0, '肆': 0
        }
        
        # 遍歷所有結果記錄
        for record in self.results:
            award = record.get('獎別', '')
            if award and award in stats:
                stats[award] += 1

        # 更新統計數據
        self.stats = stats

    def update_ui(self):
        """更新界面顯示（統計區塊和用戶選號）"""
        try:
            # 清除舊組件
            self.ids.selected_nums_layout.clear_widgets()

            # 更新總筆數顯示（基於完整資料）
            self.ids.total_count_label.text = str(len(self.all_results))

            # 更新各獎別統計
            self.ids.prize_count_head.text = str(self.stats.get('頭', 0))
            self.ids.prize_count_second.text = str(self.stats.get('貳', 0))
            self.ids.prize_count_third.text = str(self.stats.get('參', 0))
            self.ids.prize_count_fourth.text = str(self.stats.get('肆', 0))

            # 添加自選號球
            for num in sorted(self.user_numbers['numbers']):
                ball = ResultBall(number=num, area=1, selected=True, lotto_type='lotto539')
                self.ids.selected_nums_layout.add_widget(ball)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539UI更新錯誤: {str(e)}")

    def _update_result_list(self):
        """更新結果列表（分頁版本）"""
        try:
            # 清除結果列表
            self.ids.results_layout.clear_widgets()
            
            # 如果沒有結果，顯示提示
            if not self.displayed_results:
                no_data_label = Label(
                    text="查無符合資料",
                    font_name='ChineseFont',
                    font_size=dp(24),
                    color=(1, 0, 0, 1),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(100)
                )
                self.ids.results_layout.add_widget(no_data_label)
                return

            # 顯示當前已載入的所有資料
            for record in self.displayed_results:
                item_widget = self._create_result_item(record)
                self.ids.results_layout.add_widget(item_widget)
            
            # 添加載入更多指示器
            self._add_load_more_indicator()

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539結果列表更新錯誤: {str(e)}")

    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        # 創建結果行容器
        result_row = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(70),
            spacing=dp(5)
        )

        # 期別和日期行
        info_row = BoxLayout(
            size_hint_y=None,
            height=dp(20)
        )
        
        period_label = Label(
            text=f"期別: {record['期別']}",
            font_name='ChineseFont',
            font_size='12sp',
            size_hint_x=None,
            width=dp(140),
            halign='left',
            valign='middle',
            text_size=(dp(140), None)
        )
        info_row.add_widget(period_label)
        
        date_label = Label(
            text=f"開獎日期: {record['開獎日期']}",
            font_name='ChineseFont',
            font_size='12sp',
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        date_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        info_row.add_widget(date_label)
        
        result_row.add_widget(info_row)

        # 獎號和獎別行
        numbers_row = BoxLayout(
            size_hint_y=None,
            height=dp(40)
        )
        
        # 獎號網格
        winning_nums_layout = GridLayout(
            cols=5,
            spacing=dp(5)
        )
        
        for num in sorted(record['獎號']):
            selected = num in self.user_numbers['numbers']
            ball = ResultBall(number=num, area=1, selected=selected, lotto_type='lotto539')
            winning_nums_layout.add_widget(ball)
        
        numbers_row.add_widget(winning_nums_layout)
        
        # 獎別標籤
        prize_label = Label(
            text=record['獎別'],
            font_name='ChineseFont',
            font_size=dp(18),
            color=(1, 0, 0, 1),
            size_hint_x=None,
            width=dp(40),
            halign='center',
            valign='middle'
        )
        numbers_row.add_widget(prize_label)
        
        result_row.add_widget(numbers_row)
        
        return result_row

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'results_layout'):
            logger.warning("今彩539查詢結果找不到results_layout，無法添加載入指示器")
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
            logger.debug(f"今彩539查詢結果添加載入指示器: {text} (has_more_data={self.has_more_data})")
        else:
            text = "已顯示全部資料"
            opacity = 0.5
            logger.debug(f"今彩539查詢結果添加載入指示器: {text} (has_more_data={self.has_more_data})")
        
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
        self.ids.results_layout.add_widget(load_more_box)
        
        # 儲存引用以便後續更新
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label

    def _load_next_page(self):
        """載入下一頁資料"""
        if self.is_loading_more or not self.has_more_data:
            return
        
        self.is_loading_more = True
        
        # 顯示載入提示
        self._show_loading_indicator()
        
        # 延遲載入，避免UI阻塞
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
                
                logger.debug(f"今彩539載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"今彩539載入下一頁錯誤: {str(e)}")
            show_popup("錯誤", "載入更多資料失敗")
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()

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

    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表"""
        try:
            # 保存當前滾動的絕對位置
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                current_content_height = self.ids.results_layout.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                
                logger.debug(f"今彩539載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
            else:
                current_absolute_scroll = 0
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 添加新記錄
            for record in new_records:
                item_widget = self._create_result_item(record)
                self.ids.results_layout.add_widget(item_widget)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置（延遲執行確保UI更新完成）
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            
        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539追加結果錯誤: {str(e)}")

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and self.load_more_indicator in self.ids.results_layout.children:
            self.ids.results_layout.remove_widget(self.load_more_indicator)

    def _restore_scroll_position_absolute(self, target_absolute_scroll):
        """根據絕對位置恢復滾動位置"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                new_content_height = self.ids.results_layout.height
                viewport_height = scroll_view.height
                
                # 計算新的相對滾動位置
                max_scroll = max(0, new_content_height - viewport_height)
                if max_scroll > 0:
                    # 保持相同的絕對位置，但稍微向上調整以保持視覺連續性
                    adjusted_absolute_scroll = max(0, target_absolute_scroll - 50)  # 向上調整50像素
                    new_scroll_y = 1 - (adjusted_absolute_scroll / max_scroll)
                    new_scroll_y = max(0, min(1, new_scroll_y))  # 確保在有效範圍內
                else:
                    new_scroll_y = 1  # 內容不夠長，保持在頂部
                
                scroll_view.scroll_y = new_scroll_y
                logger.debug(f"今彩539載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"今彩539恢復滾動位置錯誤: {str(e)}")

    def _set_scrolling_state(self, is_scrolling):
        """設定滾動狀態並更新按鈕"""
        self.is_scrolling = is_scrolling
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = is_scrolling
        logger.debug(f"今彩539結果頁面設定滾動狀態: {is_scrolling}, 按鈕禁用: {is_scrolling}")

    def _simple_reset_scroll(self):
        """簡單有效的滾動重置方法"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                
                # 停止所有動畫
                Animation.cancel_all(scroll_view)
                
                # 暫時禁用滾動事件檢測，避免重置時觸發滾動事件
                self._disable_scroll_events()
                
                # 使用Animation確保平滑重置
                anim = Animation(scroll_y=1.0, duration=0.3)
                anim.bind(on_complete=lambda *args: self._enable_scroll_events())
                anim.start(scroll_view)
                
                logger.debug("今彩539使用動畫重置到頂部")
        except Exception as e:
            logger.exception(f"今彩539簡單重置錯誤: {str(e)}")

    def _disable_scroll_events(self):
        """暫時禁用滾動事件檢測"""
        self._scroll_events_disabled = True
        logger.debug("今彩539暫時禁用滾動事件")

    def _enable_scroll_events(self):
        """重新啟用滾動事件檢測並確保排序按鈕可用"""
        self._scroll_events_disabled = False
        # 確保排序按鈕恢復可用狀態
        Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 0.1)
        logger.debug("今彩539重新啟用滾動事件")

    def _ensure_sort_button_enabled(self):
        """確保排序按鈕處於可用狀態"""
        self.is_scrolling = False
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = False
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
        logger.debug("今彩539確保排序按鈕可用")

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
                logger.debug("今彩539滾動位置已重置到頂部")
        except Exception as e:
            logger.exception(f"今彩539重置滾動位置錯誤: {str(e)}")

    def _stop_scrolling(self):
        """停止當前的滾動動作"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                # 取消任何正在進行的動畫
                Animation.cancel_all(scroll_view)
                # 停止滾動效果
                if hasattr(scroll_view, 'scroll_timeout'):
                    Clock.unschedule(scroll_view.scroll_timeout)
                # 立即設定位置
                scroll_view.scroll_y = 1
                logger.debug("今彩539停止滾動動作並立即重置")
        except Exception as e:
            logger.exception(f"今彩539停止滾動錯誤: {str(e)}")

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
                
                logger.debug(f"今彩539強制滾動位置: {scroll_view.scroll_y}")
        except Exception as e:
            logger.exception(f"今彩539強制滾動錯誤: {str(e)}")

    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時禁用排序按鈕"""
        Clock.unschedule(self._check_inertia_scroll)
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            logger.debug("今彩539滾動事件被禁用，忽略滾動開始")
            return
        
        # 記錄觸摸開始位置和時間
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start
        logger.debug(f"今彩539觸摸開始: 位置{touch.pos}, 時間{touch.time_start}")

    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            return
        
        # 檢查是否有觸摸開始記錄
        if not hasattr(self, '_touch_start_pos') or not hasattr(self, '_touch_start_time'):
            return
        
        # 計算移動距離
        if self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            # 只有移動距離超過閾值才認為是滑動
            if distance > 20:  # 20像素的移動閾值
                if not self.is_scrolling:
                    Clock.schedule_once(lambda dt: self._set_scrolling_state(True), 0.1)
                    logger.debug(f"今彩539檢測到滑動，移動距離: {distance:.1f}px")

    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多並重新啟用排序按鈕"""
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            logger.debug("今彩539滾動事件被禁用，忽略滾動結束")
            return
        
        # 計算總移動距離和時間
        if hasattr(self, '_touch_start_pos') and hasattr(self, '_touch_start_time'):
            if self._touch_start_pos:
                dx = abs(touch.pos[0] - self._touch_start_pos[0])
                dy = abs(touch.pos[1] - self._touch_start_pos[1])
                distance = (dx * dx + dy * dy) ** 0.5
                duration = touch.time_start - self._touch_start_time
                
                logger.debug(f"今彩539觸摸結束: 移動距離{distance:.1f}px, 持續時間{duration:.2f}s")
                
                # 如果有滑動，需要等待慣性滾動結束
                if distance > 20:
                    # 開始監控慣性滾動
                    self._start_inertia_monitoring(scroll_view)
                    logger.debug("今彩539開始監控慣性滾動")
        
        # 清除觸摸記錄
        self._touch_start_pos = None
        self._touch_start_time = None
        
        # 立即檢查是否需要載入更多（不等慣性滾動結束）
        self._check_load_more_immediate(scroll_view)

    def _start_inertia_monitoring(self, scroll_view):
        """開始監控慣性滾動"""
        Clock.unschedule(self._check_inertia_scroll)
        # 記錄當前滾動位置
        self._last_scroll_y = scroll_view.scroll_y
        self._inertia_check_count = 0
        
        # 每0.1秒檢查一次滾動位置
        Clock.schedule_interval(self._check_inertia_scroll, 0.1)

    def _check_inertia_scroll(self, dt):
        """檢查慣性滾動是否結束"""
        if not hasattr(self.ids, 'scroll_view'):
            return False
        
        scroll_view = self.ids.scroll_view
        current_scroll_y = scroll_view.scroll_y
        
        # 計算滾動位置變化
        scroll_change = abs(current_scroll_y - self._last_scroll_y)
        self._inertia_check_count += 1
        
        logger.debug(f"今彩539慣性檢查 {self._inertia_check_count}: 位置變化 {scroll_change:.4f}")
        
        # 如果滾動位置變化很小，認為慣性滾動結束
        if scroll_change < 0.001:  # 位置變化小於0.001
            logger.debug("今彩539慣性滾動結束，啟用排序按鈕")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            
            # 檢查是否需要載入更多
            self._check_load_more(scroll_view)
            
            return False  # 停止定時檢查
        
        # 更新上次位置
        self._last_scroll_y = current_scroll_y
        
        # 最多檢查30次（3秒），避免無限檢查
        if self._inertia_check_count >= 30:
            logger.warning("今彩539慣性檢查超時，強制啟用排序按鈕")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            return False
        
        return True  # 繼續檢查

    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料（不等慣性滾動結束）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.results_layout.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"今彩539立即檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()

    def _check_load_more(self, scroll_view):
        """檢查是否需要載入更多資料（慣性滾動結束後的補充檢查）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.results_layout.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"今彩539慣性滾動結束後檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()
   
    def back_to_query(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_back_to_query)

    def _real_back_to_query(self):
        """返回查詢界面"""
        self.manager.current = 'lotto539_query'

    def check_database(self):
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
    
        if not os.path.exists(db_path):
            logger.error("錯誤：資料庫文件不存在")
            return
    
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
        
            # 檢查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lotto_539'")
            if not cursor.fetchone():
                logger.error("錯誤：lotto_539表不存在")
                return
        
            # 檢查記錄數量
            cursor.execute("SELECT COUNT(*) FROM lotto_539")
            count = cursor.fetchone()[0]
            logger.debug(f"資料庫中包含 {count} 條今彩539記錄")
        
            conn.close()
        except Exception as e:
            logger.exception(f"資料庫檢查錯誤: {str(e)}")


class Lotto539SavedScreen(BaseLotterySavedScreen):
    """今彩539自選號管理界面"""
    
    @property
    def lottery_type(self):
        return '539'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    # load_saved_numbers 和 populate_saved_list 現在由基礎類別提供

    # 觸摸事件處理和刪除邏輯現在由基礎類別提供

    def use_saved_number(self, index):
        """實作基礎類別的抽象方法"""
        if 0 <= index < len(self.saved_numbers):
            saved = self.saved_numbers[index]
            
            query_screen = self.manager.get_screen('lotto539_query')
            
            # 直接設定 selected_numbers 屬性
            query_screen.selected_numbers = saved['numbers'].copy()
            
            # 更新號碼網格顯示
            query_screen.update_number_grid()
            
            self.manager.current = 'lotto539_query'
    
    # back_to_query 現在由基礎類別提供


class Lotto539WinningDetailsScreen(Screen):
    """今彩539自選號中獎詳情界面"""
    sort_order = StringProperty('DESC')
    
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
    user_numbers = DictProperty({})
    
    # 分頁相關屬性
    all_results = ListProperty([])  # 完整查詢結果（用於統計）
    displayed_results = ListProperty([])  # 當前顯示的結果
    current_page = NumericProperty(0)     # 當前頁數
    page_size = NumericProperty(30)       # 每頁顯示數量
    is_loading_more = BooleanProperty(False)  # 是否正在載入更多
    has_more_data = BooleanProperty(True)     # 是否還有更多資料
    is_scrolling = BooleanProperty(False)     # 是否正在滾動
    query_params = DictProperty({})
    results = ListProperty([])
    stats = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto_history.db')

    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"今彩539中獎詳情進入頁面，初始化滾動狀態: {self.is_scrolling}, 滾動事件啟用: {not self._scroll_events_disabled}")
        
        # 清空結果列表，避免重複顯示
        if hasattr(self.ids, 'results_layout'):
            self.ids.results_layout.clear_widgets()
            logger.debug("清空結果列表")
        
        # 延遲檢查排序按鈕是否存在
        Clock.schedule_once(lambda dt: self._check_sort_button(), 0.5)
        
        if self.query_params:
            self.user_numbers = {
                'numbers': self.query_params['numbers']
            }
            # 執行完整查詢並初始化分頁
            self._perform_full_query_with_pagination()
            # 重置滾動位置到頂部（新查詢）
            self._reset_scroll_to_top()
        else:
            # 保持舊版本相容性
            logger.debug("今彩539中獎詳情沒有query_params，使用舊版show_results")
            self.show_results()

    def _check_sort_button(self):
        """檢查排序按鈕是否存在"""
        if hasattr(self.ids, 'sort_btn'):
            logger.debug(f"今彩539中獎詳情找到排序按鈕: {self.ids.sort_btn}")
            logger.debug(f"排序按鈕當前狀態: disabled={self.ids.sort_btn.disabled}")
        else:
            logger.debug("今彩539中獎詳情沒有找到排序按鈕 sort_btn")
            logger.debug(f"可用的ids: {list(self.ids.keys()) if hasattr(self, 'ids') else 'No ids'}")

    def _perform_full_query_with_pagination(self):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 1. 執行完整查詢（用於統計）
            self.all_results = self.perform_winning_query()
            self.results = self.all_results  # 保持向後相容
            
            # 2. 計算統計資料（基於完整資料）
            self.calculate_stats()
            
            # 3. 初始化分頁
            self._initialize_pagination()
            
            # 4. 更新UI（統計區塊） - 延遲執行確保KV完全載入
            Clock.schedule_once(lambda dt: self.update_ui(), 0.1)
            
            # 5. 載入第一頁資料
            self._load_first_page()
            
            # 6. 確保排序按鈕在查詢完成後可用
            Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 1.0)
            
        except Exception as e:
            logger.exception(f"今彩539中獎詳情分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > 0
        
        logger.debug(f"今彩539中獎詳情分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"今彩539中獎詳情第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self._update_result_list()  # 顯示無資料

    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {'頭獎': 0, '貳獎': 0, '參獎': 0, '肆獎': 0}
        
        # 遍歷所有結果記錄，使用all_results確保統計完整資料
        for record in self.all_results:
            award = record.get('獎別全名', '')
            if award and award in stats:
                stats[award] += 1

        # 更新統計數據
        self.stats = stats

        # 打印調試信息
        logger.debug("今彩539中獎詳情獎別統計結果:")
        for award, count in stats.items():
            logger.debug(f"{award}: {count}")

    def update_ui(self):
        """更新界面顯示（統計區塊和用戶選號）"""
        try:
            # 只更新數據，不添加任何UI元素（KV檔案已定義）
            logger.debug("今彩539中獎詳情更新UI - 僅更新統計數據，不添加UI元素")
            
            # 更新總筆數顯示（基於完整資料）
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = str(len(self.all_results))
                logger.debug(f"更新總筆數: {len(self.all_results)}")

            # 更新各獎別統計
            prize_map = {
                '頭獎': 'prize_count_head',
                '貳獎': 'prize_count_second',
                '參獎': 'prize_count_third',
                '肆獎': 'prize_count_fourth',
            }
            
            for prize_full, prize_id in prize_map.items():
                if hasattr(self.ids, prize_id):
                    count = self.stats.get(prize_full, 0)
                    getattr(self.ids, prize_id).text = str(count)
                    logger.debug(f"更新{prize_full}: {count}")

            # 清空並重新添加自選號球（確保正確顯示）
            if hasattr(self.ids, 'selected_nums_layout'):
                self.ids.selected_nums_layout.clear_widgets()
                logger.debug("清空並重新添加自選號球")
                for num in sorted(self.user_numbers.get('numbers', [])):
                    ball = ResultBall(number=num, selected=True, lotto_type='lotto539')
                    self.ids.selected_nums_layout.add_widget(ball)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539中獎詳情UI更新錯誤: {str(e)}")

    def _update_result_list(self):
        """更新結果列表（分頁版本）"""
        try:
            # 清除結果列表
            if hasattr(self.ids, 'results_layout'):
                self.ids.results_layout.clear_widgets()
            
            # 如果沒有結果，顯示提示
            if not self.displayed_results:
                no_data_label = Label(
                    text="查無符合資料",
                    font_name='ChineseFont',
                    font_size=dp(24),
                    color=(1, 0, 0, 1),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(100)
                )
                if hasattr(self.ids, 'results_layout'):
                    self.ids.results_layout.add_widget(no_data_label)
                return

            # 顯示當前已載入的所有資料
            for record in self.displayed_results:
                item_widget = self._create_result_item(record)
                if hasattr(self.ids, 'results_layout'):
                    self.ids.results_layout.add_widget(item_widget)
            
            # 添加載入更多指示器
            self._add_load_more_indicator()

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539中獎詳情結果列表更新錯誤: {str(e)}")

    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        # 創建結果行容器
        result_row = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(70),
            spacing=dp(5)
        )

        # 期別和日期行
        info_row = BoxLayout(
            size_hint_y=None,
            height=dp(20)
        )
        
        period_label = Label(
            text=f"期別: {record['期別']}",
            font_name='ChineseFont',
            font_size='12sp',
            size_hint_x=None,
            width=dp(140),
            halign='left',
            valign='middle',
            text_size=(dp(140), None)
        )
        info_row.add_widget(period_label)
        
        date_label = Label(
            text=f"開獎日期: {record['開獎日期']}",
            font_name='ChineseFont',
            font_size='12sp',
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        date_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        info_row.add_widget(date_label)
        
        result_row.add_widget(info_row)

        # 獎號和獎別行
        numbers_row = BoxLayout(
            size_hint_y=None,
            height=dp(40)
        )
        
        # 獎號網格
        winning_nums_layout = GridLayout(
            cols=5,
            spacing=dp(5)
        )
        
        selected_numbers = self.user_numbers.get('numbers', [])
        
        for num in sorted(record['獎號']):
            ball = ResultBall(number=num, area=1, selected=(num in selected_numbers), lotto_type='lotto539')
            winning_nums_layout.add_widget(ball)
        
        numbers_row.add_widget(winning_nums_layout)
        
        # 獎別標籤
        prize_label = Label(
            text=record['獎別簡稱'],
            font_name='ChineseFont',
            font_size=dp(18),
            color=(1, 0, 0, 1),
            size_hint_x=None,
            width=dp(40),
            halign='center',
            valign='middle'
        )
        numbers_row.add_widget(prize_label)
        
        result_row.add_widget(numbers_row)
        
        return result_row

    def toggle_sort_order(self):
        """切換排序方式並重新查詢"""
        logger.debug(f"今彩539中獎詳情排序按鈕被點擊，滾動狀態: {self.is_scrolling}")
        
        if self.is_scrolling:
            logger.debug("今彩539中獎詳情滾動中，忽略排序請求")
            return
        
        logger.debug("今彩539中獎詳情開始執行排序")
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
            self.all_results.sort(key=lambda x: datetime.strptime(x['開獎日期'], '%Y/%m/%d'), reverse=reverse_order)
            logger.debug(f"今彩539中獎詳情排序: sort_order={self.sort_order}, reverse={reverse_order}")
            self.results = self.all_results  # 保持向後相容
            
            # 重新初始化分頁
            self._initialize_pagination()
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"今彩539中獎詳情排序錯誤: {str(e)}")
            traceback.print_exc()
        finally:
            # 關閉載入彈窗
            loading_popup.dismiss()
            # 在所有操作完成後，使用最簡單的方法重置
            Clock.schedule_once(lambda dt: self._simple_reset_scroll(), 0.5)

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if self.has_more_data and hasattr(self.ids, 'results_layout'):
            load_more_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(60),
                padding=(dp(10), dp(10))
            )
            
            load_more_label = Label(
                text="滑動到底部載入更多",
                font_name='ChineseFont',
                font_size=dp(14),
                color=get_color_from_hex('#888888'),
                halign='center',
                valign='middle'
            )
            load_more_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
            
            load_more_box.add_widget(load_more_label)
            self.ids.results_layout.add_widget(load_more_box)
            
            # 儲存引用以便後續更新
            self.load_more_indicator = load_more_box
            self.load_more_label = load_more_label

    def _load_next_page(self):
        """載入下一頁資料"""
        if self.is_loading_more or not self.has_more_data:
            return
        
        self.is_loading_more = True
        
        # 顯示載入提示
        self._show_loading_indicator()
        
        # 延遲載入，避免UI阻塞
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
                
                logger.debug(f"今彩539中獎詳情載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"今彩539中獎詳情載入下一頁錯誤: {str(e)}")
            show_popup("錯誤", "載入更多資料失敗")
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()

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

    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表"""
        try:
            # 保存當前滾動的絕對位置
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                current_content_height = self.ids.results_layout.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                
                logger.debug(f"今彩539中獎詳情載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
            else:
                current_absolute_scroll = 0
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 添加新記錄
            for record in new_records:
                item_widget = self._create_result_item(record)
                if hasattr(self.ids, 'results_layout'):
                    self.ids.results_layout.add_widget(item_widget)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置（延遲執行確保UI更新完成）
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            
        except Exception as e:
            traceback.print_exc()
            logger.exception(f"今彩539中獎詳情追加結果錯誤: {str(e)}")

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'results_layout') and self.load_more_indicator in self.ids.results_layout.children:
            self.ids.results_layout.remove_widget(self.load_more_indicator)

    def _restore_scroll_position_absolute(self, target_absolute_scroll):
        """根據絕對位置恢復滾動位置"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                new_content_height = self.ids.results_layout.height
                viewport_height = scroll_view.height
                
                # 計算新的相對滾動位置
                max_scroll = max(0, new_content_height - viewport_height)
                if max_scroll > 0:
                    # 保持相同的絕對位置，但稍微向上調整以保持視覺連續性
                    adjusted_absolute_scroll = max(0, target_absolute_scroll - 50)  # 向上調整50像素
                    new_scroll_y = 1 - (adjusted_absolute_scroll / max_scroll)
                    new_scroll_y = max(0, min(1, new_scroll_y))  # 確保在有效範圍內
                else:
                    new_scroll_y = 1  # 內容不夠長，保持在頂部
                
                scroll_view.scroll_y = new_scroll_y
                logger.debug(f"今彩539中獎詳情載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"今彩539中獎詳情恢復滾動位置錯誤: {str(e)}")

    def _set_scrolling_state(self, is_scrolling):
        """設定滾動狀態並更新按鈕"""
        self.is_scrolling = is_scrolling
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = is_scrolling
            logger.debug(f"今彩539中獎詳情排序按鈕禁用狀態: {self.ids.sort_btn.disabled}")
        else:
            logger.debug("今彩539中獎詳情找不到sort_btn")
        logger.debug(f"今彩539中獎詳情設定滾動狀態: {is_scrolling}, 按鈕禁用: {is_scrolling}")

    def _simple_reset_scroll(self):
        """簡單有效的滾動重置方法"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                
                # 停止所有動畫
                Animation.cancel_all(scroll_view)
                
                # 暫時禁用滾動事件檢測，避免重置時觸發滾動事件
                self._disable_scroll_events()
                
                # 使用Animation確保平滑重置
                anim = Animation(scroll_y=1.0, duration=0.3)
                anim.bind(on_complete=lambda *args: self._enable_scroll_events())
                anim.start(scroll_view)
                
                logger.debug("今彩539中獎詳情使用動畫重置到頂部")
        except Exception as e:
            logger.exception(f"今彩539中獎詳情簡單重置錯誤: {str(e)}")

    def _disable_scroll_events(self):
        """暫時禁用滾動事件檢測"""
        self._scroll_events_disabled = True
        logger.debug("今彩539中獎詳情暫時禁用滾動事件")

    def _enable_scroll_events(self):
        """重新啟用滾動事件檢測並確保排序按鈕可用"""
        self._scroll_events_disabled = False
        # 確保排序按鈕恢復可用狀態
        Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 0.1)
        logger.debug("今彩539中獎詳情重新啟用滾動事件")

    def _ensure_sort_button_enabled(self):
        """確保排序按鈕處於可用狀態"""
        self.is_scrolling = False
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = False
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
            logger.debug(f"今彩539中獎詳情排序按鈕已啟用: {not self.ids.sort_btn.disabled}")
        else:
            logger.debug("今彩539中獎詳情找不到sort_btn，無法啟用")
        logger.debug("今彩539中獎詳情確保排序按鈕可用")

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
                logger.debug("今彩539中獎詳情滾動位置已重置到頂部")
        except Exception as e:
            logger.exception(f"今彩539中獎詳情重置滾動位置錯誤: {str(e)}")

    def _stop_scrolling(self):
        """停止當前的滾動動作"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                # 取消任何正在進行的動畫
                Animation.cancel_all(scroll_view)
                # 停止滾動效果
                if hasattr(scroll_view, 'scroll_timeout'):
                    Clock.unschedule(scroll_view.scroll_timeout)
                # 立即設定位置
                scroll_view.scroll_y = 1
                logger.debug("今彩539中獎詳情停止滾動動作並立即重置")
        except Exception as e:
            logger.exception(f"今彩539中獎詳情停止滾動錯誤: {str(e)}")

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
                
                logger.debug(f"今彩539中獎詳情強制滾動位置: {scroll_view.scroll_y}")
        except Exception as e:
            logger.exception(f"今彩539中獎詳情強制滾動錯誤: {str(e)}")

    def show_results(self):
        """保留舊版本的show_results方法以保持向後相容"""
        # 如果有新的query_params，使用分頁版本
        if self.query_params:
            logger.debug("今彩539中獎詳情使用分頁版本，跳過舊版show_results")
            return
        
        # 舊版本邏輯（僅在沒有query_params時執行）
        logger.debug("今彩539中獎詳情執行舊版show_results")
        self.ids.results_layout.clear_widgets()
        self.ids.selected_nums_layout.clear_widgets()

        selected_numbers = self.user_numbers.get('numbers', [])
        for num in sorted(selected_numbers):
            ball = ResultBall(number=num, selected=True, area=1)
            self.ids.selected_nums_layout.add_widget(ball)

        matched_records = self.perform_winning_query()

        # 重置獎別統計
        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third',
            '肆獎': 'prize_count_fourth',
        }
        
        for prize_id in prize_map.values():
            if prize_id in self.ids:
                self.ids[prize_id].text = '0'

        if not matched_records:
            no_data_label = Label(
                text='查無符合的開獎記錄',
                font_name='ChineseFont',
                font_size=dp(16),
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(100)
            )
            self.ids.results_layout.add_widget(no_data_label)
            self.ids.total_count_label.text = '0'
            return

        # 統計獎別
        prize_counts = Counter(record['獎別全名'] for record in matched_records)

        for prize_full, count in prize_counts.items():
            if prize_full in prize_map and prize_map[prize_full] in self.ids:
                self.ids[prize_map[prize_full]].text = str(count)

        # 顯示結果
        for row in matched_records:
            # 創建結果行容器
            result_row = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(70),
                spacing=dp(5)
            )

            # 期別和日期行
            info_row = BoxLayout(
                size_hint_y=None,
                height=dp(20)
            )
            
            period_label = Label(
                text=f"期別: {row['期別']}",
                font_name='ChineseFont',
                font_size='12sp',
                size_hint_x=None,
                width=dp(140),
                halign='left',
                valign='middle',
                text_size=(dp(140), None)
            )
            info_row.add_widget(period_label)
            
            date_label = Label(
                text=f"開獎日期: {row['開獎日期']}",
                font_name='ChineseFont',
                font_size='12sp',
                halign='left',
                valign='middle',
                text_size=(None, None)
            )
            date_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
            info_row.add_widget(date_label)
            
            result_row.add_widget(info_row)

            # 獎號和獎別行
            numbers_row = BoxLayout(
                size_hint_y=None,
                height=dp(40)
            )
            
            # 獎號網格
            winning_nums_layout = GridLayout(
                cols=5,
                spacing=dp(5)
            )
            
            for num in sorted(row['獎號']):
                selected = num in selected_numbers
                ball = ResultBall(number=num, area=1, selected=selected)
                winning_nums_layout.add_widget(ball)
            
            numbers_row.add_widget(winning_nums_layout)
            
            # 獎別標籤
            prize_label = Label(
                text=row['獎別簡稱'],
                font_name='ChineseFont',
                font_size=dp(18),
                color=(1, 0, 0, 1),
                size_hint_x=None,
                width=dp(40),
                halign='center',
                valign='middle'
            )
            numbers_row.add_widget(prize_label)
            
            result_row.add_widget(numbers_row)
            self.ids.results_layout.add_widget(result_row)

        self.ids.total_count_label.text = str(len(matched_records))

    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時禁用排序按鈕"""
        Clock.unschedule(self._check_inertia_scroll)
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            logger.debug("今彩539中獎詳情滾動事件被禁用，忽略滾動開始")
            return
        
        # 記錄觸摸開始位置和時間
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start
        logger.debug(f"今彩539中獎詳情觸摸開始: 位置{touch.pos}, 時間{touch.time_start}")

    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            return
        
        # 檢查是否有觸摸開始記錄
        if not hasattr(self, '_touch_start_pos') or not hasattr(self, '_touch_start_time'):
            return
        
        # 計算移動距離
        if self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            # 只有移動距離超過閾值才認為是滑動
            if distance > 10:  # 降低閾值到10像素，更敏感地檢測滑動
                if not self.is_scrolling:
                    self._set_scrolling_state(True)  # 立即設定，不延遲
                    logger.debug(f"今彩539中獎詳情檢測到滑動，移動距離: {distance:.1f}px，立即禁用排序按鈕")

    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多並重新啟用排序按鈕"""
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            logger.debug("今彩539中獎詳情滾動事件被禁用，忽略滾動結束")
            return
        
        # 計算總移動距離和時間
        if hasattr(self, '_touch_start_pos') and hasattr(self, '_touch_start_time'):
            if self._touch_start_pos:
                dx = abs(touch.pos[0] - self._touch_start_pos[0])
                dy = abs(touch.pos[1] - self._touch_start_pos[1])
                distance = (dx * dx + dy * dy) ** 0.5
                duration = touch.time_start - self._touch_start_time
                
                logger.debug(f"今彩539中獎詳情觸摸結束: 移動距離{distance:.1f}px, 持續時間{duration:.2f}s")
                
                # 如果有滑動，需要等待慣性滾動結束
                if distance > 20:
                    # 開始監控慣性滾動
                    self._start_inertia_monitoring(scroll_view)
                    logger.debug("今彩539中獎詳情開始監控慣性滾動")
        
        # 清除觸摸記錄
        self._touch_start_pos = None
        self._touch_start_time = None
        
        # 立即檢查是否需要載入更多（不等慣性滾動結束）
        self._check_load_more_immediate(scroll_view)

    def _start_inertia_monitoring(self, scroll_view):
        """開始監控慣性滾動"""
        Clock.unschedule(self._check_inertia_scroll)
        # 記錄當前滾動位置
        self._last_scroll_y = scroll_view.scroll_y
        self._inertia_check_count = 0
        
        # 每0.1秒檢查一次滾動位置
        Clock.schedule_interval(self._check_inertia_scroll, 0.1)

    def _check_inertia_scroll(self, dt):
        """檢查慣性滾動是否結束"""
        if not hasattr(self.ids, 'scroll_view'):
            return False
        
        scroll_view = self.ids.scroll_view
        current_scroll_y = scroll_view.scroll_y
        
        # 計算滾動位置變化
        scroll_change = abs(current_scroll_y - self._last_scroll_y)
        self._inertia_check_count += 1
        
        logger.debug(f"今彩539中獎詳情慣性檢查 {self._inertia_check_count}: 位置變化 {scroll_change:.4f}")
        
        # 如果滾動位置變化很小，認為慣性滾動結束
        if scroll_change < 0.0005:  # 位置變化小於0.0005（更嚴格的閾值）
            logger.debug("今彩539中獎詳情慣性滾動結束，啟用排序按鈕")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            
            # 檢查是否需要載入更多
            self._check_load_more(scroll_view)
            
            return False  # 停止定時檢查
        
        # 更新上次位置
        self._last_scroll_y = current_scroll_y
        
        # 最多檢查50次（5秒），避免無限檢查，但給更多時間等待滾動完全停止
        if self._inertia_check_count >= 50:
            logger.warning("今彩539中獎詳情慣性檢查超時，強制啟用排序按鈕")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            return False
        
        return True  # 繼續檢查

    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料（不等慣性滾動結束）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        if hasattr(self.ids, 'results_layout'):
            content_height = self.ids.results_layout.height
            viewport_height = scroll_view.height
            current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
            remaining_content = content_height - current_scroll_pos - viewport_height
            
            # 當剩餘內容少於1.5個螢幕高度時開始載入
            if remaining_content <= viewport_height * 1.5:
                logger.debug(f"今彩539中獎詳情立即檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
                self._load_next_page()

    def _check_load_more(self, scroll_view):
        """檢查是否需要載入更多資料（慣性滾動結束後的補充檢查）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        if hasattr(self.ids, 'results_layout'):
            content_height = self.ids.results_layout.height
            viewport_height = scroll_view.height
            current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
            remaining_content = content_height - current_scroll_pos - viewport_height
            
            # 當剩餘內容少於1.5個螢幕高度時開始載入
            if remaining_content <= viewport_height * 1.5:
                logger.debug(f"今彩539中獎詳情慣性滾動結束後檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
                self._load_next_page()

    def go_back(self):
        self.manager.current = 'lotto539_query'

    def on_leave(self):
        self.ids.results_layout.clear_widgets()
        self.ids.selected_nums_layout.clear_widgets()
        self.ids.total_count_label.text = '0'
        
        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third',
            '肆獎': 'prize_count_fourth',
        }
        for prize_id in prize_map.values():
            if prize_id in self.ids:
                self.ids[prize_id].text = '0'

    def perform_winning_query(self):
        app = App.get_running_app()
        selected_numbers = set(self.user_numbers.get('numbers', []))

        db_path = self.db_path
        if not os.path.exists(db_path):
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM lotto_539')
            
            matched_records = []
            for row in cursor:
                winning_numbers = {row[f'num{i}'] for i in range(1, 6)}
                
                prize_full, prize_short = self._determine_winning_award(selected_numbers, winning_numbers)
                
                if prize_full:
                    matched_records.append({
                        '期別': row['issue'],
                        '開獎日期': row['date'],
                        '獎號': sorted(list(winning_numbers)),
                        '獎別全名': prize_full,
                        '獎別簡稱': prize_short
                    })
            
            matched_records.sort(key=lambda x: datetime.strptime(x['開獎日期'], '%Y/%m/%d'), reverse=(self.sort_order == 'DESC'))
            
            conn.close()
            return matched_records
        except Exception as e:
            traceback.print_exc()
            return []

    def _determine_winning_award(self, selected_nums, winning_nums):
        """判斷中獎獎別"""
        matched_count = len(selected_nums.intersection(winning_nums))
        
        if matched_count == 5:
            return '頭獎', '頭'
        elif matched_count == 4:
            return '貳獎', '貳'
        elif matched_count == 3:
            return '參獎', '參'
        elif matched_count == 2:
            return '肆獎', '肆'
        
        return None, ''


class Lotto539DuplicateScreen(Screen):
    """重複五碼查詢界面"""
    duplicates = ListProperty([])
    
    # 分頁相關屬性
    all_duplicates = ListProperty([])  # 完整查詢結果
    displayed_duplicates = ListProperty([])  # 當前顯示的結果
    current_page = NumericProperty(0)     # 當前頁數
    page_size = NumericProperty(30)       # 每頁顯示數量
    is_loading_more = BooleanProperty(False)  # 是否正在載入更多
    has_more_data = BooleanProperty(True)     # 是否還有更多資料
    is_scrolling = BooleanProperty(False)     # 是否正在滾動
    
    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"今彩539重複五碼進入頁面，初始化滾動狀態: {self.is_scrolling}")
        
        # 重置分頁狀態
        self._reset_pagination_state()
        
        # 清空列表並重置滾動位置
        if hasattr(self.ids, 'duplicate_list'):
            self.ids.duplicate_list.clear_widgets()
        self._reset_scroll_to_top()
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='查詢重複五碼中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_duplicate_query(), 0.1)

    def _reset_pagination_state(self):
        """重置分頁狀態"""
        self.duplicates = []
        self.all_duplicates = []
        self.displayed_duplicates = []
        self.current_page = 0
        self.is_loading_more = False
        self.has_more_data = True
        logger.debug("今彩539重複五碼重置分頁狀態")

    def _reset_scroll_to_top(self):
        """重置滾動位置到頂部"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                scroll_view.scroll_y = 1  # 滾動到頂部
                logger.debug("今彩539重複五碼滾動位置重置到頂部")
        except Exception as e:
            logger.exception(f"今彩539重複五碼重置滾動位置錯誤: {str(e)}")
    
    def _perform_duplicate_query(self):
        """實際執行重複查詢的方法"""
        try:
            # 1. 執行完整查詢
            self.find_duplicates()
            self.all_duplicates = self.duplicates.copy()  # 保存完整結果
            
            # 2. 初始化分頁
            self._initialize_pagination()
            
            # 3. 載入第一頁資料並顯示
            self._load_first_page()
            self.populate_duplicate_list()
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
        except Exception as e:
            error_msg = f"查詢重複五碼失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            self.show_popup("錯誤", error_msg)
            traceback.print_exc()

    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_duplicates)
        self.current_page = 0
        self.displayed_duplicates = []
        self.has_more_data = total_records > 0
        
        logger.debug(f"今彩539重複五碼分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_duplicates:
            end_index = min(self.page_size, len(self.all_duplicates))
            self.displayed_duplicates = self.all_duplicates[:end_index]
            self.duplicates = self.displayed_duplicates.copy()  # 更新顯示用的duplicates
            self.current_page = 1
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_duplicates)
            logger.debug(f"今彩539重複五碼第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_duplicates)} 筆")
        else:
            self.duplicates = []
            self.displayed_duplicates = []


    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if self.has_more_data:
            load_more_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(60),
                padding=(dp(10), dp(10))
            )
            
            load_more_label = Label(
                text="滑動到底部載入更多",
                font_name='ChineseFont',
                font_size=dp(14),
                color=get_color_from_hex('#888888'),
                halign='center',
                valign='middle'
            )
            load_more_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
            
            load_more_box.add_widget(load_more_label)
            self.ids.duplicate_list.add_widget(load_more_box)
            
            # 儲存引用以便後續更新
            self.load_more_indicator = load_more_box
            self.load_more_label = load_more_label

    def _load_next_page(self):
        """載入下一頁資料"""
        if self.is_loading_more or not self.has_more_data:
            return
        
        self.is_loading_more = True
        
        # 顯示載入提示
        self._show_loading_indicator()
        
        # 延遲載入，避免UI阻塞
        Clock.schedule_once(lambda dt: self._perform_load_next_page(), 0.2)

    def _perform_load_next_page(self):
        """實際執行下一頁載入"""
        try:
            start_index = len(self.displayed_duplicates)
            end_index = min(start_index + self.page_size, len(self.all_duplicates))
            
            if start_index < len(self.all_duplicates):
                # 添加下一頁資料
                next_page_data = self.all_duplicates[start_index:end_index]
                self.displayed_duplicates.extend(next_page_data)
                self.duplicates = self.displayed_duplicates.copy()  # 更新顯示用的duplicates
                self.current_page += 1
                
                # 重新顯示所有資料（保持原始顯示方式）
                self.populate_duplicate_list()
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_duplicates)
                
                logger.debug(f"今彩539重複五碼載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"今彩539重複五碼載入下一頁錯誤: {str(e)}")
            show_popup("錯誤", "載入更多資料失敗")
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()

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


    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'duplicate_list') and self.load_more_indicator in self.ids.duplicate_list.children:
            self.ids.duplicate_list.remove_widget(self.load_more_indicator)

    def show_duplicate_detail(self, duplicate):
        """顯示重複五碼詳情"""
        detail_screen = self.manager.get_screen('lotto539_duplicate_detail')
        detail_screen.duplicate_numbers = duplicate['numbers']
        self.manager.current = 'lotto539_duplicate_detail'

    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時記錄觸摸位置"""
        Clock.unschedule(self._check_inertia_scroll)
        # 記錄觸摸開始位置和時間
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start
        logger.debug(f"今彩539重複五碼觸摸開始: 位置{touch.pos}")

    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        # 檢查是否有觸摸開始記錄
        if not hasattr(self, '_touch_start_pos') or not hasattr(self, '_touch_start_time'):
            return
        
        # 計算移動距離
        if self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            # 只有移動距離超過閾值才認為是滑動（不需要排序按鈕禁用功能）
            if distance > 10:  # 10像素的移動閾值
                if not self.is_scrolling:
                    self.is_scrolling = True
                    logger.debug(f"今彩539重複五碼檢測到滑動，移動距離: {distance:.1f}px")

    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多"""
        # 計算總移動距離和時間
        if hasattr(self, '_touch_start_pos') and hasattr(self, '_touch_start_time'):
            if self._touch_start_pos:
                dx = abs(touch.pos[0] - self._touch_start_pos[0])
                dy = abs(touch.pos[1] - self._touch_start_pos[1])
                distance = (dx * dx + dy * dy) ** 0.5
                duration = touch.time_start - self._touch_start_time
                
                logger.debug(f"今彩539重複五碼觸摸結束: 移動距離{distance:.1f}px, 持續時間{duration:.2f}s")
                
                # 如果有滑動，需要等待慣性滾動結束
                if distance > 10:
                    # 開始監控慣性滾動
                    self._start_inertia_monitoring(scroll_view)
                    logger.debug("今彩539重複五碼開始監控慣性滾動")
        
        # 清除觸摸記錄
        self._touch_start_pos = None
        self._touch_start_time = None
        
        # 立即檢查是否需要載入更多（不等慣性滾動結束）
        self._check_load_more_immediate(scroll_view)

    def _start_inertia_monitoring(self, scroll_view):
        """開始監控慣性滾動"""
        Clock.unschedule(self._check_inertia_scroll)
        # 記錄當前滾動位置
        self._last_scroll_y = scroll_view.scroll_y
        self._inertia_check_count = 0
        
        # 每0.1秒檢查一次滾動位置
        Clock.schedule_interval(self._check_inertia_scroll, 0.1)

    def _check_inertia_scroll(self, dt):
        """檢查慣性滾動是否結束"""
        if not hasattr(self.ids, 'scroll_view'):
            return False
        
        scroll_view = self.ids.scroll_view
        current_scroll_y = scroll_view.scroll_y
        
        # 計算滾動位置變化
        scroll_change = abs(current_scroll_y - self._last_scroll_y)
        self._inertia_check_count += 1
        
        logger.debug(f"今彩539重複五碼慣性檢查 {self._inertia_check_count}: 位置變化 {scroll_change:.4f}")
        
        # 如果滾動位置變化很小，認為慣性滾動結束
        if scroll_change < 0.0005:  # 位置變化小於0.0005
            logger.debug("今彩539重複五碼慣性滾動結束，啟用排序按鈕")
            self.is_scrolling = False
            
            # 檢查是否需要載入更多
            self._check_load_more(scroll_view)
            
            return False  # 停止定時檢查
        
        # 更新上次位置
        self._last_scroll_y = current_scroll_y
        
        # 最多檢查50次（5秒），避免無限檢查
        if self._inertia_check_count >= 50:
            logger.warning("今彩539重複五碼慣性檢查超時，強制啟用排序按鈕")
            self.is_scrolling = False
            return False
        
        return True  # 繼續檢查

    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料（不等慣性滾動結束）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.duplicate_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"今彩539重複五碼立即檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()

    def _check_load_more(self, scroll_view):
        """檢查是否需要載入更多資料（慣性滾動結束後的補充檢查）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.duplicate_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"今彩539重複五碼慣性滾動結束後檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()

    def find_duplicates(self):
        """使用 SQLite 查詢重複五碼"""
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
        self.duplicates = []

        if not os.path.exists(db_path):
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
            SELECT 
                num1, num2, num3, num4, num5,
                COUNT(*) as count,
                GROUP_CONCAT(issue, ', ') as issues
            FROM lotto_539
            GROUP BY num1, num2, num3, num4, num5
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            ''')

            for row in cursor.fetchall():
                self.duplicates.append({
                    'numbers': sorted([row[0], row[1], row[2], row[3], row[4]]),
                    'count': row[5],
                    'issues': row[6]
                })

            conn.close()
        except Exception as e:
            logger.exception(f"重複查詢錯誤: {str(e)}")
            traceback.print_exc()
    
    def populate_duplicate_list(self):
        """填充重複號碼列表"""
        duplicate_list = self.ids.duplicate_list
        duplicate_list.clear_widgets()
        
        if not self.duplicates:
            duplicate_list.add_widget(Label(
                text="沒有重複的五碼組合",
                font_name='ChineseFont',
                font_size=dp(18),
                color=get_color_from_hex('#FF0000'),
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(50),
                padding=(0, dp(20))
            ))
            return
        
        for item in self.duplicates:
            # 創建重複條目
            box = ClickableBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(50),
                spacing=dp(5),
                padding=(dp(10), dp(5)))

            # 號碼球
            for num in sorted(item['numbers']):
                ball = ResultBall(
                    number=num, 
                    area=1,
                    size_hint=(None, None),
                    size=(dp(30), dp(30)))
                box.add_widget(ball)
        
            # 重複次數
            count_label = Label(
                text=f"({item['count']}次)",
                font_name='ChineseFont',
                font_size=dp(20),
                color=(1, 1, 1, 1),
                size_hint_x=None,
                width=dp(40),
                halign='center'
            )
            box.add_widget(count_label)
        
            # 點擊事件
            box.bind(on_release=lambda instance, item=item: 
                    self._handle_duplicate_item_click(instance, item))
        
            duplicate_list.add_widget(box)
        
            # 分隔線
            separator = BoxLayout(size_hint_y=None, height=dp(1))
            with separator.canvas:
                Color(rgba=get_color_from_hex('#888888'))
                Rectangle(pos=separator.pos, size=separator.size)
            duplicate_list.add_widget(separator)

    def _handle_duplicate_item_click(self, instance, item):
        """處理重複項目的點擊事件"""
        self.show_duplicate_details(item['numbers'])
    
    def show_duplicate_details(self, numbers):
        """從 SQLite 載入詳細記錄"""
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
        details = []

        if not os.path.exists(db_path):
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
            SELECT 
                issue, date,
                num1, num2, num3, num4, num5
            FROM lotto_539
            WHERE num1 IN (?,?,?,?,?)
              AND num2 IN (?,?,?,?,?)
              AND num3 IN (?,?,?,?,?)
              AND num4 IN (?,?,?,?,?)
              AND num5 IN (?,?,?,?,?)
            ORDER BY date DESC
            ''', numbers * 5)

            for row in cursor.fetchall():
                details.append({
                    '期別': row[0],
                    '開獎日期': row[1],
                    '獎號': [row[2], row[3], row[4], row[5], row[6]]
                })

            conn.close()
        except Exception as e:
            logger.exception(f"詳細記錄查詢錯誤: {str(e)}")
            traceback.print_exc()

        detail_screen = self.manager.get_screen('lotto539_duplicate_detail')
        detail_screen.details = details
        self.manager.current = 'lotto539_duplicate_detail'
    
    def back_to_query(self):
        """返回查詢界面"""
        self.manager.current = 'lotto539_query'

    def show_popup(self, title, message):
        """顯示消息彈窗"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 添加標題
        title_label = Label(
            text=title,
            font_name='ChineseFont',
            font_size=dp(16),
            bold=True,
            color=(1, 0, 0, 1)
        )
        content.add_widget(title_label)
        
        # 添加消息內容
        message_label = Label(
            text=message,
            font_name='ChineseFont',
            font_size=dp(14)
        )
        content.add_widget(message_label)
        
        # 添加確定按鈕
        btn = Button(
            text="確定",
            size_hint_y=None,
            height=40,
            font_name='ChineseFont'
        )
        
        # 創建彈窗
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.7, 0.3),
            separator_height=0
        )
        
        # 綁定按鈕事件
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()


class Lotto539DuplicateDetailScreen(Screen):
    """重複五碼詳細信息界面"""
    details = ListProperty([])
    
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
    
    # 分頁相關屬性
    all_details = ListProperty([])  # 完整查詢結果
    displayed_details = ListProperty([])  # 當前顯示的結果
    current_page = NumericProperty(0)     # 當前頁數
    page_size = NumericProperty(30)       # 每頁顯示數量
    is_loading_more = BooleanProperty(False)  # 是否正在載入更多
    has_more_data = BooleanProperty(True)     # 是否還有更多資料
    is_scrolling = BooleanProperty(False)     # 是否正在滾動
    duplicate_numbers = ListProperty([])      # 重複號碼
    
    def on_pre_enter(self):
        """進入屏幕前填充數據"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"今彩539重複記錄詳情進入頁面，初始化滾動狀態: {self.is_scrolling}")
        
        # 重置分頁狀態
        self._reset_pagination_state()
        
        # 清空列表並重置滾動位置
        if hasattr(self.ids, 'detail_list'):
            self.ids.detail_list.clear_widgets()
        self._reset_scroll_to_top()
        
        # 如果有重複號碼，重新查詢詳細記錄
        if self.duplicate_numbers:
            self._perform_detail_query()
        else:
            # 使用現有的details資料進行分頁
            self._initialize_with_existing_data()

    def _reset_pagination_state(self):
        """重置分頁狀態"""
        self.all_details = []
        self.displayed_details = []
        self.current_page = 0
        self.is_loading_more = False
        self.has_more_data = True
        logger.debug("今彩539重複記錄詳情重置分頁狀態")

    def _reset_scroll_to_top(self):
        """重置滾動位置到頂部"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                scroll_view.scroll_y = 1  # 滾動到頂部
                logger.debug("今彩539中獎詳情慣性滾動結束")
        except Exception as e:
            logger.exception(f"今彩539重複記錄詳情重置滾動位置錯誤: {str(e)}")

    def _perform_detail_query(self):
        """執行詳細記錄查詢"""
        try:
            # 查詢詳細記錄
            self._load_duplicate_details()
            
            # 初始化分頁
            self._initialize_pagination()
            
            # 載入第一頁資料
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"今彩539重複記錄詳情分頁查詢錯誤: {str(e)}")
            traceback.print_exc()

    def _initialize_with_existing_data(self):
        """使用現有details資料初始化分頁"""
        if self.details:
            self.all_details = self.details.copy()
            self._initialize_pagination()
            self._load_first_page()
        else:
            self.populate_detail_list()

    def _load_duplicate_details(self):
        """從 SQLite 載入詳細記錄"""
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
        details = []

        if not os.path.exists(db_path):
            self.all_details = []
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
            SELECT 
                issue, date,
                num1, num2, num3, num4, num5
            FROM lotto_539
            WHERE num1 IN (?,?,?,?,?)
              AND num2 IN (?,?,?,?,?)
              AND num3 IN (?,?,?,?,?)
              AND num4 IN (?,?,?,?,?)
              AND num5 IN (?,?,?,?,?)
            ORDER BY date DESC
            ''', self.duplicate_numbers * 5)

            for row in cursor.fetchall():
                details.append({
                    '期別': row[0],
                    '開獎日期': row[1],
                    '獎號': [row[2], row[3], row[4], row[5], row[6]]
                })

            conn.close()
            self.all_details = details
            self.details = details  # 保持向後相容
            
        except Exception as e:
            logger.exception(f"今彩539中獎詳情載入下一頁錯誤: {str(e)}")
            traceback.print_exc()
            self.all_details = []

    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_details)
        self.current_page = 0
        self.displayed_details = []
        self.has_more_data = total_records > 0
        
        logger.debug(f"今彩539重複記錄詳情分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_details:
            end_index = min(self.page_size, len(self.all_details))
            self.displayed_details = self.all_details[:end_index]
            self.details = self.displayed_details.copy()  # 更新顯示用的details
            self.current_page = 1
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_details)
            logger.debug(f"今彩539重複記錄詳情第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_details)} 筆")
        else:
            self.details = []
            self.displayed_details = []
        
        # 設定分頁狀態（假設沒有更多資料，因為這是詳情頁面）
        self.has_more_data = False
        
        # 顯示資料
        self.populate_detail_list()
    
    def populate_detail_list(self):
        """填充詳細記錄列表"""
        detail_list = self.ids.detail_list
        detail_list.clear_widgets()
        
        if not self.details:
            detail_list.add_widget(Label(
                text="沒有詳細記錄",
                font_name='ChineseFont',
                font_size=dp(18),
                color=get_color_from_hex('#FF0000'),
                halign='center'
            ))
            return
        
        for record in self.details:
            # 創建記錄條目
            box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(80),
                spacing=dp(5),
                padding=(dp(10), dp(5)))
            
            # 期別和日期
            row1 = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(30))
            
            period_label = Label(
                text=f"期別: {record['期別']}",
                font_name='ChineseFont',
                font_size='12sp',
                size_hint_x=None,
                width=dp(140),
                halign='left',
                valign='middle',
                text_size=(dp(140), None)
            )
            row1.add_widget(period_label)
            
            date_label = Label(
                text=f"開獎日期: {record['開獎日期']}",
                font_name='ChineseFont',
                font_size='12sp',
                halign='left',
                valign='middle'
            )
            date_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
            row1.add_widget(date_label)
            
            box.add_widget(row1)
            
            # 獎號
            row2 = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(40),
                spacing=dp(10),
                padding=(dp(10), 0))
            
            # 獎號
            for num in sorted(record['獎號']):
                ball = ResultBall(number=num, area=1)
                row2.add_widget(ball)
            
            # 添加空白區域保持對齊
            row2.add_widget(Widget())
            
            box.add_widget(row2)
            
            detail_list.add_widget(box)
        
        # 添加載入更多指示器
        self._add_load_more_indicator_to_detail_list()
    
    def _add_load_more_indicator_to_detail_list(self):
        """添加載入更多指示器到詳情列表"""
        if not hasattr(self.ids, 'detail_list'):
            return
            
        load_more_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            padding=(dp(10), dp(10))
        )
        
        # 根據是否還有更多資料設定不同的文字和透明度
        if hasattr(self, 'has_more_data') and self.has_more_data:
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
        self.ids.detail_list.add_widget(load_more_box)

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if self.has_more_data:
            load_more_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(60),
                padding=(dp(10), dp(10))
            )
            
            load_more_label = Label(
                text="滑動到底部載入更多",
                font_name='ChineseFont',
                font_size=dp(14),
                color=get_color_from_hex('#888888'),
                halign='center',
                valign='middle'
            )
            load_more_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
            
            load_more_box.add_widget(load_more_label)
            self.ids.detail_list.add_widget(load_more_box)
            
            # 儲存引用以便後續更新
            self.load_more_indicator = load_more_box
            self.load_more_label = load_more_label

    def _load_next_page(self):
        """載入下一頁資料"""
        if self.is_loading_more or not self.has_more_data:
            return
        
        self.is_loading_more = True
        
        # 顯示載入提示
        self._show_loading_indicator()
        
        # 延遲載入，避免UI阻塞
        Clock.schedule_once(lambda dt: self._perform_load_next_page(), 0.2)

    def _perform_load_next_page(self):
        """實際執行下一頁載入"""
        try:
            start_index = len(self.displayed_details)
            end_index = min(start_index + self.page_size, len(self.all_details))
            
            if start_index < len(self.all_details):
                # 添加下一頁資料
                next_page_data = self.all_details[start_index:end_index]
                self.displayed_details.extend(next_page_data)
                self.details = self.displayed_details.copy()  # 更新顯示用的details
                self.current_page += 1
                
                # 重新顯示所有資料（保持原始顯示方式）
                self.populate_detail_list()
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_details)
                
                logger.debug(f"今彩539重複記錄詳情載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"今彩539重複記錄詳情載入下一頁錯誤: {str(e)}")
            show_popup("錯誤", "載入更多資料失敗")
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()

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

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'detail_list') and self.load_more_indicator in self.ids.detail_list.children:
            self.ids.detail_list.remove_widget(self.load_more_indicator)

    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時記錄觸摸位置"""
        Clock.unschedule(self._check_inertia_scroll)
        # 記錄觸摸開始位置和時間
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start
        logger.debug(f"今彩539重複五碼觸摸開始: 位置{touch.pos}")

    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        # 檢查是否有觸摸開始記錄
        if not hasattr(self, '_touch_start_pos') or not hasattr(self, '_touch_start_time'):
            return
        
        # 計算移動距離
        if self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            # 只有移動距離超過閾值才認為是滑動（不需要排序按鈕禁用功能）
            if distance > 10:  # 10像素的移動閾值
                if not self.is_scrolling:
                    self.is_scrolling = True
                    logger.debug(f"今彩539重複五碼檢測到滑動，移動距離: {distance:.1f}px")

    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多"""
        # 計算總移動距離和時間
        if hasattr(self, '_touch_start_pos') and hasattr(self, '_touch_start_time'):
            if self._touch_start_pos:
                dx = abs(touch.pos[0] - self._touch_start_pos[0])
                dy = abs(touch.pos[1] - self._touch_start_pos[1])
                distance = (dx * dx + dy * dy) ** 0.5
                duration = touch.time_start - self._touch_start_time
                
                logger.debug(f"今彩539重複五碼觸摸結束: 移動距離{distance:.1f}px, 持續時間{duration:.2f}s")
                
                # 如果有滑動，需要等待慣性滾動結束
                if distance > 10:
                    # 開始監控慣性滾動
                    self._start_inertia_monitoring(scroll_view)
                    logger.debug("今彩539中獎詳情開始監控慣性滾動")
        
        # 清除觸摸記錄
        self._touch_start_pos = None
        self._touch_start_time = None
        
        # 立即檢查是否需要載入更多（不等慣性滾動結束）
        self._check_load_more_immediate(scroll_view)

    def _start_inertia_monitoring(self, scroll_view):
        """開始監控慣性滾動"""
        Clock.unschedule(self._check_inertia_scroll)
        # 記錄當前滾動位置
        self._last_scroll_y = scroll_view.scroll_y
        self._inertia_check_count = 0
        
        # 每0.1秒檢查一次滾動位置
        Clock.schedule_interval(self._check_inertia_scroll, 0.1)

    def _check_inertia_scroll(self, dt):
        """檢查慣性滾動是否結束"""
        if not hasattr(self.ids, 'scroll_view'):
            return False
        
        scroll_view = self.ids.scroll_view
        current_scroll_y = scroll_view.scroll_y
        
        # 計算滾動位置變化
        scroll_change = abs(current_scroll_y - self._last_scroll_y)
        self._inertia_check_count += 1
        
        logger.debug(f"今彩539重複記錄詳情慣性檢查 {self._inertia_check_count}: 位置變化 {scroll_change:.4f}")
        
        # 如果滾動位置變化很小，認為慣性滾動結束
        if scroll_change < 0.0005:  # 位置變化小於0.0005
            logger.debug("今彩539重複記錄詳情慣性滾動結束")
            self.is_scrolling = False
            
            # 檢查是否需要載入更多
            self._check_load_more(scroll_view)
            
            return False  # 停止定時檢查
        
        # 更新上次位置
        self._last_scroll_y = current_scroll_y
        
        # 最多檢查50次（5秒），避免無限檢查
        if self._inertia_check_count >= 50:
            logger.warning("今彩539重複記錄詳情慣性檢查超時，強制結束")
            self.is_scrolling = False
            return False
        
        return True  # 繼續檢查

    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料（不等慣性滾動結束）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.detail_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"今彩539重複記錄詳情立即檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()

    def _check_load_more(self, scroll_view):
        """檢查是否需要載入更多資料（慣性滾動結束後的補充檢查）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.detail_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"今彩539重複記錄詳情慣性滾動結束後檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()
    
    def back_to_duplicate(self):
        """返回重複列表界面"""
        self.manager.current = 'lotto539_duplicate'


class Lotto539DuplicateScreen(BaseAdvancedResultScreen):
    """今彩539重複五碼查詢"""
    duplicates = ListProperty([])
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'lotto_539'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5']
    
    @property
    def special_column(self):
        return None  # 今彩539沒有特別號
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 重複號碼查詢頁面禁用排序功能
        self.enable_sort = False

    # __init__ 已在上面定義
    
    def _update_result_list(self):
        """更新結果列表顯示 - 實現基類抽象方法"""
        try:
            # 清空結果列表
            self.ids.duplicate_list.clear_widgets()
            
            # 添加總筆數顯示
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = f"總筆數: {len(self.all_results)}"
            
            if not self.displayed_results:
                self.ids.duplicate_list.add_widget(Label(
                    text="沒有重複的五碼組合",
                    font_name='ChineseFont',
                    font_size=dp(18),
                    color=get_color_from_hex('#FF0000'),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(50),
                    padding=(0, dp(20))
                ))
                return

            # 顯示當前頁的結果
            for item in self.displayed_results:
                item_widget = self._create_duplicate_item(item)
                self.ids.duplicate_list.add_widget(item_widget)
                
                # 添加分隔線（除了最後一個項目）
                if item != self.displayed_results[-1]:
                    separator = BoxLayout(size_hint_y=None, height=dp(1))
                    with separator.canvas:
                        Color(rgba=get_color_from_hex('#888888'))
                        Rectangle(pos=separator.pos, size=separator.size)
                    self.ids.duplicate_list.add_widget(separator)
            
            # 添加載入更多指示器
            self._add_load_more_indicator()
            
        except Exception as e:
            logger.exception(f"今彩539重複五碼更新列表錯誤: {str(e)}")
            traceback.print_exc()
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            # 保存當前滾動位置
            scroll_view = self.ids.scroll_view
            content_height_before = self.ids.duplicate_list.height
            viewport_height = scroll_view.height
            current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, content_height_before - viewport_height)
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 添加新記錄
            for item in new_records:
                item_widget = self._create_duplicate_item(item)
                self.ids.duplicate_list.add_widget(item_widget)
                
                # 添加分隔線（除了最後一個項目）
                if item != new_records[-1] or len(self.displayed_results) < len(self.all_results):
                    separator = BoxLayout(size_hint_y=None, height=dp(1))
                    with separator.canvas:
                        Color(rgba=get_color_from_hex('#888888'))
                        Rectangle(pos=separator.pos, size=separator.size)
                    self.ids.duplicate_list.add_widget(separator)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            
        except Exception as e:
            logger.exception(f"今彩539重複五碼追加記錄錯誤: {str(e)}")
            traceback.print_exc()
    
    def _create_duplicate_item(self, item):
        """創建重複項目的UI組件"""
        # 這個方法需要根據今彩539的具體UI需求來實現
        # 暫時返回一個基本的Label，實際實現時需要根據原有邏輯調整
        return Label(
            text=f"重複組合: {item}",
            font_name='ChineseFont',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )

    def on_pre_enter(self):
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"今彩539重複五碼頁面進入，初始化滾動狀態: {self.is_scrolling}")
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='查詢重複五碼中')
        self.loading_popup.open()
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_duplicate_query(), 0.1)

    def _perform_duplicate_query(self):
        """執行重複查詢"""
        try:
            self.find_duplicates()
            # 填充列表並重置滾動位置
            self.populate_duplicate_list()
            logger.warning("今彩539中獎詳情慣性檢查超時，強制結束")
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
        except Exception as e:
            logger.exception(f"今彩539中獎詳情分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            if hasattr(self, 'loading_popup'):
                self.loading_popup.dismiss()
            show_popup("錯誤", f"查詢失敗: {str(e)}")

    def find_duplicates(self):
        """查找重複的五碼組合"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查詢所有今彩539記錄
            cursor.execute("SELECT issue, date, num1, num2, num3, num4, num5 FROM lotto_539 ORDER BY date DESC")
            rows = cursor.fetchall()
            conn.close()
            
            # 統計每個五碼組合的出現次數
            number_combinations = {}
            for row in rows:
                issue, date, n1, n2, n3, n4, n5 = row
                numbers = tuple(sorted([n1, n2, n3, n4, n5]))
                
                if numbers not in number_combinations:
                    number_combinations[numbers] = []
                number_combinations[numbers].append({
                    '期別': issue,
                    '開獎日期': date,
                    '獎號': [n1, n2, n3, n4, n5]
                })
            
            # 找出重複的組合（出現次數 > 1）
            self.duplicates = []
            for numbers, records in number_combinations.items():
                if len(records) > 1:
                    self.duplicates.append({
                        'numbers': list(numbers),
                        'count': len(records),
                        'records': records
                    })
            
            # 按出現次數排序
            self.duplicates.sort(key=lambda x: x['count'], reverse=True)
            
            logger.debug(f"今彩539找到 {len(self.duplicates)} 組重複五碼")
            
        except Exception as e:
            logger.exception(f"今彩539中獎詳情排序錯誤: {str(e)}")
            traceback.print_exc()
            self.duplicates = []

    def populate_duplicate_list(self):
        """填充重複號碼列表（分頁版本）"""
        try:
            logger.debug(f"今彩539重複五碼列表開始填充: 總筆數={len(self.duplicates)}")
            
            # 保存重複號碼資料
            self.all_results = self.duplicates
            
            # 更新總筆數顯示
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = f'總筆數: {len(self.duplicates)}'
                logger.debug(f"今彩539重複五碼更新總筆數顯示: {len(self.duplicates)}")
            
            # 確保滾動狀態正確初始化
            self.is_scrolling = False
            self._scroll_events_disabled = False
            
            # 清空結果列表
            self.ids.duplicate_list.clear_widgets()
            
            # 初始化分頁並載入第一頁
            self._initialize_pagination()
            self._load_first_page()
            
            # 重置滾動位置到頂部
            self._reset_scroll_to_top()
            logger.debug("今彩539重複記錄詳情慣性滾動結束")
            
        except Exception as e:
            logger.exception(f"今彩539重複五碼列表填充錯誤: {str(e)}")
            traceback.print_exc()

    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > self.page_size
        
        logger.debug(f"今彩539重複五碼分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"今彩539重複五碼第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self._update_result_list()  # 顯示無資料

    # _update_result_list 已在上面定義

    def _create_duplicate_item(self, item):
        """創建重複號碼項目的UI組件"""
        box = ClickableBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5),
            padding=(dp(10), dp(5)))

        for num in item['numbers']:
            ball = ResultBall(
                number=num, 
                area=1,
                selected=False,  # 顯示黃色
                lotto_type='lotto539',
                size_hint=(None, None),
                size=(dp(30), dp(30)))
            box.add_widget(ball)
    
        count_label = Label(
            text=f"({item['count']}次)",
            font_name='ChineseFont',
            font_size=dp(20),
            color=(1, 1, 1, 1),
            size_hint_x=None,
            width=dp(60),
            halign='center'
        )
        box.add_widget(count_label)
    
        box.bind(on_release=lambda instance, item=item: 
                self._handle_duplicate_item_click(instance, item))
    
        return box

    def _handle_duplicate_item_click(self, instance, item):
        """處理重複項目點擊事件"""
        # 切換到詳情頁面
        detail_screen = self.manager.get_screen('lotto539_duplicate_detail')
        detail_screen.details = item['records']
        self.manager.current = 'lotto539_duplicate_detail'

    def back_to_query(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_back_to_query)

    def _real_back_to_query(self):
        """返回查詢頁面"""
        self.manager.current = 'lotto539_query'

    # 添加滾動處理方法（簡化版，因為沒有排序按鈕）
    def _reset_scroll_to_top(self):
        """重置滾動位置到頂部"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                Clock.schedule_once(lambda dt: setattr(scroll_view, 'scroll_y', 1), 0.2)
                logger.warning("今彩539重複記錄詳情慣性檢查超時，強制結束")
        except Exception as e:
            logger.exception(f"今彩539重複五碼重置滾動位置錯誤: {str(e)}")

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'duplicate_list'):
            return
            
        load_more_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            padding=(dp(10), dp(10))
        )
        
        text = "滑動到底部載入更多" if self.has_more_data else "已顯示全部資料"
        opacity = 0.7 if self.has_more_data else 0.5
        
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
        self.ids.duplicate_list.add_widget(load_more_box)
        
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label

    # 添加完整的分頁載入功能
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
                
                # 移除舊的載入指示器
                self._remove_load_more_indicator()
                
                # 添加新記錄
                for item in next_page_data:
                    item_widget = self._create_duplicate_item(item)
                    self.ids.duplicate_list.add_widget(item_widget)
                    
                    # 添加分隔線
                    if item != next_page_data[-1] or end_index < len(self.all_results):
                        separator = BoxLayout(size_hint_y=None, height=dp(1))
                        with separator.canvas:
                            Color(rgba=get_color_from_hex('#888888'))
                            Rectangle(pos=separator.pos, size=separator.size)
                        self.ids.duplicate_list.add_widget(separator)
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_results)
                
                # 重新添加載入指示器
                self._add_load_more_indicator()
                
                logger.debug(f"今彩539重複五碼載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"今彩539重複五碼載入下一頁錯誤: {str(e)}")
            traceback.print_exc()
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()

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

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'duplicate_list') and self.load_more_indicator in self.ids.duplicate_list.children:
            self.ids.duplicate_list.remove_widget(self.load_more_indicator)

    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時的處理"""
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start

    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        if not hasattr(self, '_touch_start_pos'):
            return
        
        if self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance > 20:
                if not self.is_scrolling:
                    self.is_scrolling = True

    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多"""
        self.is_scrolling = False
        self._touch_start_pos = None
        self._touch_start_time = None
        self._check_load_more_immediate(scroll_view)

    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        content_height = self.ids.duplicate_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        if remaining_content <= viewport_height * 1.0:
            self._load_next_page()

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
                
                # 移除舊的載入指示器
                self._remove_load_more_indicator()
                
                # 添加新記錄
                for item in next_page_data:
                    item_widget = self._create_duplicate_item(item)
                    self.ids.duplicate_list.add_widget(item_widget)
                    
                    # 添加分隔線（除了最後一個項目）
                    if item != next_page_data[-1] or end_index < len(self.all_results):
                        separator = BoxLayout(size_hint_y=None, height=dp(1))
                        with separator.canvas:
                            Color(rgba=get_color_from_hex('#888888'))
                            Rectangle(pos=separator.pos, size=separator.size)
                        self.ids.duplicate_list.add_widget(separator)
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_results)
                
                # 重新添加載入指示器
                self._add_load_more_indicator()
                
                logger.debug(f"今彩539重複五碼載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"今彩539重複五碼載入下一頁錯誤: {str(e)}")
            traceback.print_exc()
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()

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

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'duplicate_list') and self.load_more_indicator in self.ids.duplicate_list.children:
            self.ids.duplicate_list.remove_widget(self.load_more_indicator)

    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時的處理"""
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start

    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        if not hasattr(self, '_touch_start_pos'):
            return
        
        if self._touch_start_pos:
            dx = abs(touch.pos[0] - self._touch_start_pos[0])
            dy = abs(touch.pos[1] - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance > 20:
                if not self.is_scrolling:
                    self.is_scrolling = True

    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多"""
        self.is_scrolling = False
        self._touch_start_pos = None
        self._touch_start_time = None
        self._check_load_more_immediate(scroll_view)

    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        content_height = self.ids.duplicate_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        if remaining_content <= viewport_height * 1.0:
            self._load_next_page()



class Lotto539SavedScreen(BaseLotterySavedScreen):
    """今彩539自選號管理界面"""
    
    @property
    def lottery_type(self):
        return '539'

    def on_pre_enter(self):
        """進入屏幕前的初始化"""
        self.is_scrolling = False
        self._scroll_events_disabled = False
        self.load_saved_numbers()
        self.populate_saved_list()
        logger.debug(f"今彩539自選號頁面進入，總筆數: {len(self.all_results)}")

    def use_saved_number(self, index):
        """使用選中的今彩539自選號（支援分頁索引轉換）"""
        actual_index = index
        if hasattr(self, 'displayed_results') and index < len(self.displayed_results):
            target_item = self.displayed_results[index]
            actual_index = next((i for i, item in enumerate(self.all_results) if item['id'] == target_item['id']), index)
        
        if 0 <= actual_index < len(self.all_results):
            saved = self.all_results[actual_index]
            query_screen = self.manager.get_screen('lotto539_query')
            query_screen.selected_numbers = set(saved['numbers'])
            query_screen.update_number_grid()
            self.manager.current = 'lotto539_query'

