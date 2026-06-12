import os
import traceback
from datetime import datetime
import sqlite3
from collections import Counter
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, DictProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from .common import show_popup, BallButton, ResultBall, LoadingPopup, DatabaseManager, BaseLotteryQueryScreen, BaseLotterySavedScreen, BaseAdvancedResultScreen, ClickableBoxLayout, BaseScrollMixin
from kivy.utils import get_color_from_hex
from kivy.app import App
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
import logging
logger = logging.getLogger(__name__)



class Lotto3StarQueryScreen(BaseLotteryQueryScreen):
    """三星彩選號查詢"""
    selected_numbers = ObjectProperty({'hundreds': None, 'tens': None, 'units': None})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_numbers = {'hundreds': None, 'tens': None, 'units': None}
        # 移除舊的 db_path 設定，使用父類的 DatabaseManager

    def load_saved_numbers(self):
        """從資料庫載入三星彩自選號 (不排序)"""
        self.saved_numbers = []
        self.all_results = []
        
        try:
            query = '''
                SELECT id, num1, num2, num3, created_time
                FROM custom_numbers 
                WHERE lottery_type = ?
                ORDER BY created_time DESC
            '''
            rows = self.db_manager.execute_custom_query(query, (self.lottery_type,))
            
            for row in rows:
                # 三星彩號碼有順序性，直接讀取 num1, num2, num3
                numbers = [num for num in row[1:4] if num is not None]
                
                item = {
                    'id': row[0],
                    'numbers': numbers, # 不進行排序
                    'created_time': row[4]
                }
                
                self.saved_numbers.append(item)
                self.all_results.append(item)
                
            logger.info(f"三星彩載入自選號: 總筆數={len(self.all_results)}")
                
        except Exception as e:
            logger.exception(f"載入三星彩自選號失敗: {str(e)}")
            self.handle_database_error(e)

    def on_enter(self):
        self.update_number_grids()

    def update_number_grids(self):
        """更新三個位數的號碼網格"""
        positions = ['hundreds', 'tens', 'units']
        grid_ids = ['hundreds_grid', 'tens_grid', 'units_grid']
        
        for position, grid_id in zip(positions, grid_ids):
            grid = self.ids[grid_id]
            grid.clear_widgets()
            
            for i in range(10):  # 0-9
                ball = BallButton(text=str(i), area=1, lotto_type='lotto3star')
                ball.unbind(selected=lambda instance, value, pos=position: self.on_ball_selected(instance, value, pos))
                
                if self.selected_numbers[position] == i:
                    ball.selected = True
                else:
                    ball.selected = False
                    
                ball.bind(selected=lambda instance, value, pos=position: self.on_ball_selected(instance, value, pos))
                grid.add_widget(ball)

    def on_ball_selected(self, instance, value, position):
        """處理球號選擇"""
        number = int(instance.text)
        
        if value:  # 選中
            # 取消該位數之前選中的球號
            old_number = self.selected_numbers[position]
            if old_number is not None:
                # 找到舊球號並取消選中
                grid_id = f"{position}_grid"
                grid = self.ids[grid_id]
                for child in grid.children:
                    if isinstance(child, BallButton) and child.text == str(old_number):
                        child.selected = False
                        break
            
            self.selected_numbers[position] = number
        else:  # 取消選中
            if self.selected_numbers[position] == number:
                self.selected_numbers[position] = None

    def clear_selection(self):
        """取消所有選取"""
        self.selected_numbers = {'hundreds': None, 'tens': None, 'units': None}
        self.update_number_grids()

    def set_position_number(self, position_index, number):
        """設定指定位置的號碼（用於自選號回填）"""
        positions = ['hundreds', 'tens', 'units']
        if 0 <= position_index < len(positions):
            position = positions[position_index]
            
            # 清除該位置原有選擇
            if self.selected_numbers[position] is not None:
                old_number = self.selected_numbers[position]
                grid_id = f"{position}_grid"
                grid = self.ids[grid_id]
                for child in grid.children:
                    if isinstance(child, BallButton) and child.text == str(old_number):
                        child.selected = False
                        break
            
            # 設定新號碼
            self.selected_numbers[position] = number
            
            # 更新UI顯示
            grid_id = f"{position}_grid"
            grid = self.ids[grid_id]
            for child in grid.children:
                if isinstance(child, BallButton) and child.text == str(number):
                    child.selected = True
                    break

    def apply_selected_numbers(self):
        """應用選中的號碼到UI（更新所有位置的顯示狀態）"""
        self.update_number_grids()

    def query_history(self):
        """查詢歷史開獎"""
        # 檢查是否至少選了一個球號
        if all(v is None for v in self.selected_numbers.values()):
            self.show_popup('提示', '至少要選1個球號')
            return
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='三星彩查詢中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_query(), 0.1)

    def _perform_query(self):
        """實際執行查詢的方法"""
        try:
            results_screen = self.manager.get_screen('lotto3star_results')
            results_screen.show_results(self.selected_numbers)
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
            # 切換到結果屏幕
            self.manager.current = 'lotto3star_results'
        except Exception as e:
            error_msg = f"查詢失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            self.show_popup("錯誤", error_msg)

    @property
    def lottery_type(self):
        """彩種類型標識"""
        return '3star'

    def save_custom_numbers(self):
        """儲存自選號"""
        if any(v is None for v in self.selected_numbers.values()):
            show_popup('提示', '需選滿三位數')
            return
        
        try:
            # 使用 DatabaseManager 的自選號資料庫方法
            query = """
                INSERT INTO custom_numbers (lottery_type, num1, num2, num3, created_time) 
                VALUES (?, ?, ?, ?, ?)
            """
            params = (
                '3star', 
                self.selected_numbers['hundreds'],
                self.selected_numbers['tens'], 
                self.selected_numbers['units'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # 使用自選號資料庫
            self.db_manager.execute_custom_insert(query, params)
            show_popup('成功', '自選號碼已儲存')
        except Exception as e:
            logger.exception(f"三星彩儲存自選號錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            show_popup('錯誤', f'儲存失敗: {e}')

    def show_custom_numbers(self):
        """顯示自選號"""
        self.manager.current = 'lotto3star_saved'
    
    def show_saved_numbers(self):
        """顯示已儲存的自選號 - 與 show_custom_numbers 相同功能"""
        self.manager.current = 'lotto3star_saved'

    def query_repeated_numbers(self):
        """查詢重複三碼"""
        self.manager.current = 'lotto3star_repeated_numbers'

    def query_winning_details(self):
        """查詢自選號中獎詳情"""
        if any(v is None for v in self.selected_numbers.values()):
            self.show_popup('提示', '需選滿三位數，或請先提取自選號')
            return
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='查詢中獎詳情中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_winning_details_query(), 0.1)

    def _perform_winning_details_query(self):
        """實際執行中獎詳情查詢的方法"""
        try:
            winning_details_screen = self.manager.get_screen('lotto3star_winning_details')
            winning_details_screen.user_numbers = dict(self.selected_numbers)
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
            # 切換到中獎詳情屏幕
            self.manager.current = 'lotto3star_winning_details'
        except Exception as e:
            error_msg = f"中獎詳情查詢失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            self.show_popup("錯誤", error_msg)
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


class Lotto3StarResultsScreen(BaseAdvancedResultScreen):
    """三星彩查詢結果"""
    user_numbers = DictProperty({})
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'lotto_3star'
    
    @property
    def number_columns(self):
        return ['number']  # 三星彩使用單一number欄位存儲000-999
    
    @property
    def special_column(self):
        return None  # 三星彩沒有特別號

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保三星彩查詢結果頁面預設為降序排列
        self.sort_order = 'DESC'
    
    query_params = DictProperty({})

    def get_prize_info(self, matched_nums, special_matched):
        """三星彩特有的獎別計算邏輯（數字組合000-999，直選/組選玩法）"""
        # 三星彩的獎別計算需要根據具體的玩法來實現
        # 這裡提供基本的框架，實際邏輯需要根據三星彩規則調整
        if matched_nums >= 1:
            return '中獎', '中'
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
            logger.exception(f"三星彩查詢結果列表更新錯誤: {str(e)}")
    
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
            logger.exception(f"三星彩追加結果錯誤: {str(e)}")
    
    def _create_result_item(self, record):
        """創建結果項目的UI組件 - 和大樂透保持一致"""
        from kivy.factory import Factory
        
        # 使用和大樂透相同的 ResultRow 組件
        result_row = Factory.ResultRow()
        
        # 設定三星彩特有的資料
        result_row.period = record['期別']
        result_row.date = record['開獎日期']
        result_row.numbers = [record['number']]  # 三星彩是單一數字，轉為列表格式
        result_row.special_number = None  # 三星彩沒有特別號
        result_row.award = record.get('獎別', '')
        result_row.lottery_type = 'lotto3star'  # 設定彩券類型
        
        return result_row

    def go_back(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_go_back)

    def _real_go_back(self):
        self.manager.current = 'lotto3star'
        self.on_leave()


    def on_leave(self):
        # 離開頁面時不清空結果，保持狀態
        pass

    def toggle_sort_order(self):
        """切換排序方式並重新查詢"""
        logger.debug(f"=== 三星彩查詢結果排序按鈕被點擊！===")
        logger.debug(f"當前排序: {self.sort_order}")
        
        # 檢查排序按鈕狀態
        if hasattr(self.ids, 'sort_btn'):
            logger.debug(f"排序按鈕存在，disabled={self.ids.sort_btn.disabled}")
            logger.debug(f"排序按鈕文字: {self.ids.sort_btn.text}")
        else:
            logger.debug("排序按鈕不存在！")
            return
        
        # 檢查排序按鈕是否被禁用
        if self.ids.sort_btn.disabled:
            logger.debug("三星彩查詢結果排序按鈕被禁用，忽略排序請求")
            logger.debug(f"當前滾動狀態: is_scrolling={self.is_scrolling}")
            return
        
        # 檢查是否有資料可以排序
        if not hasattr(self, 'all_results') or not self.all_results:
            logger.debug("三星彩查詢結果沒有資料可以排序")
            logger.debug(f"all_results存在: {hasattr(self, 'all_results')}")
            if hasattr(self, 'all_results'):
                logger.debug(f"all_results長度: {len(self.all_results)}")
            return
        
        logger.debug(f"三星彩查詢結果開始排序，資料筆數: {len(self.all_results)}")
        
        # 立即禁用排序按鈕，避免重複點擊
        self.ids.sort_btn.disabled = True
        logger.debug("排序按鈕已禁用")
        
        # 暫時禁用滾動事件，避免排序過程中觸發滾動檢測
        self._disable_scroll_events()
        logger.debug("滾動事件已禁用")
        
        # 顯示載入中彈窗
        loading_popup = LoadingPopup(title='排序中')
        loading_popup.open()
        logger.debug("載入彈窗已顯示")
    
        # 使用 Clock.schedule_once 延遲執行，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_sort(loading_popup), 0.1)
        logger.debug("排序任務已排程")

    def _perform_sort(self, loading_popup):
        """實際執行排序的方法（分頁版本）"""
        try:
            logger.debug(f"三星彩查詢結果執行排序前: sort_order={self.sort_order}, 資料筆數={len(self.all_results)}")
            
            # 切換排序方式
            old_sort_order = self.sort_order
            self.sort_order = 'ASC' if self.sort_order == 'DESC' else 'DESC'
            
            logger.debug(f"三星彩查詢結果排序方式切換: {old_sort_order} -> {self.sort_order}")
        
            # 重新排序完整資料
            reverse_order = (self.sort_order == 'DESC')
            try:
                self.all_results.sort(key=lambda x: datetime.strptime(x['開獎日期'], '%Y/%m/%d'), reverse=reverse_order)
                logger.debug(f"三星彩查詢結果使用日期排序成功")
            except Exception as date_error:
                logger.debug(f"三星彩查詢結果日期排序失敗: {date_error}")
                # 如果日期格式解析失敗，使用字串排序
                self.all_results.sort(key=lambda x: x['開獎日期'], reverse=reverse_order)
                logger.debug(f"三星彩查詢結果使用字串排序")
            
            logger.debug(f"三星彩查詢結果排序完成: sort_order={self.sort_order}, reverse={reverse_order}")
            
            # 重新初始化分頁
            self._initialize_pagination()
            self._load_first_page()
            
            # 排序後重置滾動位置到頂部
            self._reset_scroll_to_top()
            
            logger.debug(f"三星彩查詢結果分頁重新載入完成，已重置滾動位置")
            
        except Exception as e:
            logger.exception(f"三星彩查詢結果排序錯誤: {str(e)}")
            traceback.print_exc()
        finally:
            # 關閉載入彈窗
            loading_popup.dismiss()
            
            # 更新按鈕文字並重新啟用
            if hasattr(self.ids, 'sort_btn'):
                self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
                self.ids.sort_btn.disabled = False
                logger.debug(f"三星彩查詢結果排序按鈕已重新啟用，文字更新為: {self.ids.sort_btn.text}")
            
            # 重新啟用滾動事件
            Clock.schedule_once(lambda dt: self._enable_scroll_events(), 0.1)

    def get_prize_info(self, selected_numbers, n1, n2, n3):
        """根據三星彩中獎規則判斷獎別"""
        # 檢查各位數是否有選擇且匹配
        hundreds_selected = selected_numbers['hundreds'] is not None
        tens_selected = selected_numbers['tens'] is not None
        units_selected = selected_numbers['units'] is not None
        
        hundreds_match = hundreds_selected and selected_numbers['hundreds'] == n1
        tens_match = tens_selected and selected_numbers['tens'] == n2
        units_match = units_selected and selected_numbers['units'] == n3
        
        # 個位沒選或個位沒對中 = 未中獎
        if not units_selected or not units_match:
            return '未中獎', ''
        
        # 個位對中的情況下：
        # 頭獎：佰位、拾位、個位都選且都對中
        if hundreds_selected and tens_selected and hundreds_match and tens_match and units_match:
            return '頭獎', '頭'
        # 貳獎：拾位選且對中，個位對中（佰位可選可不選，選了可對可不對）
        elif tens_selected and tens_match and units_match:
            return '貳獎', '貳'
        # 參獎：個位對中（佰位、拾位可選可不選，選了可對可不對）
        elif units_match:
            return '參獎', '參'
        
        return '未中獎', ''

    def show_results(self, selected_numbers):
        """顯示查詢結果（分頁版本）"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"三星彩查詢結果進入頁面，初始化滾動狀態: {self.is_scrolling}")
        
        # 重置排序為預設的降序
        self.sort_order = 'DESC'
        logger.debug(f"三星彩查詢結果重置排序為預設降序: {self.sort_order}")
        
        # 確保排序按鈕初始狀態為啟用並更新文字
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = False
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
            logger.debug(f"三星彩查詢結果初始化排序按鈕: {self.ids.sort_btn.text}")
        
        # 保存查詢參數
        self.query_params = selected_numbers.copy()
        self.user_numbers = selected_numbers.copy()
        
        # 清空列表並重置滾動位置
        if hasattr(self.ids, 'results_layout'):
            self.ids.results_layout.clear_widgets()
        
        # 執行完整查詢並初始化分頁
        self._perform_full_query_with_pagination()
        # 重置滾動位置到頂部（新查詢）
        self._reset_scroll_to_top()

    def _perform_full_query_with_pagination(self):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 1. 執行完整查詢（用於統計）
            self.all_results = self._perform_query()
            
            logger.debug(f"三星彩查詢結果完整查詢完成: 總筆數={len(self.all_results)}")
            
            # 2. 計算統計資料（基於完整資料）
            self.calculate_stats()
            
            # 3. 初始化分頁
            self._initialize_pagination()
            
            # 4. 更新UI（統計區塊）
            self.update_ui()
            
            # 5. 載入第一頁資料
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"三星彩查詢結果分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")

    def _perform_query(self):
        """執行實際查詢"""
        selected_numbers = self.query_params
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 構建查詢條件
        conditions = []
        if selected_numbers['hundreds'] is not None:
            conditions.append(f"num1 = {selected_numbers['hundreds']}")
        if selected_numbers['tens'] is not None:
            conditions.append(f"num2 = {selected_numbers['tens']}")
        if selected_numbers['units'] is not None:
            conditions.append(f"num3 = {selected_numbers['units']}")
        
        query = "SELECT issue, date, num1, num2, num3 FROM lotto_3star"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += f" ORDER BY date {self.sort_order}"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        # 轉換為統一格式
        results = []
        for row in rows:
            issue, date, n1, n2, n3 = row
            
            # 使用中獎判斷邏輯
            prize, abbreviated_prize = self.get_prize_info(selected_numbers, n1, n2, n3)
            
            results.append({
                '期別': issue,
                '開獎日期': date,
                '獎號': [n1, n2, n3],
                '獎別全名': prize,
                '獎別簡稱': abbreviated_prize,
                'raw_data': row
            })
        
        return results

    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > 0
        
        logger.debug(f"三星彩查詢結果分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"三星彩查詢結果第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self._update_result_list()  # 顯示無資料

    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {'頭獎': 0, '貳獎': 0, '參獎': 0}
        
        # 遍歷所有結果記錄
        for record in self.all_results:
            award = record.get('獎別全名', '')
            if award and award in stats:
                stats[award] += 1

        # 更新統計數據
        self.stats = stats

        # 打印調試信息
        logger.debug("三星彩查詢結果獎別統計結果:")
        for award, count in stats.items():
            logger.debug(f"{award}: {count}")

    def update_ui(self):
        """更新界面顯示（統計區塊和用戶選號）"""
        try:
            # 清除舊組件
            self.ids.selected_nums_layout.clear_widgets()

            # 更新總筆數顯示（基於完整資料）
            self.ids.total_count_label.text = str(len(self.all_results))

            # 更新各獎別統計
            prize_map = {
                '頭獎': 'prize_count_head',
                '貳獎': 'prize_count_second',
                '參獎': 'prize_count_third'
            }
            
            for prize_full, prize_id in prize_map.items():
                if hasattr(self.ids, prize_id):
                    getattr(self.ids, prize_id).text = str(self.stats.get(prize_full, 0))

            # 顯示選中的號碼
            selected_numbers = self.query_params
            positions = ['hundreds', 'tens', 'units']
            for position in positions:
                if selected_numbers[position] is not None:
                    ball = ResultBall(number=selected_numbers[position], selected=True, area=1, lotto_type='lotto3star')
                    self.ids.selected_nums_layout.add_widget(ball)
                else:
                    # 顯示空白球表示未選
                    ball = ResultBall(number=0, selected=False, area=1, lotto_type='lotto3star')
                    # 等待球組件完全初始化後再設置文字
                    Clock.schedule_once(lambda dt, b=ball: setattr(b.children[0].children[0], 'text', '-'), 0)
                    self.ids.selected_nums_layout.add_widget(ball)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"三星彩查詢結果UI更新錯誤: {str(e)}")

    def _update_result_list(self):
        """更新結果列表（分頁版本）"""
        try:
            # 清除結果列表
            self.ids.results_layout.clear_widgets()
            
            # 如果沒有結果，顯示提示
            if not self.displayed_results:
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
                return

            # 顯示當前已載入的所有資料
            for record in self.displayed_results:
                item_widget = self._create_result_item(record)
                self.ids.results_layout.add_widget(item_widget)
            
            # 添加載入更多指示器（無論是否還有更多資料）
            self._add_load_more_indicator()

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"三星彩查詢結果列表更新錯誤: {str(e)}")

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
            cols=3,
            spacing=dp(5)
        )
        
        selected_numbers = self.query_params
        winning_nums = record['獎號']
        for i, num in enumerate(winning_nums):
            position = ['hundreds', 'tens', 'units'][i]
            is_selected = selected_numbers[position] == num if selected_numbers[position] is not None else False
            ball = ResultBall(number=num, selected=is_selected, area=1, lotto_type='lotto3star')
            winning_nums_layout.add_widget(ball)
        
        numbers_row.add_widget(winning_nums_layout)
        
        # 獎別標籤
        prize_label = Label(
            text=record['獎別簡稱'],
            font_name='ChineseFont',
            font_size=dp(18),
            color=(1, 0, 0, 1) if record['獎別全名'] != '未中獎' else (0.5, 0.5, 0.5, 1),
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
            logger.debug(f"三星彩查詢結果跳過載入下一頁: is_loading_more={self.is_loading_more}, has_more_data={self.has_more_data}")
            return
        
        logger.debug(f"三星彩查詢結果開始載入下一頁: 當前已顯示={len(self.displayed_results)}, 總筆數={len(self.all_results)}")
        
        self.is_loading_more = True
        
        # 顯示載入提示
        self._show_loading_indicator()
        
        # 延遲載入，避免UI阻塞
        Clock.schedule_once(lambda dt: self._perform_load_next_page(), 0.2)

    def _perform_load_next_page(self):
        """實際執行下一頁載入"""
        try:
            # 保存當前滾動位置
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                current_content_height = self.ids.results_layout.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                logger.debug(f"三星彩查詢結果載入前滾動位置: {current_absolute_scroll:.0f}px")
            else:
                current_absolute_scroll = 0
            
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
                for record in next_page_data:
                    item_widget = self._create_result_item(record)
                    self.ids.results_layout.add_widget(item_widget)
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_results)
                
                # 重新添加載入指示器（無論是否還有更多資料）
                self._add_load_more_indicator()
                
                # 恢復滾動位置（延遲執行確保UI更新完成）
                Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
                
                logger.debug(f"三星彩查詢結果載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                # 當沒有更多資料時，也要更新指示器
                if hasattr(self, 'load_more_label'):
                    self.load_more_label.text = "已顯示全部資料"
                    self.load_more_label.opacity = 0.5
                
        except Exception as e:
            logger.exception(f"三星彩查詢結果載入下一頁錯誤: {str(e)}")
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
                
                logger.debug(f"三星彩查詢結果載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
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
            logger.exception(f"三星彩查詢結果追加結果錯誤: {str(e)}")

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
                logger.debug(f"三星彩查詢結果載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"三星彩查詢結果恢復滾動位置錯誤: {str(e)}")

    def _set_scrolling_state(self, is_scrolling):
        """設定滾動狀態並更新按鈕"""
        self.is_scrolling = is_scrolling
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = is_scrolling
            logger.debug(f"三星彩查詢結果排序按鈕禁用狀態: {self.ids.sort_btn.disabled}")
        else:
            logger.debug("三星彩查詢結果找不到sort_btn")
        logger.debug(f"三星彩查詢結果設定滾動狀態: {is_scrolling}, 按鈕禁用: {is_scrolling}")

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
                
                logger.debug("三星彩查詢結果使用動畫重置到頂部")
        except Exception as e:
            logger.exception(f"三星彩查詢結果簡單重置錯誤: {str(e)}")

    def _disable_scroll_events(self):
        """暫時禁用滾動事件檢測"""
        self._scroll_events_disabled = True
        logger.debug("三星彩查詢結果暫時禁用滾動事件")

    def _enable_scroll_events(self):
        """重新啟用滾動事件檢測並確保排序按鈕可用"""
        self._scroll_events_disabled = False
        # 確保排序按鈕恢復可用狀態
        Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 0.1)
        logger.debug("三星彩查詢結果重新啟用滾動事件")

    def _ensure_sort_button_enabled(self):
        """確保排序按鈕處於可用狀態"""
        self.is_scrolling = False
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = False
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
            logger.debug(f"三星彩查詢結果排序按鈕已啟用: {not self.ids.sort_btn.disabled}")
        else:
            logger.debug("三星彩查詢結果找不到sort_btn，無法啟用")
        logger.debug("三星彩查詢結果確保排序按鈕可用")



    def _old_show_results(self, selected_numbers):
        """保留舊版本的show_results方法以保持向後相容"""
        self.ids.results_layout.clear_widgets()
        self.ids.selected_nums_layout.clear_widgets()

        # 顯示選中的號碼
        positions = ['hundreds', 'tens', 'units']
        for position in positions:
            if selected_numbers[position] is not None:
                ball = Lotto3StarResultBall(number=selected_numbers[position], selected=True)
                self.ids.selected_nums_layout.add_widget(ball)
            else:
                # 顯示空白球表示未選
                ball = Lotto3StarResultBall(number=0, selected=False)
                # 等待球組件完全初始化後再設置文字
                Clock.schedule_once(lambda dt, b=ball: setattr(b.children[0].children[0], 'text', '-'), 0)
                self.ids.selected_nums_layout.add_widget(ball)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 構建查詢條件
        conditions = []
        if selected_numbers['hundreds'] is not None:
            conditions.append(f"num1 = {selected_numbers['hundreds']}")
        if selected_numbers['tens'] is not None:
            conditions.append(f"num2 = {selected_numbers['tens']}")
        if selected_numbers['units'] is not None:
            conditions.append(f"num3 = {selected_numbers['units']}")
        
        query = "SELECT issue, date, num1, num2, num3 FROM lotto_3star"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += f" ORDER BY date {self.sort_order}"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third'
        }
        
        # Reset all prize counts to 0 before updating
        for prize_id in prize_map.values():
            if prize_id in self.ids:
                self.ids[prize_id].text = '0'

        if not rows:
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

        prize_counts = Counter()

        # 更新结果列表 - 參照今彩539的結果行格式
        for row in rows:
            issue, date, n1, n2, n3 = row
            
            # 使用新的中獎判斷邏輯
            prize, abbreviated_prize = self.get_prize_info(selected_numbers, n1, n2, n3)

            if prize != '未中獎':
                prize_counts[prize] += 1

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
                text=f"期別: {issue}",
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
                text=f"開獎日期: {date}",
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
                cols=3,
                spacing=dp(5)
            )
            
            winning_nums = [n1, n2, n3]
            for i, num in enumerate(winning_nums):
                position = ['hundreds', 'tens', 'units'][i]
                is_selected = selected_numbers[position] == num if selected_numbers[position] is not None else False
                ball = Lotto3StarResultBall(number=num, selected=is_selected)
                winning_nums_layout.add_widget(ball)
            
            numbers_row.add_widget(winning_nums_layout)
            
            # 獎別標籤
            prize_label = Label(
                text=abbreviated_prize,
                font_name='ChineseFont',
                font_size=dp(18),
                color=(1, 0, 0, 1) if prize != '未中獎' else (0.5, 0.5, 0.5, 1),
                size_hint_x=None,
                width=dp(40),
                halign='center',
                valign='middle'
            )
            numbers_row.add_widget(prize_label)
            
            result_row.add_widget(numbers_row)
            self.ids.results_layout.add_widget(result_row)

        self.ids.total_count_label.text = str(len(rows))
            
        for prize, count in prize_counts.items():
            if prize in prize_map:
                if prize_map[prize] in self.ids:
                    self.ids[prize_map[prize]].text = str(count)
    
    def _set_ball_text(self, ball, text):
        """安全地設置球組件的文字"""
        if hasattr(ball, 'set_text'):
            ball.set_text(text)
        elif hasattr(ball, 'label') and ball.label:
            ball.label.text = text
        elif ball.children and len(ball.children) > 0:
            ball.children[0].text = text




class Lotto3StarRepeatedNumbersScreen(BaseAdvancedResultScreen):
    """三星彩重複三碼查詢"""
    duplicates = ListProperty([])
    
    repeated_numbers = ListProperty([])       # 重複的號碼
    
    # 實現基類抽象屬性
    @property
    def table_name(self):
        return 'lotto_3star'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3']
    
    @property
    def special_column(self):
        return None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enable_sort = False
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto_history.db')

    def on_pre_enter(self):
        """進入頁面時的處理"""
        super().on_pre_enter()
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug("三星彩重複三碼頁面進入，開始查詢")
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='查詢重複三碼中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_duplicate_query(), 0.1)
    
    def _perform_duplicate_query(self):
        """實際執行重複查詢的方法"""
        try:
            self.find_duplicates()
            # 填充列表並重置滾動位置
            self.populate_duplicate_list()
            logger.debug("三星彩重複三碼查詢完成，已重置滾動位置")
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
        except Exception as e:
            error_msg = f"查詢重複三碼失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            self.show_popup("錯誤", error_msg)
            traceback.print_exc()

    def find_duplicates(self):
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
                num1, num2, num3,
                COUNT(*) as count,
                GROUP_CONCAT(issue, ', ') as issues
            FROM lotto_3star
            GROUP BY num1, num2, num3
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            ''')

            for row in cursor.fetchall():
                self.duplicates.append({
                    'numbers': [row[0], row[1], row[2]],
                    'count': row[3],
                    'issues': row[4]
                })

            conn.close()
        except Exception as e:
            logger.exception(f"重複查詢錯誤: {str(e)}")
            traceback.print_exc()
    
    def populate_duplicate_list(self):
        """填充重複號碼列表（分頁版本）"""
        try:
            logger.debug(f"三星彩重複三碼列表開始填充: 總筆數={len(self.duplicates)}")
            
            # 保存重複號碼資料
            self.all_results = self.duplicates
            
            # 更新總筆數顯示
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = f'總筆數: {len(self.duplicates)}'
                logger.debug(f"三星彩重複三碼更新總筆數顯示: {len(self.duplicates)}")
            
            # 確保滾動狀態正確初始化
            self.is_scrolling = False
            self._scroll_events_disabled = False
            
            # 清空結果列表
            self.ids.results_layout.clear_widgets()
            
            # 初始化分頁並載入第一頁
            self._initialize_pagination()
            self._load_first_page()
            
            # 重置滾動位置到頂部
            self._reset_scroll_to_top()
            logger.debug("三星彩重複三碼重置滾動位置")
            
        except Exception as e:
            logger.exception(f"三星彩重複三碼列表填充錯誤: {str(e)}")
            traceback.print_exc()

    def _create_duplicate_item(self, item):
        """創建重複號碼項目的UI組件"""
        try:
            # 調試：打印項目結構
            logger.debug(f"創建重複項目，item結構: {item}")
            logger.debug(f"item的keys: {item.keys() if isinstance(item, dict) else 'not a dict'}")
            
            box = ClickableBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(50),
                spacing=dp(5),
                padding=(dp(10), dp(5)))

            # 檢查不同可能的鍵名
            numbers = None
            count = 0
            
            if 'numbers' in item:
                numbers = item['numbers']
                count = item.get('count', 0)
            elif 'combination' in item:
                numbers = item['combination']
                count = item.get('count', 0)
            elif isinstance(item, (list, tuple)) and len(item) >= 4:
                # 如果是列表格式：[num1, num2, num3, count]
                numbers = item[:3]
                count = item[3]
            else:
                # 嘗試其他可能的鍵名
                for key in item.keys():
                    if isinstance(item[key], (list, tuple)) and len(item[key]) == 3:
                        numbers = item[key]
                        break
                
                if numbers is None:
                    logger.warning(f"無法找到號碼資料，item: {item}")
                    return BoxLayout()  # 返回空的佈局
            
            logger.debug(f"解析出的號碼: {numbers}, 次數: {count}")

            for num in numbers:
                ball = ResultBall(
                    number=num, 
                    selected=False,  # 顯示黃色
                    area=1,
                    lotto_type='lotto3star',
                    size_hint=(None, None),
                    size=(dp(30), dp(30)))
                box.add_widget(ball)
            
            count_label = Label(
                text=f"({count}次)",
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
            
        except Exception as e:
            logger.exception(f"創建重複項目錯誤: {str(e)}")
            logger.debug(f"錯誤項目: {item}")
            traceback.print_exc()
            return ClickableBoxLayout()  # 返回空的佈局

    def _handle_duplicate_item_click(self, instance, item):
        """處理重複項目點擊事件"""
        logger.debug(f"點擊重複項目: {item}")
        
        # 獲取號碼
        numbers = None
        if 'numbers' in item:
            numbers = item['numbers']
        elif 'combination' in item:
            numbers = item['combination']
        
        if numbers:
            logger.debug(f"跳轉到詳情頁面，號碼: {numbers}")
            self.show_duplicate_details(numbers)
        else:
            logger.warning(f"無法獲取號碼資料: {item}")

    def show_duplicate_details(self, numbers):
        """顯示重複三碼詳情"""
        try:
            logger.debug(f"三星彩重複三碼詳情查詢開始: {numbers}")
            
            # 保存當前分頁狀態（不保存滾動位置）
            self._save_pagination_state()
            
            # 查詢重複號碼的詳細記錄
            details = self.query_repeated_numbers(numbers)
            
            # 獲取詳情頁面並設定資料
            detail_screen = self.manager.get_screen('lotto3star_duplicate_detail')
            detail_screen.details = details
            
            # 跳轉到詳情頁面
            self.manager.current = 'lotto3star_duplicate_detail'
            
        except Exception as e:
            logger.exception(f"三星彩重複三碼詳情查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")

    def show_results(self, repeated_numbers):
        """顯示重複三碼查詢結果（分頁版本）"""
        try:
            logger.debug(f"三星彩重複三碼查詢開始: {repeated_numbers}")
            
            # 保存重複號碼
            self.repeated_numbers = repeated_numbers
            
            # 確保滾動狀態正確初始化
            self.is_scrolling = False
            self._scroll_events_disabled = False
            
            # 清空結果列表
            if hasattr(self.ids, 'results_layout'):
                self.ids.results_layout.clear_widgets()
            
            # 執行完整查詢並初始化分頁
            self._perform_full_query_with_pagination()
            
        except Exception as e:
            logger.exception(f"三星彩重複三碼查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")

    def query_repeated_numbers(self, repeated_numbers):
        """查詢重複三碼的詳細記錄"""
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
        details = []

        if not os.path.exists(db_path):
            return details

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            query = '''
            SELECT 
                issue, date, num1, num2, num3
            FROM lotto_3star
            WHERE num1 = ? AND num2 = ? AND num3 = ?
            ORDER BY date DESC
            '''

            cursor.execute(query, tuple(repeated_numbers))

            for row in cursor.fetchall():
                details.append({
                    '期別': row[0],
                    '開獎日期': row[1],
                    '獎號': [row[2], row[3], row[4]]
                })

            conn.close()
        except Exception as e:
            logger.exception(f"詳細記錄查詢錯誤: {str(e)}")
            traceback.print_exc()

        return details

    def _perform_full_query_with_pagination(self):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 1. 執行完整查詢
            self.all_results = self.query_repeated_numbers(self.repeated_numbers)
            
            logger.debug(f"三星彩重複三碼完整查詢完成: 總筆數={len(self.all_results)}")
            
            # 2. 初始化分頁
            self._initialize_pagination()
            
            # 3. 載入第一頁資料
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"三星彩重複三碼分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > 0
        
        logger.debug(f"三星彩重複三碼分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"三星彩重複三碼第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆，has_more_data={self.has_more_data}")
            
            # 更新結果列表（包含載入指示器）
            self._update_result_list()
        else:
            self.has_more_data = False
            self._update_result_list()  # 顯示無資料

    def _update_result_list(self):
        """更新結果列表顯示 - 實現基類抽象方法"""
        try:
            if hasattr(self.ids, 'results_layout'):
                self.ids.results_layout.clear_widgets()
            
            if not self.displayed_results:
                if hasattr(self.ids, 'results_layout'):
                    self.ids.results_layout.height = dp(100)
                no_data_label = Label(
                    text='沒有重複的三碼組合',
                    font_name='ChineseFont',
                    font_size=dp(18),
                    color=get_color_from_hex('#FF0000'),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(100)
                )
                if hasattr(self.ids, 'results_layout'):
                    self.ids.results_layout.add_widget(no_data_label)
                return


            # 一次性同步加載所有顯示的項目
            for i, item in enumerate(self.displayed_results):
                item_widget = self._create_duplicate_item(item)
                if hasattr(self.ids, 'results_layout'):
                    self.ids.results_layout.add_widget(item_widget)

            
            # 添加載入指示器
            self._add_load_more_indicator()
            logger.debug(f"三星彩重複三碼同步更新完成: 共{num_items}筆")
            
        except Exception as e:
            traceback.print_exc()
            logger.exception(f"三星彩重複三碼結果列表更新錯誤: {str(e)}")

    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            if self.manager.current != self.name:
                return
                
            scroll_view = self.ids.scroll_view
            content_height_before = self.ids.results_layout.height
            viewport_height = scroll_view.height
            current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, content_height_before - viewport_height)
            
            self._remove_load_more_indicator()


            # 同步追加所有新記錄
            for item in new_records:
                item_widget = self._create_duplicate_item(item)
                if hasattr(self.ids, 'results_layout'):
                    self.ids.results_layout.add_widget(item_widget)

            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            logger.debug(f"三星彩重複三碼同步追加記錄完成，共追加 {len(new_records)} 筆")
            
        except Exception as e:
            logger.exception(f"三星彩重複三碼追加記錄錯誤: {str(e)}")

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'results_layout'):
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
        self.ids.results_layout.add_widget(load_more_box)
        
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label

    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'results_layout') and self.load_more_indicator in self.ids.results_layout.children:
            self.ids.results_layout.remove_widget(self.load_more_indicator)

    def _save_pagination_state(self):
        try:
            self.saved_current_page = self.current_page
            self.saved_displayed_results = self.displayed_results.copy()
        except Exception as e:
            logger.exception(f"保存分頁狀態錯誤: {e}")

    def _restore_pagination_state(self):
        try:
            self.all_results = self.duplicates
            self.displayed_results = self.saved_displayed_results.copy()
            self.current_page = self.saved_current_page
            self.has_more_data = len(self.displayed_results) < len(self.all_results)
            
            self.is_scrolling = False
            self._scroll_events_disabled = False
            
            self._update_result_list()
        except Exception as e:
            logger.exception(f"恢復分頁狀態錯誤: {e}")
            Clock.schedule_once(lambda dt: self.populate_duplicate_list(reset_scroll=False), 0.1)

    def _batch_update_result_list(self):
        self._update_result_list()

    def back_to_query(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_back_to_query)

    def _real_back_to_query(self):
        self.manager.current = 'lotto3star'

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title_label = Label(text=title, font_name='ChineseFont', font_size=dp(16), bold=True, color=(1, 0, 0, 1))
        content.add_widget(title_label)
        message_label = Label(text=message, font_name='ChineseFont', font_size=dp(14))
        content.add_widget(message_label)
        btn = Button(text="確定", size_hint_y=None, height=40, font_name='ChineseFont')
        popup = Popup(title='', content=content, size_hint=(0.7, 0.3), separator_height=0)
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

class Lotto3StarDuplicateDetailScreen(Screen, BaseScrollMixin):
    """三星彩重複記錄詳情"""
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
    all_results = ListProperty([])  # 完整查詢結果
    displayed_results = ListProperty([])  # 當前顯示的結果
    current_page = NumericProperty(0)     # 當前頁數
    page_size = NumericProperty(30)       # 每頁顯示數量
    is_loading_more = BooleanProperty(False)  # 是否正在載入更多
    has_more_data = BooleanProperty(True)     # 是否還有更多資料
    is_scrolling = BooleanProperty(False)     # 是否正在滾動
    
    def on_pre_enter(self):
        """進入頁面時初始化分頁並載入第一頁"""
        logger.debug(f"三星彩重複記錄詳情進入頁面，詳情筆數: {len(self.details)}")
        
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        
        # 清空結果列表，避免重複顯示
        if hasattr(self.ids, 'detail_list'):
            self.ids.detail_list.clear_widgets()
            logger.debug("三星彩重複三碼慣性檢查超時，強制結束")
        
        # 保存詳情資料並初始化分頁
        self.all_results = self.details
        self._initialize_pagination()
        self._load_first_page()
        
        # 重置滾動位置到頂部（新查詢）
        self._reset_scroll_to_top()

    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > 0
        
        logger.debug(f"三星彩重複記錄詳情分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"三星彩重複三碼第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆，has_more_data={self.has_more_data}")
            
            # 填充詳情列表（包含載入指示器）
            self.populate_detail_list()
        else:
            self.has_more_data = False
            self.populate_detail_list()  # 顯示無資料
    
    def populate_detail_list(self):
        """填充詳情列表（分頁版本）"""
        detail_list = self.ids.detail_list
        detail_list.clear_widgets()
        
        if not self.displayed_results:
            detail_list.add_widget(Label(
                text="沒有詳細記錄",
                font_name='ChineseFont',
                font_size=dp(18),
                color=get_color_from_hex('#FF0000'),
                halign='center'
            ))
            return
        
        # 顯示當前已載入的所有詳情記錄
        for record in self.displayed_results:
            box = self._create_detail_item(record)
            detail_list.add_widget(box)
        
        # 添加載入更多指示器（無論是否還有更多資料）
        self._add_load_more_indicator()

    def _create_detail_item(self, record):
        """創建單個詳情項目的UI組件"""
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
        
        for num in record['獎號']:
            ball = ResultBall(number=num, selected=False, area=1, lotto_type='lotto3star')
            row2.add_widget(ball)
        
        # 添加空白區域保持對齊
        row2.add_widget(Widget())
        
        box.add_widget(row2)
        
        return box

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'detail_list'):
            logger.warning("三星彩重複記錄詳情找不到detail_list，無法添加載入指示器")
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
            logger.debug(f"三星彩重複記錄詳情添加載入指示器: {text}")
        else:
            text = "已顯示全部資料"
            opacity = 0.5
            logger.debug(f"三星彩重複記錄詳情添加載入指示器: {text}")
        
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

    def _load_next_page(self):
        """載入下一頁資料"""
        if self.is_loading_more or not self.has_more_data:
            logger.debug(f"三星彩重複記錄詳情跳過載入下一頁: is_loading_more={self.is_loading_more}, has_more_data={self.has_more_data}")
            return
        
        logger.debug(f"三星彩重複記錄詳情開始載入下一頁: 當前已顯示={len(self.displayed_results)}, 總筆數={len(self.all_results)}")
        
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
            
            logger.debug(f"三星彩重複記錄詳情載入檢查: start_index={start_index}, end_index={end_index}, total={len(self.all_results)}")
            
            if start_index < len(self.all_results):
                # 添加下一頁資料
                next_page_data = self.all_results[start_index:end_index]
                self.displayed_results.extend(next_page_data)
                self.current_page += 1
                
                # 移除舊的載入指示器
                self._remove_load_more_indicator()
                
                # 添加新記錄
                for record in next_page_data:
                    item_widget = self._create_detail_item(record)
                    self.ids.detail_list.add_widget(item_widget)
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_results)
                logger.debug(f"三星彩重複記錄詳情載入後狀態: has_more_data={self.has_more_data}")
                
                # 重新添加載入指示器（無論是否還有更多資料）
                self._add_load_more_indicator()
                
                logger.debug(f"三星彩重複三碼載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                logger.debug("三星彩重複記錄詳情沒有更多資料可載入")
                self.has_more_data = False
                # 當沒有更多資料時，也要更新指示器
                if hasattr(self, 'load_more_label'):
                    self.load_more_label.text = "已顯示全部資料"
                    self.load_more_label.opacity = 0.5
                    logger.debug("三星彩重複記錄詳情指示器已更新為：已顯示全部資料")
                
        except Exception as e:
            logger.exception(f"三星彩重複記錄詳情載入下一頁錯誤: {str(e)}")
            traceback.print_exc()
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

    def back_to_duplicate(self):
        # 返回重複三碼查詢頁面（會自動重新查詢並置頂）
        logger.debug("三星彩重複記錄詳情返回重複三碼查詢頁面")
        
        self.manager.current = 'lotto3star_repeated_numbers'


class Lotto3StarWinningDetailsScreen(Screen, BaseScrollMixin):
    """三星彩自選號中獎詳情"""
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
        logger.debug(f"三星彩中獎詳情進入頁面，初始化滾動狀態: {self.is_scrolling}, 滾動事件啟用: {not self._scroll_events_disabled}")
        
        # 清空結果列表，避免重複顯示
        if hasattr(self.ids, 'results_layout'):
            self.ids.results_layout.clear_widgets()
            logger.debug("三星彩重複三碼滾動事件被禁用，忽略滾動開始")
        
        # 延遲檢查排序按鈕是否存在
        Clock.schedule_once(lambda dt: self._check_sort_button(), 0.5)
        
        # 設定查詢參數並執行分頁查詢
        self.query_params = {'numbers': self.user_numbers}
        self._perform_full_query_with_pagination()
        # 重置滾動位置到頂部（新查詢）
        self._reset_scroll_to_top()

    def _check_sort_button(self):
        """檢查排序按鈕是否存在"""
        if hasattr(self.ids, 'sort_btn'):
            logger.debug(f"三星彩中獎詳情找到排序按鈕: {self.ids.sort_btn}")
            logger.debug(f"排序按鈕當前狀態: disabled={self.ids.sort_btn.disabled}")
        else:
            logger.warning("三星彩中獎詳情沒有找到排序按鈕 sort_btn")
            logger.debug(f"可用的ids: {list(self.ids.keys()) if hasattr(self, 'ids') else 'No ids'}")

    def toggle_sort_order(self):
        """切換排序方式並重新查詢"""
        logger.debug(f"=== 三星彩中獎詳情排序按鈕被點擊！===")
        logger.debug(f"當前排序: {self.sort_order}")
        
        # 檢查排序按鈕狀態
        if hasattr(self.ids, 'sort_btn'):
            logger.debug(f"排序按鈕存在，disabled={self.ids.sort_btn.disabled}")
            logger.debug(f"排序按鈕文字: {self.ids.sort_btn.text}")
        else:
            logger.debug("排序按鈕不存在！")
            return
        
        # 檢查排序按鈕是否被禁用
        if self.ids.sort_btn.disabled:
            logger.debug("三星彩中獎詳情清空結果列表")
            logger.debug(f"當前滾動狀態: is_scrolling={self.is_scrolling}")
            return
        
        # 檢查是否有資料可以排序
        if not hasattr(self, 'all_results') or not self.all_results:
            logger.warning("三星彩中獎詳情找不到排序按鈕")
            logger.debug(f"all_results存在: {hasattr(self, 'all_results')}")
            if hasattr(self, 'all_results'):
                logger.debug(f"all_results長度: {len(self.all_results)}")
            return
        
        logger.debug(f"三星彩查詢結果數量: {len(self.all_results)}")
        
        # 立即禁用排序按鈕，避免重複點擊
        self.ids.sort_btn.disabled = True
        logger.debug("排序按鈕已禁用")
        
        # 暫時禁用滾動事件，避免排序過程中觸發滾動檢測
        self._disable_scroll_events()
        logger.debug("滾動事件已禁用")
        
        # 顯示載入中彈窗
        loading_popup = LoadingPopup(title='排序中')
        loading_popup.open()
        logger.debug("載入彈窗已顯示")
    
        # 使用 Clock.schedule_once 延遲執行，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_sort(loading_popup), 0.1)
        logger.debug("排序任務已排程")

    def _perform_sort(self, loading_popup):
        """實際執行排序的方法（分頁版本）"""
        try:
            logger.debug(f"三星彩中獎詳情執行排序前: sort_order={self.sort_order}, 資料筆數={len(self.all_results)}")
            
            # 切換排序方式
            old_sort_order = self.sort_order
            self.sort_order = 'ASC' if self.sort_order == 'DESC' else 'DESC'
            
            logger.debug(f"三星彩中獎詳情排序方式切換: {old_sort_order} -> {self.sort_order}")
        
            # 重新排序完整資料
            reverse_order = (self.sort_order == 'DESC')
            try:
                self.all_results.sort(key=lambda x: datetime.strptime(x['開獎日期'], '%Y/%m/%d'), reverse=reverse_order)
                logger.debug(f"三星彩中獎詳情使用日期排序成功")
            except Exception as date_error:
                logger.exception(f"三星彩中獎詳情日期排序失敗: {date_error}")
                # 如果日期格式解析失敗，使用字串排序
                self.all_results.sort(key=lambda x: x['開獎日期'], reverse=reverse_order)
                logger.debug(f"三星彩中獎詳情使用字串排序")
            
            logger.debug(f"三星彩中獎詳情排序完成: sort_order={self.sort_order}, reverse={reverse_order}")
            self.results = self.all_results  # 保持向後相容
            
            # 重新初始化分頁
            self._initialize_pagination()
            self._load_first_page()
            
            logger.debug(f"三星彩中獎詳情分頁重新載入完成")
            
        except Exception as e:
            logger.exception(f"三星彩中獎詳情排序錯誤: {str(e)}")
            traceback.print_exc()
        finally:
            # 關閉載入彈窗
            loading_popup.dismiss()
            
            # 更新按鈕文字並重新啟用
            if hasattr(self.ids, 'sort_btn'):
                self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
                self.ids.sort_btn.disabled = False
                logger.debug(f"三星彩中獎詳情排序按鈕已重新啟用，文字更新為: {self.ids.sort_btn.text}")
            
            # 重新啟用滾動事件
            Clock.schedule_once(lambda dt: self._enable_scroll_events(), 0.1)
            Clock.schedule_once(lambda dt: self._simple_reset_scroll(), 0.5)

    def _perform_full_query_with_pagination(self):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 1. 執行完整查詢（用於統計）
            self.all_results = self.perform_winning_query()
            self.results = self.all_results  # 保持向後相容
            
            logger.debug(f"三星彩中獎詳情完整查詢完成: 總筆數={len(self.all_results)}")
            
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
            logger.exception(f"三星彩中獎詳情分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > 0
        
        logger.debug(f"三星彩中獎詳情分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"三星彩中獎詳情第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self._update_result_list()  # 顯示無資料

    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {'頭獎': 0, '貳獎': 0, '參獎': 0}
        
        # 遍歷所有結果記錄，使用all_results確保統計完整資料
        for record in self.all_results:
            award = record.get('獎別全名', '')
            if award and award in stats:
                stats[award] += 1

        # 更新統計數據
        self.stats = stats

        # 打印調試信息
        logger.debug("三星彩中獎詳情獎別統計結果:")
        for award, count in stats.items():
            logger.debug(f"{award}: {count}")

    def update_ui(self):
        """更新界面顯示（統計區塊和用戶選號）"""
        try:
            # 清除舊組件
            self.ids.selected_nums_layout.clear_widgets()

            # 更新總筆數顯示（基於完整資料）
            self.ids.total_count_label.text = str(len(self.all_results))

            # 更新各獎別統計
            prize_map = {
                '頭獎': 'prize_count_head',
                '貳獎': 'prize_count_second',
                '參獎': 'prize_count_third'
            }
            
            for prize_full, prize_id in prize_map.items():
                if hasattr(self.ids, prize_id):
                    getattr(self.ids, prize_id).text = str(self.stats.get(prize_full, 0))

            # 顯示自選號碼
            positions = ['hundreds', 'tens', 'units']
            for position in positions:
                num = self.user_numbers.get(position)
                if num is not None:
                    ball = ResultBall(number=num, selected=True, area=1, lotto_type='lotto3star')
                    self.ids.selected_nums_layout.add_widget(ball)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"三星彩中獎詳情UI更新錯誤: {str(e)}")

    def _update_result_list(self):
        """更新結果列表（分頁版本）"""
        try:
            # 清除結果列表
            self.ids.results_layout.clear_widgets()
            
            # 如果沒有結果，顯示提示
            if not self.displayed_results:
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
                return

            # 顯示當前已載入的所有資料
            for record in self.displayed_results:
                item_widget = self._create_result_item(record)
                self.ids.results_layout.add_widget(item_widget)
            
            # 添加載入更多指示器（無論是否還有更多資料）
            self._add_load_more_indicator()

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"三星彩中獎詳情更新列表錯誤: {str(e)}")

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
            cols=3,
            spacing=dp(5)
        )
        
        for i, num in enumerate(record['獎號']):
            position = ['hundreds', 'tens', 'units'][i]
            user_num = self.user_numbers.get(position)
            is_selected = user_num == num if user_num is not None else False
            ball = ResultBall(number=num, selected=is_selected, area=1, lotto_type='lotto3star')
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

    def _load_next_page(self):
        """載入下一頁資料"""
        if self.is_loading_more or not self.has_more_data:
            logger.debug(f"三星彩中獎詳情跳過載入下一頁: is_loading_more={self.is_loading_more}, has_more_data={self.has_more_data}")
            return
        
        logger.debug(f"三星彩中獎詳情開始載入下一頁: 當前已顯示={len(self.displayed_results)}, 總筆數={len(self.all_results)}")
        
        self.is_loading_more = True
        
        # 顯示載入提示
        self._show_loading_indicator()
        
        # 延遲載入，避免UI阻塞
        Clock.schedule_once(lambda dt: self._perform_load_next_page(), 0.2)

    def _perform_load_next_page(self):
        """實際執行下一頁載入"""
        try:
            # 保存當前滾動位置
            if hasattr(self.ids, 'results_scroll'):
                scroll_view = self.ids.results_scroll
                current_content_height = self.ids.results_layout.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                logger.debug(f"三星彩中獎詳情載入前滾動位置: {current_absolute_scroll:.0f}px")
            else:
                current_absolute_scroll = 0
            
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
                for record in next_page_data:
                    item_widget = self._create_result_item(record)
                    self.ids.results_layout.add_widget(item_widget)
                
                # 檢查是否還有更多資料
                self.has_more_data = end_index < len(self.all_results)
                
                # 重新添加載入指示器（無論是否還有更多資料）
                self._add_load_more_indicator()
                
                # 恢復滾動位置（延遲執行確保UI更新完成）
                Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
                
                logger.debug(f"三星彩中獎詳情載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                # 當沒有更多資料時，也要更新指示器
                if hasattr(self, 'load_more_label'):
                    self.load_more_label.text = "已顯示全部資料"
                    self.load_more_label.opacity = 0.5
                
        except Exception as e:
            logger.exception(f"三星彩中獎詳情載入下一頁錯誤: {str(e)}")
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
        if hasattr(self, 'load_more_indicator') and hasattr(self.ids, 'results_layout') and self.load_more_indicator in self.ids.results_layout.children:
            self.ids.results_layout.remove_widget(self.load_more_indicator)

    def _set_scrolling_state(self, is_scrolling):
        """設定滾動狀態並更新按鈕"""
        self.is_scrolling = is_scrolling
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = is_scrolling
            logger.debug(f"三星彩中獎詳情排序按鈕禁用狀態: {self.ids.sort_btn.disabled}")
        else:
            logger.warning("三星彩中獎詳情找不到sort_btn")
        logger.debug(f"三星彩重複三碼設定滾動狀態: {is_scrolling}, 按鈕禁用: {is_scrolling}")

    def _simple_reset_scroll(self):
        """簡單有效的滾動重置方法"""
        try:
            if hasattr(self.ids, 'results_scroll'):
                scroll_view = self.ids.results_scroll
                
                # 停止所有動畫
                Animation.cancel_all(scroll_view)
                
                # 暫時禁用滾動事件檢測，避免重置時觸發滾動事件
                self._disable_scroll_events()
                
                # 使用Animation確保平滑重置
                anim = Animation(scroll_y=1.0, duration=0.3)
                anim.bind(on_complete=lambda *args: self._enable_scroll_events())
                anim.start(scroll_view)
                
                logger.debug("三星彩中獎詳情使用動畫重置到頂部")
        except Exception as e:
            logger.exception(f"三星彩中獎詳情簡單重置錯誤: {str(e)}")

    def _disable_scroll_events(self):
        """暫時禁用滾動事件檢測"""
        self._scroll_events_disabled = True
        logger.debug("三星彩中獎詳情暫時禁用滾動事件")

    def _enable_scroll_events(self):
        """重新啟用滾動事件檢測並確保排序按鈕可用"""
        self._scroll_events_disabled = False
        # 確保排序按鈕恢復可用狀態
        Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 0.1)
        logger.debug("三星彩中獎詳情重新啟用滾動事件")

    def _ensure_sort_button_enabled(self):
        """確保排序按鈕處於可用狀態"""
        self.is_scrolling = False
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = False
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "ASC" else "降序"}'
            logger.debug(f"三星彩中獎詳情排序按鈕已啟用: {not self.ids.sort_btn.disabled}")
        else:
            logger.warning("三星彩中獎詳情找不到sort_btn，無法啟用")
        logger.debug("三星彩中獎詳情確保排序按鈕可用")



    def show_results(self):
        self.ids.results_layout.clear_widgets()
        self.ids.selected_nums_layout.clear_widgets()

        # 顯示自選號碼
        positions = ['hundreds', 'tens', 'units']
        for position in positions:
            num = self.user_numbers.get(position)
            if num is not None:
                ball = Lotto3StarResultBall(number=num, selected=True)
                self.ids.selected_nums_layout.add_widget(ball)

        matched_records = self.perform_winning_query()

        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third'
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

        prize_counts = Counter(record['獎別全名'] for record in matched_records)

        for prize_full, count in prize_counts.items():
            if prize_full in prize_map and prize_map[prize_full] in self.ids:
                self.ids[prize_map[prize_full]].text = str(count)

        # 顯示結果 - 參照今彩539的結果行格式
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
                cols=3,
                spacing=dp(5)
            )
            
            for i, num in enumerate(row['獎號']):
                position = ['hundreds', 'tens', 'units'][i]
                user_num = self.user_numbers.get(position)
                is_selected = user_num == num if user_num is not None else False
                ball = Lotto3StarResultBall(number=num, selected=is_selected)
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

    def go_back(self):
        self.manager.current = 'lotto3star'

    def on_leave(self):
        super().on_leave()
        self.ids.results_layout.clear_widgets()
        self.ids.selected_nums_layout.clear_widgets()
        self.ids.total_count_label.text = '0'
        
        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third'
        }
        for prize_id in prize_map.values():
            if prize_id in self.ids:
                self.ids[prize_id].text = '0'

    def perform_winning_query(self):
        app = App.get_running_app()
        
        db_path = self.db_path
        if not os.path.exists(db_path):
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM lotto_3star')
            
            matched_records = []
            for row in cursor:
                hundreds_num = row['num1']
                tens_num = row['num2'] 
                units_num = row['num3']
                
                prize_full, prize_short = self._determine_winning_award(hundreds_num, tens_num, units_num)
                
                if prize_full:
                    matched_records.append({
                        '期別': row['issue'],
                        '開獎日期': row['date'],
                        '獎號': [hundreds_num, tens_num, units_num],
                        '獎別全名': prize_full,
                        '獎別簡稱': prize_short
                    })
            
            matched_records.sort(key=lambda x: datetime.strptime(x['開獎日期'], '%Y/%m/%d'), reverse=(self.sort_order == 'DESC'))
            
            conn.close()
            return matched_records
        except Exception as e:
            traceback.print_exc()
            return []

    def _determine_winning_award(self, hundreds_num, tens_num, units_num):
        """根據三星彩中獎規則判斷獎別"""
        user_hundreds = self.user_numbers.get('hundreds')
        user_tens = self.user_numbers.get('tens')
        user_units = self.user_numbers.get('units')
        
        # 檢查各位數是否有選擇且匹配
        hundreds_selected = user_hundreds is not None
        tens_selected = user_tens is not None
        units_selected = user_units is not None
        
        hundreds_match = hundreds_selected and user_hundreds == hundreds_num
        tens_match = tens_selected and user_tens == tens_num
        units_match = units_selected and user_units == units_num
        
        # 個位沒選或個位沒對中 = 未中獎
        if not units_selected or not units_match:
            return None, ''
        
        # 個位對中的情況下：
        # 頭獎：佰位、拾位、個位都選且都對中
        if hundreds_selected and tens_selected and hundreds_match and tens_match and units_match:
            return '頭獎', '頭'
        # 貳獎：拾位選且對中，個位對中（佰位可選可不選，選了可對可不對）
        elif tens_selected and tens_match and units_match:
            return '貳獎', '貳'
        # 參獎：個位對中（佰位、拾位可選可不選，選了可對可不對）
        elif units_match:
            return '參獎', '參'
        
        return None, ''




class Lotto3StarSavedScreen(BaseLotterySavedScreen):
    """三星彩自選號管理界面"""
    
    @property
    def lottery_type(self):
        return '3star'

    def on_pre_enter(self):
        """進入屏幕前的初始化"""
        self.is_scrolling = False
        self._scroll_events_disabled = False
        self.load_saved_numbers()
        self.populate_saved_list()
        logger.debug(f"三星彩自選號頁面進入，總筆數: {len(self.all_results)}")

    def use_saved_number(self, index):
        """使用選中的三星彩自選號（支援分頁索引轉換）"""
        actual_index = index
        if hasattr(self, 'displayed_results') and index < len(self.displayed_results):
            target_item = self.displayed_results[index]
            actual_index = next((i for i, item in enumerate(self.all_results) if item['id'] == target_item['id']), index)
        
        if 0 <= actual_index < len(self.all_results):
            saved = self.all_results[actual_index]
            query_screen = self.manager.get_screen('lotto3star')
            query_screen.clear_selection()
            
            if len(saved['numbers']) >= 3:
                for i, num in enumerate(saved['numbers'][:3]):
                    if hasattr(query_screen, 'set_position_number'):
                        query_screen.set_position_number(i, num)
            
            # 確保UI完全更新
            if hasattr(query_screen, 'apply_selected_numbers'):
                query_screen.apply_selected_numbers()
            
            self.manager.current = 'lotto3star'

