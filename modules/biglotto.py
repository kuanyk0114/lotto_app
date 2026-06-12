import os
import traceback
from datetime import datetime
import sqlite3
from collections import Counter
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, DictProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from .common import show_popup, BallButton, ResultBall, LoadingPopup, DatabaseManager, BaseLotteryQueryScreen, BaseLotterySavedScreen, BaseAdvancedResultScreen, ClickableBoxLayout
from kivy.utils import get_color_from_hex
from kivy.app import App
from kivy.graphics import Color, Rectangle
import logging
logger = logging.getLogger(__name__)



class BigLottoQueryScreen(BaseLotteryQueryScreen):
    selected_numbers = ObjectProperty(set())
    
    # 實作抽象屬性
    @property
    def lottery_type(self):
        return 'big'
    
    @property
    def table_name(self):
        return 'big_lotto'
    
    @property
    def max_numbers(self):
        return 6
    
    def get_selected_numbers(self):
        return list(self.selected_numbers)
    
    def validate_selection(self):
        """覆寫驗證邏輯 - 查詢時只需要至少1個號碼"""
        if not self.selected_numbers:
            return False, "請至少選擇1個號碼"
        return True, ""
    
    def validate_for_save(self):
        """儲存時的驗證邏輯"""
        if len(self.selected_numbers) != 6:
            return False, "請選擇6個號碼才能儲存"
        return True, ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_numbers = set()

    def on_enter(self):
        self.update_number_grid()

    def update_number_grid(self):
        grid = self.ids.number_grid
        grid.clear_widgets()
        for i in range(1, 50):
            ball = BallButton(text=str(i))
            # 暫時解除綁定，避免觸發 on_ball_selected
            ball.unbind(selected=self.on_ball_selected)
            if i in self.selected_numbers:
                ball.selected = True
            else:
                ball.selected = False # 確保未選中的球狀態正確
            # 重新綁定
            ball.bind(selected=self.on_ball_selected)
            grid.add_widget(ball)

    def on_ball_selected(self, instance, value):
        number = int(instance.text)
        if value:
            if len(self.selected_numbers) < self.max_numbers:
                self.selected_numbers.add(number)
            else:
                instance.selected = False
                show_popup('提示', f'最多只能選擇 {self.max_numbers} 個號碼')
        else:
            if number in self.selected_numbers:
                self.selected_numbers.remove(number)

    def clear_selection(self):
        self.selected_numbers.clear()
        for child in self.ids.number_grid.children:
            if isinstance(child, BallButton):
                child.selected = False

    def query_history(self):
        """大樂透特殊的查詢邏輯 - 覆寫基礎類別方法"""
        if not self.selected_numbers:
            show_popup('提示', '請至少選擇1個號碼')
            return
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='大樂透查詢中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._perform_query(), 0.1)

    def _perform_query(self):
        """實際執行查詢的方法"""
        try:
            results_screen = self.manager.get_screen('biglotto_results')
            results_screen.show_results(self.selected_numbers)
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
            # 切換到結果屏幕
            self.manager.current = 'biglotto_results'
        except Exception as e:
            error_msg = f"查詢失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            show_popup("錯誤", error_msg)

    # save_custom_numbers 和 show_custom_numbers 現在由基礎類別提供

    def query_repeated_numbers(self):
        self.manager.current = 'biglotto_repeated_numbers'

    def query_winning_details(self):
        """查詢中獎詳情 - 保留特有功能"""
        if len(self.selected_numbers) != 6:
            show_popup('提示', '請選擇6個號碼或提取自選號')
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
                'area1': list(self.selected_numbers)
            }
            
            winning_details_screen = self.manager.get_screen('biglotto_winning_details')
            winning_details_screen.query_params = query_params
            winning_details_screen.sort_order = 'DESC'
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
            # 切換到中獎詳情屏幕
            self.manager.current = 'biglotto_winning_details'
        except Exception as e:
            error_msg = f"中獎詳情查詢失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            show_popup("錯誤", error_msg)
            traceback.print_exc()

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

