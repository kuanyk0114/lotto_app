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
import traceback
from datetime import datetime
from modules.common import LoadingPopup, BallButton, ResultBall, show_popup, DatabaseManager, BaseLotteryQueryScreen, BaseLotterySavedScreen, BaseAdvancedResultScreen, ClickableBoxLayout
import logging
logger = logging.getLogger(__name__)



class PowerLottoQueryScreen(BaseLotteryQueryScreen):
    """威力彩選號查詢界面"""
    selected_area1 = ListProperty([])  # 第一區選中號碼
    selected_area2 = ListProperty([])  # 第二區選中號碼
    _is_loading_selection = BooleanProperty(False)
    
    # 實作抽象屬性
    @property
    def lottery_type(self):
        return 'power'
    
    @property
    def table_name(self):
        return 'power_lotto'
    
    @property
    def max_numbers(self):
        return 6  # 第一區6個號碼
    
    def get_selected_numbers(self):
        # 威力彩需要特殊處理，返回第一區和第二區
        return {
            'area1': list(self.selected_area1),
            'area2': list(self.selected_area2)
        }
    
    def save_custom_numbers(self):
        """威力彩專用的自選號儲存方法 - 必須覆蓋父類方法"""
        logger.info(f"=== 威力彩專用方法開始儲存自選號 ===")
        logger.debug(f"第一區選號: {self.selected_area1}")
        logger.debug(f"第二區選號: {self.selected_area2}")
        
        # 驗證選號
        if not self.selected_area1:
            show_popup('提示', '第一區至少要選1個號碼才能儲存')
            return
        
        try:
            # 準備威力彩的插入參數
            area1_nums = list(self.selected_area1)
            area2_nums = list(self.selected_area2)
            
            # 威力彩需要填滿6個第一區位置，不足的用NULL
            while len(area1_nums) < 6:
                area1_nums.append(None)
            
            # 第二區號碼（威力彩的特別號）
            special_num = area2_nums[0] if area2_nums else None
            
            params = ['power'] + area1_nums + [special_num, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            
            query = """
                INSERT INTO custom_numbers (lottery_type, num1, num2, num3, num4, num5, num6, special_num, created_time) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            logger.debug(f"威力彩SQL查詢: {query}")
            logger.debug(f"威力彩插入參數: {params}")
            
            # 使用自選號資料庫
            result_id = self.db_manager.execute_custom_insert(query, params)
            logger.info(f"威力彩插入結果 ID: {result_id}")
            show_popup('成功', '威力彩自選號碼已儲存')
            
        except Exception as e:
            logger.exception(f"❌ 威力彩專用方法儲存錯誤: {str(e)}")
            show_popup('錯誤', f'威力彩儲存失敗: {e}')
    
    def validate_for_save(self):
        """威力彩儲存時的特殊驗證 - 需要第一區至少1個號碼"""
        if not self.selected_area1:
            return False, "第一區至少要選1個號碼才能儲存"
        return True, ""
    
    def validate_selection(self):
        """覆寫驗證邏輯 - 查詢時只需要第一區至少1個號碼"""
        if not self.selected_area1:
            return False, "第一區至少要選1個號碼"
        return True, ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.update_ui, 0.1)

    def on_pre_enter(self):
        """Called when the screen is about to be shown."""
        self.update_ui()
    
    def update_ui(self, dt=None):
        """(Re)draws the number selection grids based on current selections."""
        # Area 1 Grid (1-38)
        area1_grid = self.ids.area1_grid
        area1_grid.clear_widgets()
        for i in range(1, 39):
            btn = BallButton(text=str(i), area=1, lotto_type='powerlotto')
            btn.selected = i in self.selected_area1
            btn.bind(selected=self.on_ball_selected)
            area1_grid.add_widget(btn)

        # Area 2 Grid (1-8)
        area2_grid = self.ids.area2_grid
        area2_grid.clear_widgets()
        for i in range(1, 9):
            btn = BallButton(text=str(i), area=2, lotto_type='powerlotto')
            btn.selected = i in self.selected_area2
            btn.bind(selected=self.on_ball_selected)
            area2_grid.add_widget(btn)
    
    

    def on_ball_selected(self, instance, value):
        if self._is_loading_selection:
            return

        number = int(instance.text)
        if instance.area == 1:
            if value:
                if len(self.selected_area1) < 6:
                    if number not in self.selected_area1:
                        self.selected_area1.append(number)
                else:
                    instance.selected = False
                    show_popup('提示', '第一區最多只能選擇6個號碼')
            else:
                if number in self.selected_area1:
                    self.selected_area1.remove(number)
        else:  # area 2
            if value:
                if len(self.selected_area2) < 1:
                    if number not in self.selected_area2:
                        self.selected_area2.append(number)
                else:
                    instance.selected = False
                    show_popup('提示', '第二區最多只能選擇1個號碼')
            else:
                if number in self.selected_area2:
                    self.selected_area2.remove(number)

    def clear_selection(self):
        """清除所有選取"""
        # 清除第一區選取
        for btn in self.ids.area1_grid.children:
            if isinstance(btn, BallButton):
                btn.selected = False
        self.selected_area1.clear()
        
        # 清除第二區選取
        for btn in self.ids.area2_grid.children:
            if isinstance(btn, BallButton): 
                btn.selected = False
        self.selected_area2.clear()
    
    
    def save_selection(self):
        """保持向後相容的方法名"""
        self.save_custom_numbers()
    
    # show_saved_numbers 現在由基礎類別提供
    
    def query_history(self):
        """威力彩查詢歷史"""
        if not self.selected_area1:
            show_popup('提示', '第一區至少要選1個號碼')
            return
        
        logger.debug(f"威力彩查詢界面 - 第一區選號: {self.selected_area1}")
        logger.debug(f"威力彩查詢界面 - 第二區選號: {self.selected_area2}")
        
        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='威力彩查詢中')
        self.loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行查詢，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_query(), 0.1)

    def _perform_query(self):
        """實際執行查詢的方法"""
        try:
            results_screen = self.manager.get_screen('power_result')
            results_screen.show_results(self.selected_area1, self.selected_area2)
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
            # 切換到結果屏幕
            self.manager.current = 'power_result'
        except Exception as e:
            error_msg = f"查詢失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            show_popup("錯誤", error_msg)

    def check_duplicates(self):
        """查詢重複六碼"""
        self.manager.current = 'power_duplicate'

    def check_winning_details(self):
        """查詢自選號中獎詳情"""
        if len(self.selected_area1) != 6:
            show_popup("提示", "請選擇6個第一區號碼"+'\n'+"，或先提取自選號!!")
            return

        # 顯示載入中彈窗
        self.loading_popup = LoadingPopup(title='查詢中獎詳情')
        self.loading_popup.open()

        # 延遲執行查詢
        Clock.schedule_once(lambda dt: self._perform_winning_details_query(), 0.1)

    def _perform_winning_details_query(self):
        """執行自選號中獎詳情查詢"""
        try:
            query_params = {
                'area1': list(self.selected_area1),
                'area2': list(self.selected_area2) if self.selected_area2 else []
            }
            
            details_screen = self.manager.get_screen('power_winning_details')
            details_screen.query_params = query_params
            details_screen.sort_order = 'DESC'
            
            self.loading_popup.dismiss()
            self.manager.current = 'power_winning_details'
        except Exception as e:
            self.loading_popup.dismiss()
            show_popup("錯誤", f"無法開啟詳情頁面: {str(e)}")

    # query_history 現在由基礎類別提供
    
    def prepare_query_params(self):
        """準備查詢參數 - 威力彩特殊格式"""
        return {
            'area1': sorted(self.selected_area1),
            'area2': self.selected_area2[0] if self.selected_area2 else None
        }
    
    def validate_selection(self):
        """覆寫驗證邏輯 - 查詢時只需要第一區有號碼"""
        if not self.selected_area1:
            return False, "第一區至少要選1個號碼"
        return True, ""
    
    


class PowerLottoResultScreen(BaseAdvancedResultScreen):
    """威力彩查詢結果界面"""
    query_params = DictProperty({})
    results = ListProperty([])
    stats = DictProperty({})
    user_numbers = DictProperty({})  # 存儲用戶選擇的號碼
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'power_lotto'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    
    @property
    def special_column(self):
        return 'special_num'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保威力彩查詢結果頁面預設為降序排列
        self.sort_order = 'DESC'

    def get_prize_info(self, matched_nums, special_matched):
        """威力彩特有的獎別計算邏輯（雙區系統）"""
        if matched_nums == 6 and special_matched:
            return '頭獎', '頭'
        if matched_nums == 6 and not special_matched:
            return '貳獎', '貳'
        if matched_nums == 5 and special_matched:
            return '參獎', '參'
        if matched_nums == 5 and not special_matched:
            return '肆獎', '肆'
        if matched_nums == 4 and special_matched:
            return '伍獎', '伍'
        if matched_nums == 4 and not special_matched:
            return '陸獎', '陸'
        if matched_nums == 3 and special_matched:
            return '柒獎', '柒'
        if matched_nums == 3 and not special_matched:
            return '捌獎', '捌'
        if matched_nums == 2 and special_matched:
            return '玖獎', '玖'
        if special_matched and matched_nums < 2:
            return '普獎', '普'
        return '未中獎', ''
   
    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"威力彩進入頁面，初始化滾動狀態: {self.is_scrolling}, 滾動事件啟用: {not self._scroll_events_disabled}")
        
        # 重置排序為預設降序（除非子類有特殊設定）
        if not hasattr(self, '_sort_initialized'):
            self.sort_order = 'DESC'
            self._sort_initialized = True
        
        logger.debug(f"威力彩進入頁面，初始化滾動狀態: {self.is_scrolling}, 滾動事件啟用: {not self._scroll_events_disabled}")
        
        if self.query_params:
            self.user_numbers = {
                'area1': self.query_params['area1'],
                'area2': self.query_params['area2']
            }
            # 先檢查資料庫
            self.check_database()
            # 執行完整查詢並初始化分頁
            self._perform_full_query_with_pagination()
            # 重置滾動位置到頂部（新查詢）
            self._reset_scroll_to_top()
    
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
            logger.exception(f"分頁查詢錯誤: {str(e)}")
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > self.page_size
        
        logger.debug(f"分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self.has_more_data = False
            self._update_result_list()  # 顯示無資料
    
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
                
                logger.debug(f"載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
                # 如果還有更多資料，更新載入指示器狀態
                if self.has_more_data:
                    logger.debug("還有更多資料可載入")
                else:
                    logger.debug("已載入全部資料")
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"載入下一頁錯誤: {str(e)}")
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

    def perform_query(self):
        """使用 SQLite 查詢歷史記錄（嚴格符合三個條件）"""
        """最終優化版（已移除 _process_results 的獨立方法）"""
        app = App.get_running_app()
        area1_selected = self.user_numbers['area1']
        area2_selected = self.user_numbers['area2']
    
        db_path = app.resource_path('data/lotto_history.db')
        if not os.path.exists(db_path):
            self.show_popup("錯誤", "找不到資料庫文件")
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        
            # 動態生成查詢條件（智慧化處理單一/多號碼情況）
            query = f'''
            SELECT 
                issue as 期別,
                date as 開獎日期,
                num1, num2, num3, num4, num5, num6,
                special_num as 第二區
            FROM power_lotto
            WHERE {self._build_area1_condition(area1_selected)}
            {f"AND special_num = {area2_selected}" if area2_selected else ""}
            '''
        
            cursor = conn.execute(query)
            matched_records = []
            area1_set = set(area1_selected)  # 使用集合加速比對
        
            for row in cursor:
                winning_numbers = [row[f'num{i}'] for i in range(1, 7)]
                matched_count = len(area1_set & set(winning_numbers))
                special_match = area2_selected and (area2_selected == row['第二區'])

                # 將文字日期轉換為日期物件
                try:
                    date_obj = datetime.strptime(row['開獎日期'], '%Y/%m/%d').date()
                except ValueError:
                    # 如果日期格式錯誤，嘗試其他可能的格式
                    try:
                        date_obj = datetime.strptime(row['開獎日期'], '%Y-%m-%d').date()  # 嘗試橫線分隔
                    except ValueError:
                        date_obj = datetime.min.date()  # 如果都失敗，使用最小日期
                    logger.warning(f"警告: 無法解析日期格式: {row['開獎日期']}")

            
                matched_records.append({
                    '期別': row['期別'],
                    '開獎日期': row['開獎日期'],
                    '日期物件': date_obj,        # 新增日期物件用於排序
                    '獎號': winning_numbers,
                    '第二區': row['第二區'],
                    '獎別': self._determine_award(matched_count, special_match)
                })

            # 依日期物件排序
            reverse_order = (self.sort_order == 'DESC')
            matched_records.sort(key=lambda x: x['日期物件'], reverse=reverse_order)
            
            conn.close()
            return matched_records
        
        except Exception as e:
            logger.exception(f"SQL 查詢錯誤: {str(e)}")
            return []

    def _build_area1_condition(self, numbers):
        """構建第一區查詢條件（保持獨立因邏輯複雜）"""
        if not numbers:
            return "1=0"
        return " AND ".join(
            f"({num} IN (num1, num2, num3, num4, num5, num6))" 
            for num in numbers
        )


    def _determine_award(self, matched_count, special_match):
        """獎別判斷輔助方法"""
        if matched_count == 6:
            return '頭' if special_match else '貳'
        elif matched_count == 5:
            return '參' if special_match else '肆'
        elif matched_count == 4:
            return '伍' if special_match else '陸'
        elif matched_count == 3:
            return '柒' if special_match else '玖'
        elif matched_count == 2 and special_match:
            return '捌'
        elif matched_count == 1 and special_match:
            return '普'
        return ''

    def toggle_sort_order(self):
        """切換排序方式並重新查詢"""
        # 顯示載入中彈窗
        loading_popup = LoadingPopup(title='排序中')
        loading_popup.open()
    
        # 使用 Clock.schedule_once 延遲執行，確保UI更新
        Clock.schedule_once(lambda dt: self._perform_sort(loading_popup), 0.1)

    def _perform_sort(self, loading_popup):
        """實際執行排序的方法（分頁版本）"""
        try:
            # 切換排序方式
            self.sort_order = 'asc' if self.sort_order == 'DESC' else 'DESC'
        
            # 更新按鈕文字
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "asc" else "降序"}'
        
            # 重新排序完整資料
            reverse_order = (self.sort_order == 'DESC')
            self.all_results.sort(key=lambda x: x['日期物件'], reverse=reverse_order)
            logger.debug(f"威力彩排序: sort_order={self.sort_order}, reverse={reverse_order}")
            self.results = self.all_results  # 保持向後相容
            
            # 重新初始化分頁
            self._initialize_pagination()
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"排序錯誤: {str(e)}")
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
                self._disable_scroll_events()
                
                # 使用Animation確保平滑重置
                anim = Animation(scroll_y=1.0, duration=0.3)
                anim.bind(on_complete=lambda *args: self._enable_scroll_events())
                anim.start(scroll_view)
                
                logger.debug("威力彩使用動畫重置到頂部")
        except Exception as e:
            logger.exception(f"威力彩簡單重置錯誤: {str(e)}")
    
    def _disable_scroll_events(self):
        """暫時禁用滾動事件檢測"""
        self._scroll_events_disabled = True
        logger.debug("威力彩暫時禁用滾動事件")
    
    def _enable_scroll_events(self):
        """重新啟用滾動事件檢測並確保排序按鈕可用"""
        self._scroll_events_disabled = False
        # 確保排序按鈕恢復可用狀態
        Clock.schedule_once(lambda dt: self._ensure_sort_button_enabled(), 0.1)
        logger.debug("威力彩重新啟用滾動事件")
    
    def _ensure_sort_button_enabled(self):
        """確保排序按鈕處於可用狀態"""
        self.is_scrolling = False
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = False
            self.ids.sort_btn.text = f'排序: {"升序" if self.sort_order == "asc" else "降序"}'
        logger.debug("威力彩確保排序按鈕可用")
    
    def _ultimate_reset_scroll(self):
        """終極滾動重置方法"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                
                # 停止所有動畫
                Animation.cancel_all(scroll_view)
                
                # 強制重置到頂部
                scroll_view.scroll_y = 1.0
                
                # 如果ScrollView有update方法，調用它
                if hasattr(scroll_view, 'update_from_scroll'):
                    scroll_view.update_from_scroll()
                
                logger.debug(f"威力彩終極重置滾動位置: {scroll_view.scroll_y}")
        except Exception as e:
            logger.exception(f"威力彩終極重置錯誤: {str(e)}")
    
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
                logger.debug("威力彩滾動位置已重置到頂部")
        except Exception as e:
            logger.exception(f"威力彩重置滾動位置錯誤: {str(e)}")
    
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
                # 重置滾動相關屬性
                if hasattr(scroll_view, '_scroll_y_mouse'):
                    scroll_view._scroll_y_mouse = 1
                if hasattr(scroll_view, '_scroll_y_touch'):
                    scroll_view._scroll_y_touch = 1
                # 立即設定位置
                scroll_view.scroll_y = 1
                logger.debug("威力彩停止滾動動作並立即重置")
        except Exception as e:
            logger.exception(f"威力彩停止滾動錯誤: {str(e)}")
    
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
                
                # 如果有內部滾動屬性，也重置它們
                if hasattr(scroll_view, '_scroll_y_mouse'):
                    scroll_view._scroll_y_mouse = 1
                if hasattr(scroll_view, '_scroll_y_touch'):
                    scroll_view._scroll_y_touch = 1
                
                logger.debug(f"威力彩強制滾動位置: {scroll_view.scroll_y}")
        except Exception as e:
            logger.exception(f"威力彩強制滾動錯誤: {str(e)}")


    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {
            '頭': 0, '貳': 0, '參': 0, '肆': 0, '伍': 0,
            '陸': 0, '柒': 0, '捌': 0, '玖': 0, '普': 0
        }
        
        # 遍歷所有結果記錄
        for record in self.results:
            award = record.get('獎別', '')
            if award and award in stats:
                stats[award] += 1

        # 更新統計數據
        self.stats = stats

        # 打印調試信息
        logger.debug("獎別統計結果:")
        for award, count in stats.items():
            logger.debug(f"{award}: {count}")

    def update_ui(self):
        """更新界面顯示（統計區塊和用戶選號）"""
        try:
            # 清除舊組件
            self.ids.user_area1.clear_widgets()
            self.ids.user_area2.clear_widgets()

            # 更新總筆數顯示（基於完整資料）
            self.ids.total_count_label.text = str(len(self.all_results))

            # 更新各獎別統計
            self.ids.prize_count_head.text = str(self.stats.get('頭', 0))
            self.ids.prize_count_second.text = str(self.stats.get('貳', 0))
            self.ids.prize_count_third.text = str(self.stats.get('參', 0))
            self.ids.prize_count_fourth.text = str(self.stats.get('肆', 0))
            self.ids.prize_count_fifth.text = str(self.stats.get('伍', 0))
            self.ids.prize_count_sixth.text = str(self.stats.get('陸', 0))
            self.ids.prize_count_seventh.text = str(self.stats.get('柒', 0))
            self.ids.prize_count_eighth.text = str(self.stats.get('捌', 0))
            self.ids.prize_count_ninth.text = str(self.stats.get('玖', 0))
            self.ids.prize_count_normal.text = str(self.stats.get('普', 0))

            # 添加第一區自選號球
            for num in sorted(self.user_numbers['area1']):
                ball = ResultBall(number=num, area=1, selected=True)
                self.ids.user_area1.add_widget(ball)

            # 添加第二區自選號球
            if self.user_numbers['area2']:
                ball = ResultBall(number=self.user_numbers['area2'], area=2, selected=True)
                self.ids.user_area2.add_widget(ball)

        except Exception as e:
            logger.exception(f"UI更新錯誤: {str(e)}")
    
    def _update_result_list(self):
        """更新結果列表（分頁版本）"""
        try:
            # 清除結果列表
            self.ids.result_list.clear_widgets()
            
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
                self.ids.result_list.add_widget(no_data_label)
                return

            # 顯示當前已載入的所有資料
            for record in self.displayed_results:
                item_widget = self._create_result_item(record)
                self.ids.result_list.add_widget(item_widget)
            
            # 添加載入更多指示器
            self._add_load_more_indicator()

        except Exception as e:
            logger.exception(f"結果列表更新錯誤: {str(e)}")
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表"""
        try:
            # 保存當前滾動的絕對位置
            scroll_view = self.ids.scroll_view
            if hasattr(self.ids, 'scroll_view'):
                # 計算當前滾動的絕對像素位置
                current_content_height = self.ids.result_list.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                
                logger.debug(f"載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
            else:
                current_absolute_scroll = 0
            
            # 移除舊的載入指示器
            self._remove_load_more_indicator()
            
            # 添加新記錄
            for record in new_records:
                item_widget = self._create_result_item(record)
                self.ids.result_list.add_widget(item_widget)
            
            # 重新添加載入指示器
            self._add_load_more_indicator()
            
            # 恢復滾動位置（延遲執行確保UI更新完成）
            Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
            
        except Exception as e:
            logger.exception(f"追加結果錯誤: {str(e)}")
    
    def _restore_scroll_position_absolute(self, target_absolute_scroll):
        """根據絕對位置恢復滾動位置"""
        try:
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                new_content_height = self.ids.result_list.height
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
                logger.debug(f"載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"恢復滾動位置錯誤: {str(e)}")
    
    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        # 創建主容器
        item_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(5),
            padding=(dp(10), 0)
        )

        # 期別和日期行
        row1 = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(10),
            padding=(0, 0, dp(10), 0)
        )

        # 期別標籤
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

        # 日期標籤
        date_label = Label(
            text=f"開獎日期: {record['開獎日期']}",
            font_name='ChineseFont',
            font_size='12sp',
            size_hint_x=1,
            halign='left',
            valign='middle'
        )
        date_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        row1.add_widget(date_label)

        item_box.add_widget(row1)

        # 獎號行
        row2 = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(5),
            padding=(dp(0), 0)
        )

        # 第一區獎號
        for num in sorted(record['獎號']):
            selected = num in self.user_numbers['area1']
            ball = ResultBall(number=num, area=1, selected=selected)
            row2.add_widget(ball)

        # 第二區獎號
        selected_second = (self.user_numbers['area2'] is not None and 
                        self.user_numbers['area2'] == record['第二區'])
        ball = ResultBall(number=record['第二區'], area=2, selected=selected_second, lotto_type=self.lottery_type)
        row2.add_widget(ball)

        # 獎別標籤
        award_label = Label(
            text=record['獎別'],
            font_name='ChineseFont',
            font_size=dp(16),
            bold=True,
            color=(1, 0, 0, 1),
            size_hint_x=None,
            width=dp(60),
            halign='center',
            valign='middle'
        )
        row2.add_widget(award_label)

        item_box.add_widget(row2)

        # 分隔線
        separator = BoxLayout(
            size_hint_y=None,
            height=dp(1)
        )
        with separator.canvas:
            Color(rgba=get_color_from_hex('#888888'))
            Rectangle(pos=separator.pos, size=separator.size)

        item_box.add_widget(separator)
        
        return item_box
    
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
        self.ids.result_list.add_widget(load_more_box)
        
        # 儲存引用以便後續更新
        self.load_more_indicator = load_more_box
        self.load_more_label = load_more_label
    
    def _remove_load_more_indicator(self):
        """移除載入更多指示器"""
        if hasattr(self, 'load_more_indicator') and self.load_more_indicator in self.ids.result_list.children:
            self.ids.result_list.remove_widget(self.load_more_indicator)
    
    def on_scroll_start(self, scroll_view, touch):
        """滾動開始時禁用排序按鈕"""
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            logger.debug("威力彩滾動事件被禁用，忽略滾動開始")
            return
        
        # 記錄觸摸開始位置和時間
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start
        logger.debug(f"威力彩觸摸開始: 位置{touch.pos}, 時間{touch.time_start}")
    
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
                    logger.debug(f"威力彩檢測到滑動，移動距離: {distance:.1f}px")
    
    def on_scroll_end(self, scroll_view, touch):
        """滾動結束時檢查是否需要載入更多並重新啟用排序按鈕"""
        # 檢查是否禁用滾動事件
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            logger.debug("威力彩滾動事件被禁用，忽略滾動結束")
            return
        
        # 計算總移動距離和時間
        if hasattr(self, '_touch_start_pos') and hasattr(self, '_touch_start_time'):
            if self._touch_start_pos:
                dx = abs(touch.pos[0] - self._touch_start_pos[0])
                dy = abs(touch.pos[1] - self._touch_start_pos[1])
                distance = (dx * dx + dy * dy) ** 0.5
                duration = touch.time_start - self._touch_start_time
                
                logger.debug(f"威力彩觸摸結束: 移動距離{distance:.1f}px, 持續時間{duration:.2f}s")
                
                # 如果有滑動，需要等待慣性滾動結束
                if distance > 20:
                    # 開始監控慣性滾動
                    self._start_inertia_monitoring(scroll_view)
                    logger.debug("威力彩開始監控慣性滾動")
        
        # 清除觸摸記錄
        self._touch_start_pos = None
        self._touch_start_time = None
        
        # 立即檢查是否需要載入更多（不等慣性滾動結束）
        self._check_load_more_immediate(scroll_view)
    
    def _start_inertia_monitoring(self, scroll_view):
        """開始監控慣性滾動"""
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
        
        logger.debug(f"威力彩慣性檢查 {self._inertia_check_count}: 位置變化 {scroll_change:.4f}")
        
        # 如果滾動位置變化很小，認為慣性滾動結束
        if scroll_change < 0.001:  # 位置變化小於0.001
            logger.debug("威力彩慣性滾動結束，啟用排序按鈕")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            
            # 檢查是否需要載入更多
            self._check_load_more(scroll_view)
            
            return False  # 停止定時檢查
        
        # 更新上次位置
        self._last_scroll_y = current_scroll_y
        
        # 最多檢查30次（3秒），避免無限檢查
        if self._inertia_check_count >= 30:
            logger.warning("威力彩慣性檢查超時，強制啟用排序按鈕")
            Clock.schedule_once(lambda dt: self._set_scrolling_state(False), 0.1)
            return False
        
        return True  # 繼續檢查
    
    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料（不等慣性滾動結束）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.result_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"威力彩立即檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()
    
    def _check_load_more(self, scroll_view):
        """檢查是否需要載入更多資料（慣性滾動結束後的補充檢查）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部（在到達底部前就開始載入）
        content_height = self.ids.result_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"威力彩慣性滾動結束後檢測到接近底部，載入下一頁 (剩餘內容: {remaining_content:.0f}px)")
            self._load_next_page()
    
    def _set_scrolling_state(self, is_scrolling):
        """設定滾動狀態並更新按鈕"""
        self.is_scrolling = is_scrolling
        if hasattr(self.ids, 'sort_btn'):
            self.ids.sort_btn.disabled = is_scrolling
            # 不改變按鈕文字，只改變禁用狀態
            # self.ids.sort_btn.text 保持不變
        logger.debug(f"威力彩設定滾動狀態: {is_scrolling}, 按鈕禁用: {is_scrolling}")
    
    def toggle_sort_order(self):
        """切換排序方式（檢查是否在滾動中）"""
        logger.debug(f"威力彩排序按鈕被點擊，滾動狀態: {self.is_scrolling}")
        
        if self.is_scrolling:
            logger.debug("威力彩滾動中，忽略排序請求")
            return
        
        logger.debug("威力彩開始執行排序")
        loading_popup = LoadingPopup(title='重新排序中')
        loading_popup.open()
        
        Clock.schedule_once(lambda dt: self._perform_sort(loading_popup), 0.1)
   
    def back_to_query(self):
        """返回查詢界面"""
        self.manager.current = 'power_query'

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
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='power_lotto'")
            if not cursor.fetchone():
                logger.error("錯誤：power_lotto表不存在")
                return
        
            # 檢查記錄數量
            cursor.execute("SELECT COUNT(*) FROM power_lotto")
            count = cursor.fetchone()[0]
            logger.debug(f"資料庫中包含 {count} 條威力彩記錄")
        
            # 顯示前5條記錄
            cursor.execute("SELECT * FROM power_lotto ORDER BY date DESC LIMIT 5")
            for row in cursor.fetchall():
                logger.debug(row)
        
            conn.close()
        except Exception as e:
            logger.exception(f"資料庫檢查錯誤: {str(e)}")