class BigLottoResultsScreen(BaseAdvancedResultScreen):
    user_numbers = DictProperty({})
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'big_lotto'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    
    @property
    def special_column(self):
        return 'special_num'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保大樂透查詢結果頁面預設為降序排列
        self.sort_order = 'DESC'

    # on_pre_enter 現在由基類提供
    
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
            logger.exception(f"大樂透結果列表更新錯誤: {str(e)}")
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            # 保存當前滾動的絕對位置
            scroll_view = self.ids.scroll_view
            if hasattr(self.ids, 'scroll_view'):
                # 計算當前滾動的絕對像素位置
                current_content_height = self.ids.results_layout.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                
                logger.debug(f"大樂透載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
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
            logger.exception(f"大樂透追加結果錯誤: {str(e)}")

    def go_back(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_go_back)

    def _real_go_back(self):
        self.manager.current = 'biglotto'
        self.on_leave()

    def on_leave(self):
        self.ids.results_layout.clear_widgets()
        self.ids.selected_nums_layout.clear_widgets()
        self.ids.total_count_label.text = '0'
        
        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third',
            '肆獎': 'prize_count_fourth',
            '伍獎': 'prize_count_fifth',
            '陸獎': 'prize_count_sixth',
            '柒獎': 'prize_count_seventh',
            '普獎': 'prize_count_eighth',
        }
        for prize_id in prize_map.values():
            if prize_id in self.ids:
                self.ids[prize_id].text = '0'

    # toggle_sort_order 現在由基類提供

    # 分頁載入相關方法現在由基類提供
    
    
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
                logger.debug(f"大樂透載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"大樂透恢復滾動位置錯誤: {str(e)}")
    
    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
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
        self.ids.results_layout.add_widget(load_more_box)
        
        # 儲存引用以便後續更新
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label
    
    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and self.load_more_indicator in self.ids.results_layout.children:
            self.ids.results_layout.remove_widget(self.load_more_indicator)
    
    def toggle_sort_order(self):
        """切換排序方式（檢查是否在滾動中）"""
        logger.debug(f"大樂透排序按鈕被點擊，滾動狀態: {self.is_scrolling}")
        
        if self.is_scrolling:
            logger.debug("大樂透滾動中，忽略排序請求")
            return
        
        logger.debug("大樂透開始執行排序")
        loading_popup = LoadingPopup(title='重新排序中')
        loading_popup.open()
        
        Clock.schedule_once(lambda dt: self._perform_sort(loading_popup), 0.1)

    def toggle_sort_order_safe(self):
        """安全的排序切換方法（確保有滾動檢查）"""
        logger.debug(f"大樂透安全排序被調用，滾動狀態: {getattr(self, 'is_scrolling', False)}")
        
        if getattr(self, 'is_scrolling', False):
            logger.debug("大樂透滾動中，忽略排序請求")
            return
        
        logger.debug("大樂透開始執行安全排序")
        loading_popup = LoadingPopup(title='重新排序中')
        loading_popup.open()
        
        Clock.schedule_once(lambda dt: self._perform_sort(loading_popup), 0.1)

    def get_prize_info(self, matched_nums, special_matched):
        """大樂透特有的獎別計算邏輯"""
        if matched_nums == 6:
            return '頭獎', '頭'
        if matched_nums == 5 and special_matched:
            return '貳獎', '貳'
        if matched_nums == 5 and not special_matched:
            return '參獎', '參'
        if matched_nums == 4 and special_matched:
            return '肆獎', '肆'
        if matched_nums == 4 and not special_matched:
            return '伍獎', '伍'
        if matched_nums == 3 and special_matched:
            return '陸獎', '陸'
        if matched_nums == 2 and special_matched:
            return '柒獎', '柒'
        if matched_nums == 3 and not special_matched:
            return '普獎', '普'
        return '未中獎', ''

    def show_results(self, selected_numbers):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 儲存用戶選號
            self.user_numbers = {'selected_numbers': list(selected_numbers)}
            
            # 1. 執行完整查詢（用於統計）
            self.all_results = self._query_all_data(selected_numbers)
            
            # 2. 初始化分頁
            self._initialize_pagination()
            
            # 3. 更新UI（統計區塊和用戶選號）
            self._update_ui(selected_numbers)
            
            # 4. 載入第一頁資料
            self._load_first_page()
            
            # 5. 確保排序功能在查詢完成後可用
            Clock.schedule_once(lambda dt: self._ensure_sort_enabled(), 1.0)
            
        except Exception as e:
            logger.exception(f"大樂透分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _query_all_data(self, selected_numbers):
        """執行完整的資料庫查詢"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT issue, date, num1, num2, num3, num4, num5, num6, special_num FROM big_lotto WHERE "
        conditions = []
        for num in selected_numbers:
            conditions.append(f"({num} IN (num1, num2, num3, num4, num5, num6, special_num))")
        query += " AND ".join(conditions)
        query += f" ORDER BY date {self.sort_order}"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        # 處理查詢結果
        processed_results = []
        selected_numbers_set = set(selected_numbers)

        for row in rows:
            issue, date, n1, n2, n3, n4, n5, n6, special_num = row
            winning_nums_list = [n1, n2, n3, n4, n5, n6]
            winning_nums_set = set(winning_nums_list)

            matched_nums = len(selected_numbers_set.intersection(winning_nums_set))
            special_matched = special_num in selected_numbers_set

            prize, abbreviated_prize = self.get_prize_info(matched_nums, special_matched)
            
            # 處理日期
            try:
                date_obj = datetime.strptime(date, '%Y/%m/%d').date()
            except ValueError:
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                except ValueError:
                    date_obj = datetime.min.date()

            processed_results.append({
                '期別': issue,
                '開獎日期': date,
                '日期物件': date_obj,
                '獎號': winning_nums_list,
                '特別號': special_num,
                '獎別': abbreviated_prize,
                '獎別全名': prize,
                '中獎': prize != '未中獎'
            })
        
        return processed_results
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > self.page_size
        
        logger.debug(f"大樂透分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"大樂透第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self._update_result_list()  # 顯示無資料
    
    def _update_ui(self, selected_numbers):
        """更新UI（統計區塊和用戶選號）"""
        try:
            # 清除舊組件
            self.ids.selected_nums_layout.clear_widgets()

            # 顯示用戶選號
            for num in sorted(list(selected_numbers)):
                ball = ResultBall(number=num, area=1, selected=True, lotto_type='biglotto')
                self.ids.selected_nums_layout.add_widget(ball)

            # 計算統計（基於完整資料）
            prize_counts = Counter()
            for record in self.all_results:
                if record['中獎']:
                    prize_counts[record['獎別全名']] += 1

            # 更新統計區塊
            prize_map = {
                '頭獎': 'prize_count_head',
                '貳獎': 'prize_count_second',
                '參獎': 'prize_count_third',
                '肆獎': 'prize_count_fourth',
                '伍獎': 'prize_count_fifth',
                '陸獎': 'prize_count_sixth',
                '柒獎': 'prize_count_seventh',
                '普獎': 'prize_count_eighth',
            }
            
            # 重置所有獎別統計
            for prize_id in prize_map.values():
                if prize_id in self.ids:
                    self.ids[prize_id].text = '0'

            # 更新總筆數顯示（基於完整資料）
            self.ids.total_count_label.text = str(len(self.all_results))
            
            # 更新各獎別統計
            for prize, count in prize_counts.items():
                if prize in prize_map and prize_map[prize] in self.ids:
                    self.ids[prize_map[prize]].text = str(count)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"大樂透UI更新錯誤: {str(e)}")
    
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
            logger.exception(f"大樂透結果列表更新錯誤: {str(e)}")
    
    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        result_row = Factory.ResultRow()
        result_row.ids.period_label.text = f'期別: {record["期別"]}'
        result_row.ids.date_label.text = f'開獎日期: {record["開獎日期"]}'
        result_row.ids.prize_label.text = record['獎別']
        
        if record['中獎']:
            result_row.ids.prize_label.color = (1, 0, 0, 1)  # 紅色
        else:
            result_row.ids.prize_label.color = (0.5, 0.5, 0.5, 1)  # 灰色

        selected_numbers = set(self.user_numbers['selected_numbers'])
        
        # 添加一般號碼
        for num in record['獎號']:
            ball = ResultBall(number=num, area=1, selected=(num in selected_numbers), lotto_type='biglotto')
            result_row.ids.winning_nums_layout.add_widget(ball)

        # 添加特別號
        special_ball = ResultBall(number=record['特別號'], area=2, selected=(record['特別號'] in selected_numbers), lotto_type='biglotto')
        result_row.ids.winning_nums_layout.add_widget(special_ball)

        return result_row

from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

class BigLottoSavedScreen(BaseLotterySavedScreen):
    
    @property
    def lottery_type(self):
        return 'big'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def on_pre_enter(self):
        """進入屏幕前的初始化"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        
        # 載入數據並初始化分頁
        self.load_saved_numbers()
        self.populate_saved_list()
        
        logger.debug(f"大樂透自選號頁面進入，總筆數: {len(self.all_results)}")

    def use_saved_number(self, index):
        """實作基礎類別的抽象方法（支援分頁索引轉換）"""
        # 計算在完整列表中的實際索引
        actual_index = index
        if hasattr(self, 'displayed_results') and index < len(self.displayed_results):
            target_item = self.displayed_results[index]
            actual_index = next((i for i, item in enumerate(self.all_results) if item['id'] == target_item['id']), index)
        
        if 0 <= actual_index < len(self.all_results):
            saved = self.all_results[actual_index]
            
            query_screen = self.manager.get_screen('biglotto')
            
            # 直接設定 selected_numbers 屬性
            query_screen.selected_numbers = set(saved['numbers'])
            
            # 更新號碼網格顯示
            query_screen.update_number_grid()
            
            self.manager.current = 'biglotto'

class BigLottoRepeatedNumbersScreen(BaseAdvancedResultScreen):
    duplicates = ListProperty([])
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'big_lotto'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    
    @property
    def special_column(self):
        return 'special_num'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 重複號碼查詢頁面禁用排序功能
        self.enable_sort = False
    
    def _update_result_list(self):
        """更新結果列表顯示 - 實現基類抽象方法"""
        try:
            # 清空結果列表
            self.ids.duplicate_list.clear_widgets()
            
            # 添加總筆數顯示
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = f"總筆數: {len(self.all_results)}"
            
            if not self.displayed_results:
                self.ids.duplicate_list.height = dp(50)
                self.ids.duplicate_list.add_widget(Label(
                    text="沒有重複的六碼組合",
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

            # 一次性同步加載所有顯示的項目
            num_items = len(self.displayed_results)
            for i, item in enumerate(self.displayed_results):
                item_widget = self._create_duplicate_item(item)
                self.ids.duplicate_list.add_widget(item_widget)
            
            # 添加載入指示器
            self._add_load_more_indicator()
            logger.debug(f"大樂透重複六碼同步更新完成: 共{num_items}筆")
            
        except Exception as e:
            logger.exception(f"大樂透重複六碼更新列表錯誤: {str(e)}")
            traceback.print_exc()
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            # 確保在非活躍狀態時不繼續添加
            if self.manager.current != self.name:
                return
                
            # 保存當前滾動位置
            scroll_view = self.ids.scroll_view
            content_height_before = self.ids.duplicate_list.height
            viewport_height = scroll_view.height
            current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, content_height_before - viewport_height)
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 同步追加所有新記錄
            for item in new_records:
                item_widget = self._create_duplicate_item(item)
                self.ids.duplicate_list.add_widget(item_widget)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            logger.debug(f"大樂透重複六碼同步追加記錄完成，共追加 {len(new_records)} 筆")
            
        except Exception as e:
            logger.exception(f"大樂透重複六碼追加記錄錯誤: {str(e)}")
            traceback.print_exc()

    def on_pre_enter(self):
        # 呼叫基類方法以清理任何背景滾動與定時器
        super().on_pre_enter()
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"大樂透重複六碼頁面進入，初始化滾動狀態: {self.is_scrolling}")
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='查詢重複六碼中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_duplicate_query(), 0.1)
    
    def _perform_duplicate_query(self):
        """實際執行重複查詢的方法"""
        try:
            self.find_duplicates()
            # 初始化分頁並載入第一頁
            self._initialize_pagination()
            self._load_first_page()
            logger.debug("大樂透重複六碼查詢完成，已重置滾動位置")
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
        except Exception as e:
            error_msg = f"查詢重複六碼失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            self.show_popup("錯誤", error_msg)
            traceback.print_exc()

    def find_duplicates(self):
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
        self.duplicates = []
        self.all_results = []

        if not os.path.exists(db_path):
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
            SELECT 
                num1, num2, num3, num4, num5, num6,
                COUNT(*) as count,
                GROUP_CONCAT(issue, ', ') as issues
            FROM big_lotto
            GROUP BY num1, num2, num3, num4, num5, num6
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            ''')

            for row in cursor.fetchall():
                duplicate_item = {
                    'numbers': sorted([row[0], row[1], row[2], row[3], row[4], row[5]]),
                    'count': row[6],
                    'issues': row[7]
                }
                self.duplicates.append(duplicate_item)
                self.all_results.append(duplicate_item)

            conn.close()
            logger.debug(f"大樂透重複六碼查詢完成: 總筆數={len(self.all_results)}")
        except Exception as e:
            logger.exception(f"重複查詢錯誤: {str(e)}")
            traceback.print_exc()
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > self.page_size
        
        logger.debug(f"大樂透重複六碼分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"大樂透重複六碼第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self.has_more_data = False
            self._update_result_list()  # 顯示無資料


    def _create_duplicate_item(self, item):
        """創建重複號碼項目的UI組件"""
        box = ClickableBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5),
            padding=(dp(10), dp(5)))

        for num in sorted(item['numbers']):
            ball = ResultBall(
                number=num, 
                lotto_type='biglotto',
                selected=False, # 將 selected 設為 False 以顯示黃色
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
        self.show_duplicate_details(item['numbers'])

    def show_duplicate_details(self, numbers):
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
        details = []

        if not os.path.exists(db_path):
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Construct the WHERE clause dynamically for 6 numbers
            where_clause = " AND ".join([f"num{i+1} = ?" for i in range(6)])
            query = f'''
            SELECT 
                issue, date,
                num1, num2, num3, num4, num5, num6,
                special_num
            FROM big_lotto
            WHERE {where_clause}
            ORDER BY date DESC
            '''
            
            # Prepare parameters for the query
            params = tuple(numbers)

            cursor.execute(query, params)

            for row in cursor.fetchall():
                details.append({
                    '期別': row[0],
                    '開獎日期': row[1],
                    '獎號': [row[2], row[3], row[4], row[5], row[6], row[7]],
                    '特別號': row[8]
                })

            conn.close()
        except Exception as e:
            logger.exception(f"詳細記錄查詢錯誤: {str(e)}")
            traceback.print_exc()

        detail_screen = self.manager.get_screen('biglotto_duplicate_detail')
        detail_screen.details = details
        self.manager.current = 'biglotto_duplicate_detail'
    
    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'duplicate_list'):
            logger.warning("大樂透重複六碼找不到duplicate_list，無法添加載入指示器")
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
        self.ids.duplicate_list.add_widget(load_more_box)
        
        # 儲存引用以便後續更新
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'duplicate_list') and self.load_more_indicator in self.ids.duplicate_list.children:
            self.ids.duplicate_list.remove_widget(self.load_more_indicator)

    def _restore_scroll_position_absolute(self, target_absolute_scroll):
        """恢復到指定的絕對滾動位置"""
        try:
            scroll_view = self.ids.scroll_view
            content_height = self.ids.duplicate_list.height
            viewport_height = scroll_view.height
            
            if content_height > viewport_height:
                max_scroll_distance = content_height - viewport_height
                # 準確定位，不加任何偏移以確保無縫滑動
                new_scroll_y = 1 - (target_absolute_scroll / max_scroll_distance)
                new_scroll_y = max(0, min(1, new_scroll_y))
                scroll_view.scroll_y = new_scroll_y
            else:
                scroll_view.scroll_y = 1
                
        except Exception as e:
            logger.exception(f"大樂透重複六碼恢復滾動位置錯誤: {str(e)}")

    def back_to_query(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_back_to_query)

    def _real_back_to_query(self):
        self.manager.current = 'biglotto'

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


class BigLottoDuplicateDetailScreen(BaseAdvancedResultScreen):
    details = ListProperty([])
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'big_lotto'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    
    @property
    def special_column(self):
        return 'special_num'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 重複記錄詳情頁面禁用排序功能（沒有排序鍵）
        self.enable_sort = False
    
    def on_pre_enter(self):
        """進入頁面時初始化分頁顯示"""
        # 基類會處理滾動狀態初始化
        super().on_pre_enter()
        
        # 將 details 轉換為 all_results 格式
        self.all_results = self.details.copy()
        
        # 初始化分頁並載入第一頁
        self._initialize_pagination()
        self._load_first_page()
    
    def _update_result_list(self):
        """更新結果列表顯示 - 實現基類抽象方法"""
        try:
            # 清空結果列表
            self.ids.detail_list.clear_widgets()
            
            if not self.displayed_results:
                self.ids.detail_list.add_widget(Label(
                    text="沒有詳細記錄",
                    font_name='ChineseFont',
                    font_size=dp(18),
                    color=get_color_from_hex('#FF0000'),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(50)
                ))
                return

            # 顯示當前頁的結果
            for record in self.displayed_results:
                item_widget = self._create_detail_item(record)
                self.ids.detail_list.add_widget(item_widget)
            
            # 添加載入更多指示器
            self._add_load_more_indicator()
            
        except Exception as e:
            logger.exception(f"大樂透重複記錄詳情更新列表錯誤: {str(e)}")
            traceback.print_exc()
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            # 保存當前滾動位置
            scroll_view = self.ids.scroll_view
            content_height_before = self.ids.detail_list.height
            viewport_height = scroll_view.height
            current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, content_height_before - viewport_height)
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 添加新記錄
            for record in new_records:
                item_widget = self._create_detail_item(record)
                self.ids.detail_list.add_widget(item_widget)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            
        except Exception as e:
            logger.exception(f"大樂透重複記錄詳情追加記錄錯誤: {str(e)}")
            traceback.print_exc()
    
    def _create_detail_item(self, record):
        """創建詳細記錄項目的UI組件"""
        box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(5),
            padding=(dp(10), dp(5)))
        
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
        
        row2 = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
            padding=(dp(10), 0))
        
        for num in sorted(record['獎號']):
            ball = ResultBall(number=num, lotto_type='biglotto')
            row2.add_widget(ball)
        
        ball = ResultBall(number=record['特別號'], lotto_type='biglotto', area=2) # 大樂透特別號是area=2
        row2.add_widget(ball)
        
        # 添加空白區域保持對齊
        row2.add_widget(Widget())
        
        box.add_widget(row2)
        
        return box
    
    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'detail_list'):
            logger.warning("大樂透重複記錄詳情找不到detail_list，無法添加載入指示器")
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
        self.ids.detail_list.add_widget(load_more_box)
        
        # 儲存引用以便後續更新
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label
    
    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'detail_list') and self.load_more_indicator in self.ids.detail_list.children:
            self.ids.detail_list.remove_widget(self.load_more_indicator)
    
    def _restore_scroll_position_absolute(self, target_absolute_scroll):
        """恢復到指定的絕對滾動位置"""
        try:
            scroll_view = self.ids.scroll_view
            content_height = self.ids.detail_list.height
            viewport_height = scroll_view.height
            
            if content_height > viewport_height:
                max_scroll_distance = content_height - viewport_height
                new_scroll_y = 1 - (target_absolute_scroll / max_scroll_distance)
                new_scroll_y = max(0, min(1, new_scroll_y))
                scroll_view.scroll_y = new_scroll_y
            else:
                scroll_view.scroll_y = 1
                
        except Exception as e:
            logger.exception(f"大樂透重複記錄詳情恢復滾動位置錯誤: {str(e)}")
    
    def back_to_duplicate(self):
        self.manager.current = 'biglotto_repeated_numbers'

class BigLottoWinningDetailsScreen(BaseAdvancedResultScreen):
    user_numbers = DictProperty({})
    query_params = DictProperty({})
    results = ListProperty([])
    stats = DictProperty({})
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'big_lotto'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    
    @property
    def special_column(self):
        return 'special_num'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保大樂透中獎詳情頁面預設為降序排列
        self.sort_order = 'DESC'
    
    def _update_result_list(self):
        """更新結果列表（分頁版本）- 實現基類抽象方法"""
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
            logger.exception(f"大樂透結果列表更新錯誤: {str(e)}")
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            # 保存當前滾動的絕對位置
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                current_content_height = self.ids.results_layout.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                
                logger.debug(f"大樂透載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
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
            logger.exception(f"大樂透追加結果錯誤: {str(e)}")

    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"大樂透進入頁面，初始化滾動狀態: {self.is_scrolling}, 滾動事件啟用: {not self._scroll_events_disabled}")
        
        if self.query_params:
            self.user_numbers = {
                'area1': self.query_params['area1']
            }
            # 執行完整查詢並初始化分頁
            self._perform_full_query_with_pagination()
            # 重置滾動位置到頂部（新查詢）
            self._reset_scroll_to_top()

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
            
            # 4. 更新UI（統計區塊）
            self.update_ui()
            
            # 5. 載入第一頁資料
            self._load_first_page()
            
            # 6. 確保排序按鈕在查詢完成後可用
            Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 1.0)
            
        except Exception as e:
            logger.exception(f"大樂透分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > self.page_size
        
        logger.debug(f"大樂透分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"大樂透第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self.has_more_data = False
            self._update_result_list()  # 顯示無資料

    def toggle_sort_order(self):
        """切換排序方式並重新查詢"""
        logger.debug(f"大樂透排序按鈕被點擊，滾動狀態: {self.is_scrolling}")
        
        if self.is_scrolling:
            logger.debug("大樂透滾動中，忽略排序請求")
            return
        
        logger.debug("大樂透開始執行排序")
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
            logger.debug(f"大樂透排序: sort_order={self.sort_order}, reverse={reverse_order}")
            self.results = self.all_results  # 保持向後相容
            
            # 重新初始化分頁
            self._initialize_pagination()
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"大樂透排序錯誤: {str(e)}")
            traceback.print_exc()
        finally:
            # 關閉載入彈窗
            loading_popup.dismiss()
            # 在所有操作完成後，使用最簡單的方法重置
            Clock.schedule_once(lambda dt: self._simple_reset_scroll(), 0.5)

    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {
            '頭獎': 0, '貳獎': 0, '參獎': 0, '肆獎': 0, '伍獎': 0,
            '陸獎': 0, '柒獎': 0, '普獎': 0
        }
        
        # 遍歷所有結果記錄
        for record in self.results:
            award = record.get('獎別全名', '')
            if award and award in stats:
                stats[award] += 1

        # 更新統計數據
        self.stats = stats

        # 打印調試信息
        logger.debug("大樂透獎別統計結果:")
        for award, count in stats.items():
            logger.debug(f"{award}: {count}")

    def update_ui(self):
        """更新界面顯示（統計區塊和用戶選號）"""
        try:
            # 清除舊組件
            if hasattr(self.ids, 'selected_nums_layout'):
                self.ids.selected_nums_layout.clear_widgets()

            # 更新總筆數顯示（基於完整資料）
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = str(len(self.all_results))

            # 更新各獎別統計
            prize_map = {
                '頭獎': 'prize_count_head',
                '貳獎': 'prize_count_second',
                '參獎': 'prize_count_third',
                '肆獎': 'prize_count_fourth',
                '伍獎': 'prize_count_fifth',
                '陸獎': 'prize_count_sixth',
                '柒獎': 'prize_count_seventh',
                '普獎': 'prize_count_eighth',
            }
            
            for prize_full, prize_id in prize_map.items():
                if hasattr(self.ids, prize_id):
                    getattr(self.ids, prize_id).text = str(self.stats.get(prize_full, 0))

            # 添加自選號球
            if hasattr(self.ids, 'selected_nums_layout'):
                for num in sorted(self.user_numbers.get('area1', [])):
                    ball = ResultBall(number=num, selected=True, lotto_type='biglotto')
                    self.ids.selected_nums_layout.add_widget(ball)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"大樂透UI更新錯誤: {str(e)}")


    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        from kivy.factory import Factory
        
        # 使用Factory創建結果行
        result_row = Factory.ResultRow()
        result_row.ids.period_label.text = f'期別: {record["期別"]}'
        result_row.ids.date_label.text = f'開獎日期: {record["開獎日期"]}'
        result_row.ids.prize_label.text = record['獎別簡稱']
        result_row.ids.prize_label.color = (1, 0, 0, 1)

        selected_numbers = self.user_numbers.get('area1', [])
        
        for num in record['獎號']:
            ball = ResultBall(number=num, area=1, selected=(num in selected_numbers), lotto_type='biglotto')
            result_row.ids.winning_nums_layout.add_widget(ball)

        special_ball = ResultBall(number=record['特別號'], area=2, selected=(record['特別號'] in selected_numbers), lotto_type='biglotto')
        result_row.ids.winning_nums_layout.add_widget(special_ball)

        return result_row

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if hasattr(self.ids, 'results_layout'):
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
                
                logger.debug(f"大樂透載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"大樂透載入下一頁錯誤: {str(e)}")
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
                
                logger.debug(f"大樂透載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
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
            logger.exception(f"大樂透追加結果錯誤: {str(e)}")

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
                logger.debug(f"大樂透載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"大樂透恢復滾動位置錯誤: {str(e)}")

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
                
                logger.debug("大樂透使用動畫重置到頂部")
        except Exception as e:
            logger.exception(f"大樂透簡單重置錯誤: {str(e)}")

    def _disable_scroll_events(self):
        """暫時禁用滾動事件檢測"""
        self._scroll_events_disabled = True
        logger.debug("大樂透暫時禁用滾動事件")

    def _enable_scroll_events(self):
        """重新啟用滾動事件檢測並確保排序按鈕可用"""
        self._scroll_events_disabled = False
        # 確保排序按鈕恢復可用狀態
        Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 0.1)
        logger.debug("大樂透重新啟用滾動事件")

    def _ensure_sort_button_enabled(self):
        """確保排序按鈕處於可用狀態"""
        self.is_scrolling = False
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = False
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
        logger.debug("大樂透確保排序按鈕可用")



    def show_results(self):
        """保留舊版本的show_results方法以保持向後相容"""
        # 這個方法現在主要用於向後相容，實際功能由分頁版本處理
        pass

    def go_back(self):
        self.manager.current = 'biglotto'

    def on_leave(self):
        self.ids.results_layout.clear_widgets()
        self.ids.selected_nums_layout.clear_widgets()
        self.ids.total_count_label.text = '0'
        
        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third',
            '肆獎': 'prize_count_fourth',
            '伍獎': 'prize_count_fifth',
            '陸獎': 'prize_count_sixth',
            '柒獎': 'prize_count_seventh',
            '普獎': 'prize_count_eighth',
        }
        for prize_id in prize_map.values():
            if prize_id in self.ids:
                self.ids[prize_id].text = '0'

    def perform_winning_query(self):
        app = App.get_running_app()
        selected_numbers = set(self.user_numbers.get('area1', []))

        db_path = self.db_path
        if not os.path.exists(db_path):
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM big_lotto')
            
            matched_records = []
            for row in cursor:
                winning_numbers = {row[f'num{i}'] for i in range(1, 7)}
                special_num_drawn = row['special_num']
                
                prize_full, prize_short = self._determine_winning_award(selected_numbers, winning_numbers, special_num_drawn)
                
                if prize_full:
                    matched_records.append({
                        '期別': row['issue'],
                        '開獎日期': row['date'],
                        '獎號': sorted(list(winning_numbers)),
                        '特別號': special_num_drawn,
                        '獎別全名': prize_full,
                        '獎別簡稱': prize_short
                    })
            
            matched_records.sort(key=lambda x: datetime.strptime(x['開獎日期'], '%Y/%m/%d'), reverse=(self.sort_order == 'DESC'))
            
            conn.close()
            return matched_records
        except Exception as e:
            traceback.print_exc()
            return []

    def _determine_winning_award(self, selected_nums, winning_nums, special_num_drawn):
        matched_count_main = len(selected_nums.intersection(winning_nums))

        if special_num_drawn not in selected_nums:
            if matched_count_main == 6: return '頭獎', '頭'
            if matched_count_main == 5: return '參獎', '參'
            if matched_count_main == 4: return '伍獎', '伍'
            if matched_count_main == 3: return '普獎', '普'
        else:
            temp_selected_nums = selected_nums - {special_num_drawn}
            matched_after_special = len(temp_selected_nums.intersection(winning_nums))
            if matched_after_special == 5: return '貳獎', '貳'
            if matched_after_special == 4: return '肆獎', '肆'
            if matched_after_special == 3: return '陸獎', '陸'
            if matched_after_special == 2: return '柒獎', '柒'
        
        return None, ''