class PowerLottoSavedScreen(BaseLotterySavedScreen):
    """威力彩自選號界面"""
    
    @property
    def lottery_type(self):
        return 'powerlotto'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._setup_ui)  # 延遲初始化UI

    def _setup_ui(self, dt):
        """延遲初始化UI元件"""
        pass  # 其他初始化代碼...
    
    def load_saved_numbers(self):
        """從SQLite加載自選號"""
        try:
            # 使用自選號資料庫
            query = '''
            SELECT id, num1, num2, num3, num4, num5, num6, special_num 
            FROM custom_numbers 
            WHERE lottery_type = ?
            ORDER BY created_time DESC
            '''
            rows = self.db_manager.execute_custom_query(query, ('power',))
        
            for row in rows:
                self.saved_numbers.append({
                    'id': row[0],  # 儲存唯一ID
                    'numbers': sorted([row[i] for i in range(1, 7)]),
                    'special': row[7]
                })
            
        except Exception as e:
            logger.exception(f"加載自選號失敗: {str(e)}")

    
    def populate_saved_list(self):
        """填充自選號列表"""
        # Get reference to the saved_list GridLayout
        saved_list = self.ids.saved_list
    
        # Clear existing widgets
        saved_list.clear_widgets()
        
        if not self.saved_numbers:
            saved_list.add_widget(Label(
                text="沒有儲存的自選號",
                font_name='ChineseFont',
                font_size=dp(18),
                color=get_color_from_hex('#FF0000'),
                halign='center'
            ))
            saved_list.height = dp(50)  # Set minimum height for empty list
            return
    
        # Calculate total height needed
        total_height = 0

        for index, item in enumerate(self.saved_numbers):
            # 創建自選號條目
            box = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(50),
                spacing=dp(5),
                padding=(dp(10), dp(5)))

        
            # 第一區號碼球
            area1_box = BoxLayout(
                orientation='horizontal',
                spacing=dp(5),
                size_hint_x=0.6)
        
            for num in sorted(item['numbers']):
                ball = ResultBall(number=num, area=1, selected=True, lotto_type=self.lottery_type)
                area1_box.add_widget(ball)
        
            box.add_widget(area1_box)
        
            # 第二區號碼球
            if item['special']:
                area2_box = BoxLayout(
                    orientation='horizontal',
                    spacing=dp(5),
                    size_hint_x=0.1)
            
                ball = ResultBall(number=item['special'], area=2, selected=True, lotto_type=self.lottery_type)
                area2_box.add_widget(ball)
                box.add_widget(area2_box)
            else:
                # 如果沒有第二區號碼，添加空白佔位
                box.add_widget(Widget(size_hint_x=0.1))

            # 添加觸摸行為
            box.bind(
                on_touch_down=lambda instance, touch, idx=index: self.on_saved_number_touch(instance, touch, idx))
       
            saved_list.add_widget(box)
            total_height += dp(50)  # Add height for each row
    
        # Set the GridLayout's height
        saved_list.height = total_height

    def _cancel_long_press(self, instance):
        """取消長按事件"""
        if hasattr(instance, '_long_press_trigger'):
            Clock.unschedule(instance._long_press_trigger)
            del instance._long_press_trigger
           

    def on_saved_number_touch(self, instance, touch, index):
        if instance.collide_point(*touch.pos) and touch.button == 'left':
            if touch.is_double_tap:
                # 雙擊事件 - 直接提取
                self.use_saved_number(index)
                return True
            elif not touch.is_mouse_scrolling:
                # 標記觸控開始，用於區分短按和長按
                touch.ud['saved_number_index'] = index
                touch.ud['long_press_trigger'] = Clock.schedule_once(
                    lambda dt: self._handle_long_press(touch, index),
                    1  # 1秒長按時間
                )
                return True
        return False


    def _handle_single_click(self, touch, index):
        """處理單擊事件"""
        if 'saved_number_clicked' in touch.ud:
            self.use_saved_number(index)
            del touch.ud['saved_number_clicked']



    def _handle_long_press(self, touch, index):
        """真正的長按事件 - 顯示刪除對話框"""
        if 'saved_number_index' in touch.ud:
            self.show_delete_confirmation(index)
            del touch.ud['saved_number_index']


    def on_touch_up(self, touch):
        """觸控釋放時處理短按事件"""
        super().on_touch_up(touch)
    
        if hasattr(touch, 'ud') and 'saved_number_index' in touch.ud:
            # 取消可能存在的長按計時器
            if 'long_press_trigger' in touch.ud:
                Clock.unschedule(touch.ud['long_press_trigger'])
                del touch.ud['long_press_trigger']
        
            # 如果是短按（未觸發長按）則提取號碼
            if 'long_press_triggered' not in touch.ud:
                index = touch.ud['saved_number_index']
                self.use_saved_number(index)
        
            del touch.ud['saved_number_index']
        return True


    def check_long_press(self, touch, index):
        """檢查是否長按"""
        if 'long_press_scheduled' in touch.ud and touch.ud['long_press_scheduled']:
            # 顯示刪除確認對話框
            self.show_delete_confirmation(index)

    def show_delete_confirmation(self, index):
        """顯示刪除確認對話框（綁定當前索引）"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 顯示要刪除的號碼（視覺化確認）
        target = self.saved_numbers[index]
        numbers_label = Label(
            text=f"第一區: {', '.join(map(str, target['numbers']))}\n第二區: {target['special']}",
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
            # 執行刪除操作
            self._delete_from_database(index)
            # 重新載入列表
            self.load_saved_numbers()
            self.populate_saved_list()

    def _delete_from_database(self, index):
        """從數據庫刪除指定自選號"""
        try:
            # 獲取要刪除的記錄ID
            record_id = self.saved_numbers[index].get('id')
        
            if record_id:
                # 使用自選號資料庫
                query = 'DELETE FROM custom_numbers WHERE id = ?'
                self.db_manager.execute_custom_delete(query, (record_id,))
        except Exception as e:
            logger.exception(f"刪除失敗: {str(e)}")
            self.show_popup("錯誤", "刪除自選號時發生錯誤")

    
    def use_saved_number(self, index):
        """Sets the selection on the query screen and switches to it."""
        if 0 <= index < len(self.saved_numbers):
            saved_selection = self.saved_numbers[index]
            query_screen = self.manager.get_screen('power_query')

            # Set the selection lists on the query screen
            query_screen.selected_area1 = saved_selection.get('numbers', [])
            special_num = saved_selection.get('special')
            query_screen.selected_area2 = [special_num] if special_num is not None else []

            # Switch back to the query screen
            self.manager.current = 'power_query'
    
    

    
    def back_to_query(self):
        """返回查詢界面"""
        self.manager.current = 'power_query'

class PowerLottoDuplicateScreen(BaseAdvancedResultScreen):
    """威力彩重複號碼查詢界面"""
    duplicates = ListProperty([])
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'power_lotto'
    
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
    
    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"威力彩重複六碼頁面進入，初始化滾動狀態: {self.is_scrolling}")
        
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
            logger.debug("威力彩重複六碼查詢完成，已重置滾動位置")
            
            # 關閉載入彈窗
            self.loading_popup.dismiss()
            
        except Exception as e:
            error_msg = f"查詢重複六碼失敗: {str(e)}"
            logger.exception(error_msg)
            self.loading_popup.dismiss()
            self.show_popup("錯誤", error_msg)

    def find_duplicates(self):
        """使用 SQLite 查詢重複六碼"""
        app = App.get_running_app()
        db_path = app.resource_path('data/lotto_history.db')
        self.duplicates = []
        self.all_results = []

        if not os.path.exists(db_path):
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 修改查詢語句，使用列索引而非列名
            cursor.execute('''
            SELECT 
                num1, num2, num3, num4, num5, num6,
                COUNT(*) as count,
                GROUP_CONCAT(issue, ', ') as issues
            FROM power_lotto
            GROUP BY num1, num2, num3, num4, num5, num6
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            ''')

            for row in cursor.fetchall():
                # 使用數字索引存取列 (0=num1, 1=num2, ..., 5=num6, 6=count, 7=issues)
                duplicate_item = {
                    'numbers': sorted([row[0], row[1], row[2], row[3], row[4], row[5]]),
                    'count': row[6],
                    'issues': row[7]
                }
                self.duplicates.append(duplicate_item)
                self.all_results.append(duplicate_item)

            conn.close()
            logger.debug(f"威力彩重複六碼查詢完成: 總筆數={len(self.all_results)}")
        except Exception as e:
            logger.exception(f"重複查詢錯誤: {str(e)}")

    def _initialize_pagination(self):
        """初始化分頁參數"""
        total_records = len(self.all_results)
        self.current_page = 0
        self.displayed_results = []
        self.has_more_data = total_records > self.page_size
        
        logger.debug(f"威力彩重複六碼分頁初始化: 總筆數={total_records}, 每頁={self.page_size}")
    
    def _load_first_page(self):
        """載入第一頁資料"""
        if self.all_results:
            end_index = min(self.page_size, len(self.all_results))
            self.displayed_results = self.all_results[:end_index]
            self.current_page = 1
            self._update_result_list()
            
            # 檢查是否還有更多資料
            self.has_more_data = end_index < len(self.all_results)
            logger.debug(f"威力彩重複六碼第一頁載入完成: 顯示 1-{end_index} 筆，共 {len(self.all_results)} 筆")
        else:
            self.has_more_data = False
            self._update_result_list()  # 顯示無資料

    def _update_result_list(self):
        """更新結果列表顯示"""
        try:
            # 清空結果列表
            self.ids.duplicate_list.clear_widgets()
            
            # 添加總筆數顯示
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = f"總筆數: {len(self.all_results)}"
            
            if not self.displayed_results:
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
            logger.exception(f"威力彩重複六碼更新列表錯誤: {str(e)}")

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
                area=1,  # 威力彩第一區用黃色
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

    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'duplicate_list'):
            logger.warning("威力彩重複六碼找不到duplicate_list，無法添加載入指示器")
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
            # 保存當前滾動位置
            scroll_view = self.ids.scroll_view
            content_height_before = self.ids.duplicate_list.height
            viewport_height = scroll_view.height
            current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, content_height_before - viewport_height)
            
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
                
                # 恢復滾動位置
                Clock.schedule_once(lambda dt: self._restore_scroll_position_absolute(current_absolute_scroll), 0.1)
                
                logger.debug(f"威力彩重複六碼載入第{self.current_page}頁: 顯示 {start_index+1}-{end_index} 筆")
                
            else:
                self.has_more_data = False
                
        except Exception as e:
            logger.exception(f"威力彩重複六碼載入下一頁錯誤: {str(e)}")
        finally:
            self.is_loading_more = False
            self._hide_loading_indicator()

    def _restore_scroll_position_absolute(self, target_absolute_scroll):
        """恢復到指定的絕對滾動位置"""
        try:
            scroll_view = self.ids.scroll_view
            content_height = self.ids.duplicate_list.height
            viewport_height = scroll_view.height
            
            if content_height > viewport_height:
                max_scroll_distance = content_height - viewport_height
                new_scroll_y = 1 - (target_absolute_scroll / max_scroll_distance)
                new_scroll_y = max(0, min(1, new_scroll_y))
                scroll_view.scroll_y = new_scroll_y
            else:
                scroll_view.scroll_y = 1
                
        except Exception as e:
            logger.exception(f"威力彩重複六碼恢復滾動位置錯誤: {str(e)}")

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
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            return
        
        self._touch_start_pos = touch.pos
        self._touch_start_time = touch.time_start

    def on_scroll_move(self, scroll_view, touch):
        """滾動移動時檢查是否為真正的滑動"""
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            return
        
        if not hasattr(self, '_touch_start_pos') or not hasattr(self, '_touch_start_time'):
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
        if hasattr(self, '_scroll_events_disabled') and self._scroll_events_disabled:
            return
        
        # 計算總移動距離
        distance = 0
        if hasattr(self, '_touch_start_pos') and hasattr(self, '_touch_start_time'):
            if self._touch_start_pos:
                dx = abs(touch.pos[0] - self._touch_start_pos[0])
                dy = abs(touch.pos[1] - self._touch_start_pos[1])
                distance = (dx * dx + dy * dy) ** 0.5
        
        # 如果有明顯滑動，需要等待慣性滾動結束
        if distance > 20:
            # 開始監控慣性滾動
            self._start_inertia_monitoring(scroll_view)
        else:
            # 沒有明顯滑動，立即重新啟用功能
            self.is_scrolling = False
        
        # 清除觸摸記錄
        self._touch_start_pos = None
        self._touch_start_time = None
        
        # 立即檢查是否需要載入更多
        self._check_load_more_immediate(scroll_view)

    def _start_inertia_monitoring(self, scroll_view):
        """開始監控慣性滾動"""
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
        
        # 如果滾動位置變化很小，認為慣性滾動結束
        if scroll_change < 0.001:  # 位置變化小於0.001
            self.is_scrolling = False
            
            # 檢查是否需要載入更多
            self._check_load_more(scroll_view)
            
            return False  # 停止定時檢查
        
        # 更新上次位置
        self._last_scroll_y = current_scroll_y
        
        # 最多檢查30次（3秒），避免無限檢查
        if self._inertia_check_count >= 30:
            self.is_scrolling = False
            return False
        
        return True  # 繼續檢查

    def _check_load_more_immediate(self, scroll_view):
        """立即檢查是否需要載入更多資料"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部
        content_height = self.ids.duplicate_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"威力彩重複六碼立即檢測到接近底部，載入下一頁")
            self._load_next_page()

    def _check_load_more(self, scroll_view):
        """檢查是否需要載入更多資料（慣性滾動結束後的補充檢查）"""
        if not self.has_more_data or self.is_loading_more:
            return
        
        # 檢查是否接近底部
        content_height = self.ids.duplicate_list.height
        viewport_height = scroll_view.height
        current_scroll_pos = (1 - scroll_view.scroll_y) * max(0, content_height - viewport_height)
        remaining_content = content_height - current_scroll_pos - viewport_height
        
        # 當剩餘內容少於1.5個螢幕高度時開始載入
        if remaining_content <= viewport_height * 1.5:
            logger.debug(f"威力彩重複六碼慣性滾動結束後檢測到接近底部，載入下一頁")
            self._load_next_page()
    
    def populate_duplicate_list(self):
        """填充重複號碼列表"""
        duplicate_list = self.ids.duplicate_list
        duplicate_list.clear_widgets()
        
        if not self.duplicates:
            duplicate_list.add_widget(Label(
                text="沒有重複的六碼組合",
                font_name='ChineseFont',
                font_size=dp(18),
                color=get_color_from_hex('#FF0000'),
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(50),
                padding=(0, dp(20))  # 增加上下padding
            ))
            return
        
        for item in self.duplicates:
            # 創建重複條目 主容器 (單行)
            box = ClickableBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(50),
                spacing=dp(5),
                padding=(dp(10), dp(5)))

            # 第一區號碼球 (黃色)
            for num in sorted(item['numbers']):
                ball = ResultBall(
                    number=num, 
                    area=1,  # 第一區用黃色
                    size_hint=(None, None),
                    size=(dp(30), dp(30)))  # 固定球大小
                box.add_widget(ball)
        
            # 重複次數 (白色文字)
            count_label = Label(
                text=f"({item['count']}次)",  # 只顯示次數
                font_name='ChineseFont',
                font_size=dp(20),
                color=(1, 1, 1, 1),  # 白色
                size_hint_x=None,
                width=dp(40),
                halign='center'
            )
            box.add_widget(count_label)
        
            # 點擊事件（單擊/雙擊都會觸發）
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
        """處理重複項目的點擊事件 - 單擊/雙擊都顯示詳細資訊"""
        # 無論單擊或雙擊都顯示詳細資訊
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

            # 修改為使用列索引
            cursor.execute('''
            SELECT 
                issue, date,
                num1, num2, num3, num4, num5, num6,
                special_num
            FROM power_lotto
            WHERE num1 IN (?,?,?,?,?,?)
              AND num2 IN (?,?,?,?,?,?)
              AND num3 IN (?,?,?,?,?,?)
              AND num4 IN (?,?,?,?,?,?)
              AND num5 IN (?,?,?,?,?,?)
              AND num6 IN (?,?,?,?,?,?)
            ORDER BY date DESC
            ''', numbers * 6)

            for row in cursor.fetchall():
                details.append({
                    '期別': row[0],  # issue
                    '開獎日期': row[1],  # date
                    '獎號': [row[2], row[3], row[4], row[5], row[6], row[7]],  # num1-num6
                    '第二區': row[8]  # special_num
                })

            conn.close()
        except Exception as e:
            logger.exception(f"詳細記錄查詢錯誤: {str(e)}")
            traceback.print_exc()

        detail_screen = self.manager.get_screen('power_duplicate_detail')
        detail_screen.details = details
        self.manager.current = 'power_duplicate_detail'

    #def on_duplicate_item_click(self, instance, touch, item):
    #    """處理重複項目的點擊事件"""
    #    if instance.collide_point(*touch.pos):
    #        self.show_duplicate_details(item['numbers'])
    
    def back_to_query(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_back_to_query)

    def _real_back_to_query(self):
        """返回查詢界面"""
        self.manager.current = 'power_query'


class PowerLottoDuplicateDetailScreen(BaseAdvancedResultScreen):
    """重複六碼詳細信息界面"""
    details = ListProperty([])
    
    # 實現抽象屬性
    @property
    def table_name(self):
        return 'power_lotto'
    
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
            logger.exception(f"威力彩重複記錄詳情載入下一頁錯誤: {str(e)}")
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
            logger.exception(f"威力彩重複記錄詳情追加記錄錯誤: {str(e)}")
            traceback.print_exc()
    
    def _create_detail_item(self, record):
        """創建詳細記錄項目的UI組件"""
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
            height=dp(40))
        
        # 第一區獎號
        for num in sorted(record['獎號']):
            ball = ResultBall(number=num, area=1)
            row2.add_widget(ball)
        
        # 第二區獎號
        ball = ResultBall(number=record['第二區'], area=2)
        row2.add_widget(ball)
        
        box.add_widget(row2)
        
        return box
    
    def _add_load_more_indicator(self):
        """添加載入更多指示器"""
        if not hasattr(self.ids, 'detail_list'):
            logger.warning("威力彩重複記錄詳情找不到detail_list，無法添加載入指示器")
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
            logger.exception(f"威力彩重複記錄詳情恢復滾動位置錯誤: {str(e)}")
    
    def populate_detail_list(self):
        """填充詳細記錄列表 - 保留向後相容性"""
        # 這個方法現在由 _update_result_list 處理
        pass
    
    def back_to_duplicate(self):
        """返回重複列表界面"""
        self.manager.current = 'power_duplicate'

class PowerLottoWinningDetailsScreen(PowerLottoResultScreen):
    """威力彩自選號中獎詳情界面 - 繼承自PowerLottoResultScreen以重用UI佈局"""
    query_params = DictProperty({})
    stats = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保威力彩中獎詳情頁面預設為降序排列
        self.sort_order = 'DESC'
    
    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        logger.debug(f"威力彩中獎詳情頁面 query_params: {self.query_params}")
        
        # 不調用父類的 on_pre_enter，避免重複初始化
        # 手動處理滾動狀態初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        self.sort_order = 'DESC'
        
        if hasattr(self.ids, 'title_label'):
            self.ids.title_label.text = '威力彩自選號中獎詳情'
        
        if self.query_params:
            # 設定用戶選號
            if 'area1' in self.query_params and 'area2' in self.query_params:
                self.user_numbers = {
                    'area1': self.query_params['area1'],
                    'area2': self.query_params['area2']
                }
            
            # 如果 query_params 中已經有結果資料，直接使用
            if 'results' in self.query_params:
                self.all_results = self.query_params['results']
                self.results = self.all_results
                logger.debug(f"威力彩中獎詳情使用傳入的結果: 共 {len(self.all_results)} 筆")
                
                # 計算統計資料
                if hasattr(self, 'calculate_stats'):
                    logger.debug("威力彩重複記錄詳情開始監控慣性滾動")
                    self.calculate_stats()
                    logger.debug(f"威力彩中獎詳情統計完成: {self.stats}")
                else:
                    logger.warning("威力彩中獎詳情沒有 calculate_stats 方法")
                
                # 初始化分頁
                self._initialize_pagination()
                
                # 更新UI
                if hasattr(self, 'update_ui'):
                    logger.debug("威力彩中獎詳情開始更新UI...")
                    self.update_ui()
                    logger.debug("威力彩中獎詳情UI更新完成")
                else:
                    logger.warning("威力彩中獎詳情沒有 update_ui 方法")
                
                # 載入第一頁
                self._load_first_page()
            else:
                # 執行完整查詢並初始化分頁
                self._perform_full_query_with_pagination()
        else:
            logger.warning("威力彩中獎詳情頁面: 沒有 query_params，無法顯示資料")
    
    def _perform_full_query_with_pagination(self):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 1. 執行完整查詢（用於統計）
            # 威力彩中獎詳情使用 perform_winning_query，其他使用 perform_query
            if hasattr(self, 'perform_winning_query') and 'WinningDetails' in self.__class__.__name__:
                self.all_results = self.perform_winning_query()
            elif hasattr(self, 'perform_query'):
                self.all_results = self.perform_query()
            else:
                # 如果都沒有，使用 query_params 中的資料
                self.all_results = self.query_params.get('results', [])
            
            self.results = self.all_results  # 保持向後相容
            
            logger.debug(f"威力彩中獎詳情查詢完成: 共 {len(self.all_results)} 筆資料")
            
            # 2. 計算統計資料（基於完整資料）
            if hasattr(self, 'calculate_stats'):
                self.calculate_stats()
            
            # 3. 初始化分頁
            self._initialize_pagination()
            
            # 4. 更新UI（統計區塊）
            if hasattr(self, 'update_ui'):
                self.update_ui()
            
            # 5. 載入第一頁資料
            self._load_first_page()
            
        except Exception as e:
            logger.exception(f"威力彩中獎詳情分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    # _update_result_list 和 _append_to_result_list 現在由父類 PowerLottoResultScreen 提供
    
    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        # 創建主容器
        item_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(5),
            padding=(dp(10), 0)
        )

        # 期別和日期行
        row1 = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(10),
            padding=(0, 0, dp(10), 0)
        )

        # 期別標籤
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

        # 日期標籤
        date_label = Label(
            text=f"開獎日期: {record['開獎日期']}",
            font_name='ChineseFont',
            font_size='12sp',
            size_hint_x=1,
            halign='left',
            valign='middle'
        )
        date_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        row1.add_widget(date_label)

        item_box.add_widget(row1)

        # 獎號行
        row2 = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(5),
            padding=(dp(0), 0)
        )

        # 第一區獎號
        for num in sorted(record['獎號']):
            selected = num in self.user_numbers['area1']
            ball = ResultBall(number=num, area=1, selected=selected)
            row2.add_widget(ball)

        # 第二區獎號
        selected_second = (self.user_numbers['area2'] is not None and 
                        self.user_numbers['area2'] == record['第二區'])
        ball = ResultBall(number=record['第二區'], area=2, selected=selected_second, lotto_type=self.lottery_type)
        row2.add_widget(ball)

        # 獎別標籤
        award_label = Label(
            text=record['獎別'],
            font_name='ChineseFont',
            font_size=dp(16),
            bold=True,
            color=(1, 0, 0, 1),
            size_hint_x=None,
            width=dp(60),
            halign='center',
            valign='middle'
        )
        row2.add_widget(award_label)

        item_box.add_widget(row2)

        # 分隔線
        separator = BoxLayout(
            size_hint_y=None,
            height=dp(1)
        )
        with separator.canvas:
            Color(rgba=get_color_from_hex('#888888'))
            Rectangle(pos=separator.pos, size=separator.size)

        item_box.add_widget(separator)
        
        return item_box
    
    # _add_load_more_indicator, _remove_load_more_indicator, _restore_scroll_position_absolute 現在由父類提供
    
    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {
            '頭': 0, '貳': 0, '參': 0, '肆': 0, '伍': 0,
            '陸': 0, '柒': 0, '捌': 0, '玖': 0, '普': 0
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
            if hasattr(self.ids, 'user_area1'):
                self.ids.user_area1.clear_widgets()
            if hasattr(self.ids, 'user_area2'):
                self.ids.user_area2.clear_widgets()

            # 更新總筆數顯示（基於完整資料）
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = str(len(self.all_results))

            # 更新各獎別統計
            logger.debug(f"威力彩中獎詳情更新獎別統計，stats: {self.stats}")
            
            if hasattr(self.ids, 'prize_count_head'):
                count = str(self.stats.get('頭', 0))
                self.ids.prize_count_head.text = count
                logger.debug(f"更新頭獎統計: {count}")
            if hasattr(self.ids, 'prize_count_second'):
                count = str(self.stats.get('貳', 0))
                self.ids.prize_count_second.text = count
                logger.debug(f"更新貳獎統計: {count}")
            if hasattr(self.ids, 'prize_count_third'):
                count = str(self.stats.get('參', 0))
                self.ids.prize_count_third.text = count
                logger.debug(f"更新參獎統計: {count}")
            if hasattr(self.ids, 'prize_count_fourth'):
                count = str(self.stats.get('肆', 0))
                self.ids.prize_count_fourth.text = count
                logger.debug(f"更新肆獎統計: {count}")
            if hasattr(self.ids, 'prize_count_fifth'):
                count = str(self.stats.get('伍', 0))
                self.ids.prize_count_fifth.text = count
                logger.debug(f"更新伍獎統計: {count}")
            if hasattr(self.ids, 'prize_count_sixth'):
                count = str(self.stats.get('陸', 0))
                self.ids.prize_count_sixth.text = count
                logger.debug(f"更新陸獎統計: {count}")
            if hasattr(self.ids, 'prize_count_seventh'):
                count = str(self.stats.get('柒', 0))
                self.ids.prize_count_seventh.text = count
                logger.debug(f"更新柒獎統計: {count}")
            if hasattr(self.ids, 'prize_count_eighth'):
                count = str(self.stats.get('捌', 0))
                self.ids.prize_count_eighth.text = count
                logger.debug(f"更新捌獎統計: {count}")
            if hasattr(self.ids, 'prize_count_ninth'):
                count = str(self.stats.get('玖', 0))
                self.ids.prize_count_ninth.text = count
                logger.debug(f"更新玖獎統計: {count}")
            if hasattr(self.ids, 'prize_count_normal'):
                count = str(self.stats.get('普', 0))
                self.ids.prize_count_normal.text = count
                logger.debug(f"更新普獎統計: {count}")

            # 添加第一區自選號球
            if hasattr(self.ids, 'user_area1'):
                for num in sorted(self.user_numbers['area1']):
                    ball = ResultBall(number=num, area=1, selected=True)
                    self.ids.user_area1.add_widget(ball)

            # 添加第二區自選號球
            if hasattr(self.ids, 'user_area2') and self.user_numbers['area2']:
                ball = ResultBall(number=self.user_numbers['area2'], area=2, selected=True)
                self.ids.user_area2.add_widget(ball)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"威力彩中獎詳情UI更新錯誤: {str(e)}")

    def perform_query(self):
        """Override perform_query to call the detailed winning query."""
        return self.perform_winning_query()

    def perform_winning_query(self):
        """查詢所有歷史記錄並判斷中獎詳情"""
        app = App.get_running_app()
        area1_selected = set(self.user_numbers['area1'])
        area2_selected = self.user_numbers['area2']

        db_path = app.resource_path('data/lotto_history.db')
        if not os.path.exists(db_path):
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM power_lotto')
            
            matched_records = []
            for row in cursor:
                winning_numbers = {row[f'num{i}'] for i in range(1, 7)}
                special_num = row['special_num']
                
                matched_count = len(area1_selected.intersection(winning_numbers))
                special_match = (area2_selected is not None and area2_selected == special_num)

                award = self._determine_winning_award(matched_count, special_match)
                
                if award:
                    try:
                        date_obj = datetime.strptime(row['date'], '%Y/%m/%d').date()
                    except (ValueError, TypeError):
                        date_obj = datetime.min.date()

                    matched_records.append({
                        '期別': row['issue'],
                        '開獎日期': row['date'],
                        '日期物件': date_obj,
                        '獎號': sorted(list(winning_numbers)),
                        '第二區': special_num,
                        '獎別': award
                    })
            
            reverse_order = (self.sort_order == 'DESC')
            matched_records.sort(key=lambda x: x['日期物件'], reverse=reverse_order)
            
            conn.close()
            return matched_records
        except Exception as e:
            traceback.print_exc()
            return []

    def _determine_winning_award(self, matched_count, special_match):
        """根據詳細規則判斷獎別"""
        if matched_count == 6 and special_match: return '頭'
        if matched_count == 6 and not special_match: return '貳'
        if matched_count == 5 and special_match: return '參'
        if matched_count == 5 and not special_match: return '肆'
        if matched_count == 4 and special_match: return '伍'
        if matched_count == 4 and not special_match: return '陸'
        if matched_count == 3 and special_match: return '柒'
        if matched_count == 2 and special_match: return '捌'
        if matched_count == 3 and not special_match: return '玖'
        if matched_count == 1 and special_match: return '普'
        return ''

    def back_to_query(self):
        """返回查詢界面"""
        self.manager.current = 'power_query'


class PowerLottoResultScreen(BaseAdvancedResultScreen):
    """威力彩查詢結果頁面"""
    user_numbers = DictProperty({})
    
    # 實現抽象屬性
    @property
    def lottery_type(self):
        return 'power'
    
    @property
    def table_name(self):
        return 'power_lotto'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    
    @property
    def special_column(self):
        return 'special_num'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保威力彩查詢結果頁面預設為降序排列
        self.sort_order = 'DESC'

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
            logger.debug(f"威力彩顯示結果: {len(self.displayed_results)} 筆")
            for i, record in enumerate(self.displayed_results):
                item_widget = self._create_result_item(record)
                if item_widget:
                    self.ids.results_layout.add_widget(item_widget)
                    logger.debug(f"威力彩添加第 {i+1} 筆結果到UI")
                else:
                    logger.error(f"威力彩第 {i+1} 筆結果創建失敗")
            
            # 添加載入更多指示器
            self._add_load_more_indicator()
            
        except Exception as e:
            traceback.print_exc()
            logger.exception(f"威力彩結果列表更新錯誤: {str(e)}")
    
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
                logger.debug(f"威力彩載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"威力彩恢復滾動位置錯誤: {str(e)}")
    
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
                
                logger.debug(f"威力彩載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
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
            logger.exception(f"威力彩追加結果錯誤: {str(e)}")

    def get_prize_info(self, matched_nums, special_matched):
        """威力彩特有的獎別計算邏輯"""
        if matched_nums == 6 and special_matched:
            return '頭獎', '頭'
        if matched_nums == 6 and not special_matched:
            return '貳獎', '貳'
        if matched_nums == 5 and special_matched:
            return '參獎', '參'
        if matched_nums == 5 and not special_matched:
            return '肆獎', '肆'
        if matched_nums == 4 and special_matched:
            return '伍獎', '伍'
        if matched_nums == 4 and not special_matched:
            return '陸獎', '陸'
        if matched_nums == 3 and special_matched:
            return '柒獎', '柒'
        if matched_nums == 2 and special_matched:
            return '捌獎', '捌'
        if matched_nums == 3 and not special_matched:
            return '玖獎', '玖'
        if matched_nums == 1 and special_matched:
            return '普獎', '普'
        return '未中獎', ''

    def show_results(self, selected_area1, selected_area2=None):
        """執行完整查詢並初始化分頁顯示"""
        try:
            # 儲存用戶選號
            self.user_numbers = {
                'area1': list(selected_area1),
                'area2': list(selected_area2) if selected_area2 else []
            }
            
            # 1. 執行完整查詢（用於統計）
            self.all_results = self._query_all_data(selected_area1, selected_area2)
            
            # 2. 初始化分頁
            self._initialize_pagination()
            
            # 3. 更新UI（統計區塊和用戶選號）
            self._update_ui_for_results(selected_area1, selected_area2)
            
            # 4. 載入第一頁資料
            self._load_first_page()
            
            # 5. 確保排序功能在查詢完成後可用
            Clock.schedule_once(lambda dt: self._ensure_sort_enabled(), 1.0)
            
        except Exception as e:
            logger.exception(f"威力彩分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")
    
    def _query_all_data(self, selected_area1, selected_area2=None):
        """執行完整的資料庫查詢"""
        logger.debug(f"威力彩資料庫查詢 - 第一區: {selected_area1}, 第二區: {selected_area2}")
        logger.debug(f"威力彩資料庫路徑: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 構建查詢條件
        conditions = []
        for num in selected_area1:
            conditions.append(f"({num} IN (num1, num2, num3, num4, num5, num6))")
        
        if selected_area2:
            for num in selected_area2:
                conditions.append(f"({num} = special_num)")
        
        query = f"SELECT issue, date, num1, num2, num3, num4, num5, num6, special_num FROM power_lotto WHERE "
        query += " AND ".join(conditions)
        query += f" ORDER BY date {self.sort_order}"

        logger.debug(f"威力彩SQL查詢: {query}")
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.debug(f"威力彩查詢到 {len(rows)} 筆原始記錄")
        conn.close()
        
        # 處理查詢結果
        processed_results = []
        selected_area1_set = set(selected_area1)
        
        # 處理 area2，確保是集合
        if selected_area2:
            if isinstance(selected_area2, (list, tuple)):
                selected_area2_set = set(selected_area2)
            elif isinstance(selected_area2, int):
                selected_area2_set = {selected_area2}
            else:
                selected_area2_set = set()
        else:
            selected_area2_set = set()

        for row in rows:
            issue, date, n1, n2, n3, n4, n5, n6, special_num = row
            winning_nums_list = [n1, n2, n3, n4, n5, n6]
            winning_nums_set = set(winning_nums_list)

            matched_nums = len(selected_area1_set.intersection(winning_nums_set))
            special_matched = special_num in selected_area2_set if selected_area2_set else False

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
        
        logger.debug(f"威力彩處理後結果數量: {len(processed_results)}")
        if processed_results:
            logger.debug(f"威力彩第一筆結果: {processed_results[0]}")
        
        return processed_results
    
    def _update_ui_for_results(self, selected_area1, selected_area2=None):
        """更新UI（統計區塊和用戶選號）"""
        try:
            logger.debug(f"威力彩UI更新 - 第一區: {selected_area1}, 第二區: {selected_area2}")
            logger.debug(f"威力彩查詢結果數量: {len(self.all_results)}")
            
            # 清除舊組件
            if hasattr(self.ids, 'selected_nums_layout'):
                self.ids.selected_nums_layout.clear_widgets()

                # 顯示第一區選號
                logger.debug(f"威力彩顯示第一區選號: {sorted(list(selected_area1))}")
                for num in sorted(list(selected_area1)):
                    ball = ResultBall(number=num, area=1, selected=True, lotto_type='powerlotto')
                    self.ids.selected_nums_layout.add_widget(ball)
                
                # 顯示第二區選號
                if selected_area2:
                    if isinstance(selected_area2, (list, tuple)):
                        for num in sorted(list(selected_area2)):
                            ball = ResultBall(number=num, area=2, selected=True, lotto_type='powerlotto')
                            self.ids.selected_nums_layout.add_widget(ball)
                    elif isinstance(selected_area2, int):
                        ball = ResultBall(number=selected_area2, area=2, selected=True, lotto_type='powerlotto')
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
                '捌獎': 'prize_count_eighth',
                '玖獎': 'prize_count_ninth',
                '普獎': 'prize_count_tenth',
            }
            
            # 重置所有獎別統計
            for prize_id in prize_map.values():
                if hasattr(self.ids, prize_id):
                    self.ids[prize_id].text = '0'

            # 更新總筆數顯示（基於完整資料）
            if hasattr(self.ids, 'total_count_label'):
                self.ids.total_count_label.text = str(len(self.all_results))
            
            # 更新各獎別統計
            for prize, count in prize_counts.items():
                if prize in prize_map and hasattr(self.ids, prize_map[prize]):
                    self.ids[prize_map[prize]].text = str(count)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"威力彩UI更新錯誤: {str(e)}")
    
    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        try:
            from kivy.factory import Factory
            
            result_row = Factory.ResultRow()
            result_row.ids.period_label.text = f'期別: {record["期別"]}'
            result_row.ids.date_label.text = f'開獎日期: {record["開獎日期"]}'
            result_row.ids.prize_label.text = record['獎別'] if record['獎別'] else ''
            
            if record['中獎']:
                result_row.ids.prize_label.color = (1, 0, 0, 1)  # 紅色
            else:
                result_row.ids.prize_label.color = (0.5, 0.5, 0.5, 1)  # 灰色

            selected_area1 = set(self.user_numbers.get('area1', []))
            selected_area2 = set(self.user_numbers.get('area2', []))
            
            # 添加一般號碼
            for num in record['獎號']:
                ball = ResultBall(number=num, area=1, selected=(num in selected_area1), lotto_type='powerlotto')
                result_row.ids.winning_nums_layout.add_widget(ball)

            # 添加特別號
            special_ball = ResultBall(number=record['特別號'], area=2, selected=(record['特別號'] in selected_area2), lotto_type='powerlotto')
            result_row.ids.winning_nums_layout.add_widget(special_ball)

            logger.debug(f"威力彩創建結果項目: 期別={record['期別']}, 獎別={record['獎別']}")
            return result_row
        except Exception as e:
            logger.exception(f"威力彩創建結果項目錯誤: {str(e)}")
            traceback.print_exc()
            return None

    def go_back(self):
        from kivy.app import App
        App.get_running_app().ad_manager.show_interstitial(on_close_callback=self._real_go_back)

    def _real_go_back(self):
        self.manager.current = 'power_query'
        self.on_leave()

    def on_leave(self):
        if hasattr(self.ids, 'results_layout'):
            self.ids.results_layout.clear_widgets()
        if hasattr(self.ids, 'selected_nums_layout'):
            self.ids.selected_nums_layout.clear_widgets()
        if hasattr(self.ids, 'total_count_label'):
            self.ids.total_count_label.text = '0'
        
        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third',
            '肆獎': 'prize_count_fourth',
            '伍獎': 'prize_count_fifth',
            '陸獎': 'prize_count_sixth',
            '柒獎': 'prize_count_seventh',
            '捌獎': 'prize_count_eighth',
            '玖獎': 'prize_count_ninth',
            '普獎': 'prize_count_tenth',
        }
        for prize_id in prize_map.values():
            if hasattr(self.ids, prize_id):
                self.ids[prize_id].text = '0'


class PowerLottoWinningDetailsScreen(BaseAdvancedResultScreen):
    """威力彩自選號中獎詳情頁面"""
    user_numbers = DictProperty({})
    query_params = DictProperty({})
    results = ListProperty([])
    stats = DictProperty({})
    
    # 實現抽象屬性
    @property
    def lottery_type(self):
        return 'power'
    
    @property
    def table_name(self):
        return 'power_lotto'
    
    @property
    def number_columns(self):
        return ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']
    
    @property
    def special_column(self):
        return 'special_num'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 確保威力彩中獎詳情頁面預設為降序排列
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
            logger.exception(f"威力彩結果列表更新錯誤: {str(e)}")
    
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
                logger.debug(f"威力彩載入後 - 內容高度: {new_content_height}, 新滾動位置: {new_scroll_y}")
                
        except Exception as e:
            logger.exception(f"威力彩恢復滾動位置錯誤: {str(e)}")
    
    def _append_to_result_list(self, new_records):
        """追加新記錄到結果列表 - 實現基類抽象方法"""
        try:
            # 保存當前滾動的絕對位置
            if hasattr(self.ids, 'scroll_view'):
                scroll_view = self.ids.scroll_view
                current_content_height = self.ids.results_layout.height
                current_viewport_height = scroll_view.height
                current_absolute_scroll = (1 - scroll_view.scroll_y) * max(0, current_content_height - current_viewport_height)
                
                logger.debug(f"威力彩載入前 - 內容高度: {current_content_height}, 絕對滾動位置: {current_absolute_scroll}")
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
            logger.exception(f"威力彩追加結果錯誤: {str(e)}")

    def on_pre_enter(self):
        """進入屏幕前執行查詢"""
        # 確保滾動狀態正確初始化
        self.is_scrolling = False
        self._scroll_events_disabled = False
        logger.debug(f"威力彩進入頁面，初始化滾動狀態: {self.is_scrolling}, 滾動事件啟用: {not self._scroll_events_disabled}")
        
        if self.query_params:
            self.user_numbers = {
                'area1': self.query_params.get('area1', []),
                'area2': self.query_params.get('area2', [])
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
            Clock.schedule_once(lambda dt: self._ensure_sort_enabled(), 1.0)
            
        except Exception as e:
            logger.exception(f"威力彩分頁查詢錯誤: {str(e)}")
            traceback.print_exc()
            show_popup("錯誤", f"查詢失敗: {str(e)}")

    def calculate_stats(self):
        """計算各獎別統計"""
        stats = {
            '頭獎': 0, '貳獎': 0, '參獎': 0, '肆獎': 0, '伍獎': 0,
            '陸獎': 0, '柒獎': 0, '捌獎': 0, '玖獎': 0, '普獎': 0
        }
        
        # 遍歷所有結果記錄
        for record in self.results:
            award = record.get('獎別全名', '')
            if award and award in stats:
                stats[award] += 1

        # 更新統計數據
        self.stats = stats

        # 打印調試信息
        logger.debug("威力彩獎別統計結果:")
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
                '捌獎': 'prize_count_eighth',
                '玖獎': 'prize_count_ninth',
                '普獎': 'prize_count_tenth',
            }
            
            for prize_full, prize_id in prize_map.items():
                if hasattr(self.ids, prize_id):
                    getattr(self.ids, prize_id).text = str(self.stats.get(prize_full, 0))

            # 添加自選號球
            if hasattr(self.ids, 'selected_nums_layout'):
                # 第一區號碼
                for num in sorted(self.user_numbers.get('area1', [])):
                    ball = ResultBall(number=num, area=1, selected=True, lotto_type='powerlotto')
                    self.ids.selected_nums_layout.add_widget(ball)
                
                # 第二區號碼
                for num in sorted(self.user_numbers.get('area2', [])):
                    ball = ResultBall(number=num, area=2, selected=True, lotto_type='powerlotto')
                    self.ids.selected_nums_layout.add_widget(ball)

        except Exception as e:
            traceback.print_exc()
            logger.exception(f"威力彩UI更新錯誤: {str(e)}")

    def _create_result_item(self, record):
        """創建單個結果項目的UI組件"""
        from kivy.factory import Factory
        
        # 使用Factory創建結果行
        result_row = Factory.ResultRow()
        result_row.ids.period_label.text = f'期別: {record["期別"]}'
        result_row.ids.date_label.text = f'開獎日期: {record["開獎日期"]}'
        result_row.ids.prize_label.text = record.get('獎別簡稱', '')
        result_row.ids.prize_label.color = (1, 0, 0, 1)

        selected_area1 = self.user_numbers.get('area1', [])
        selected_area2 = self.user_numbers.get('area2', [])
        
        for num in record['獎號']:
            ball = ResultBall(number=num, area=1, selected=(num in selected_area1), lotto_type='powerlotto')
            result_row.ids.winning_nums_layout.add_widget(ball)

        special_ball = ResultBall(number=record['特別號'], area=2, selected=(record['特別號'] in selected_area2), lotto_type='powerlotto')
        result_row.ids.winning_nums_layout.add_widget(special_ball)

        return result_row

    def perform_winning_query(self):
        """執行中獎查詢"""
        app = App.get_running_app()
        selected_area1 = set(self.user_numbers.get('area1', []))
        
        # 處理 area2，可能是列表或單個數字
        area2_data = self.user_numbers.get('area2', [])
        if isinstance(area2_data, (list, tuple)):
            selected_area2 = set(area2_data)
        elif isinstance(area2_data, int):
            selected_area2 = {area2_data}
        else:
            selected_area2 = set()

        db_path = self.db_path
        if not os.path.exists(db_path):
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM power_lotto')
            
            matched_records = []
            for row in cursor:
                winning_numbers = {row[f'num{i}'] for i in range(1, 7)}
                special_num_drawn = row['special_num']
                
                prize_full, prize_short = self._determine_winning_award(selected_area1, selected_area2, winning_numbers, special_num_drawn)
                
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

    def _determine_winning_award(self, selected_area1, selected_area2, winning_nums, special_num_drawn):
        """威力彩特有的中獎判斷邏輯"""
        matched_count_main = len(selected_area1.intersection(winning_nums))
        special_match = special_num_drawn in selected_area2

        if matched_count_main == 6 and special_match: return '頭獎', '頭'
        if matched_count_main == 6 and not special_match: return '貳獎', '貳'
        if matched_count_main == 5 and special_match: return '參獎', '參'
        if matched_count_main == 5 and not special_match: return '肆獎', '肆'
        if matched_count_main == 4 and special_match: return '伍獎', '伍'
        if matched_count_main == 4 and not special_match: return '陸獎', '陸'
        if matched_count_main == 3 and special_match: return '柒獎', '柒'
        if matched_count_main == 2 and special_match: return '捌獎', '捌'
        if matched_count_main == 3 and not special_match: return '玖獎', '玖'
        if matched_count_main == 1 and special_match: return '普獎', '普'
        
        return None, ''

    def go_back(self):
        self.manager.current = 'power_query'

    def on_leave(self):
        if hasattr(self.ids, 'results_layout'):
            self.ids.results_layout.clear_widgets()
        if hasattr(self.ids, 'selected_nums_layout'):
            self.ids.selected_nums_layout.clear_widgets()
        if hasattr(self.ids, 'total_count_label'):
            self.ids.total_count_label.text = '0'
        
        prize_map = {
            '頭獎': 'prize_count_head',
            '貳獎': 'prize_count_second',
            '參獎': 'prize_count_third',
            '肆獎': 'prize_count_fourth',
            '伍獎': 'prize_count_fifth',
            '陸獎': 'prize_count_sixth',
            '柒獎': 'prize_count_seventh',
            '捌獎': 'prize_count_eighth',
            '玖獎': 'prize_count_ninth',
            '普獎': 'prize_count_tenth',
        }
        for prize_id in prize_map.values():
            if hasattr(self.ids, prize_id):
                self.ids[prize_id].text = '0'


class PowerLottoSavedScreen(BaseLotterySavedScreen):
    """威力彩自選號管理界面"""
    
    @property
    def lottery_type(self):
        return 'power'
    
    def on_pre_enter(self):
        """進入屏幕前的初始化"""
        self.is_scrolling = False
        self._scroll_events_disabled = False
        self.load_saved_numbers()
        self.populate_saved_list()
        logger.debug(f"威力彩自選號頁面進入，總筆數: {len(self.all_results)}")
    
    def use_saved_number(self, index):
        """使用選中的威力彩自選號（支援分頁索引轉換）"""
        actual_index = index
        if hasattr(self, 'displayed_results') and index < len(self.displayed_results):
            target_item = self.displayed_results[index]
            actual_index = next((i for i, item in enumerate(self.all_results) if item['id'] == target_item['id']), index)
        
        if 0 <= actual_index < len(self.all_results):
            target = self.all_results[actual_index]
            query_screen = self.manager.get_screen('power_query')
            query_screen.clear_selection()
            
            area1_numbers = target['numbers'][:6]
            for num in area1_numbers:
                if num is not None:
                    query_screen.selected_area1.append(num)
            
            if 'special' in target and target['special'] is not None:
                query_screen.selected_area2.append(target['special'])
            
            
            self.manager.current = 'power_query'
            



