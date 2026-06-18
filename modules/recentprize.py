from kivy.uix.screenmanager import Screen
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.metrics import dp
from modules.common import DatabaseManager, ResultBall
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RecentPrizeScreen(Screen):
    current_type = StringProperty('威力彩')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DatabaseManager()
        
    def go_back(self):
        self.manager.current = 'lottery_type'

    def on_pre_enter(self):
        # 重置 Spinner 選擇並載入預設彩種 (威力彩)
        self.ids.type_spinner.text = '威力彩'
        self.load_recent_prizes('威力彩')

    def on_lottery_type_change(self, text):
        self.load_recent_prizes(text)

    def load_recent_prizes(self, type_name):
        # 更新標題
        self.ids.title_label.text = f"{type_name} 近30期獎號"
        
        # 清除舊的結果項目
        layout = self.ids.results_layout
        layout.clear_widgets()
        
        # 重置捲動條位置到最頂部
        self.ids.scroll_view.scroll_y = 1.0

        # 彩種查詢配置映射
        config = {
            '威力彩': {'table': 'power_lotto', 'lotto_type': 'power', 'balls': 6, 'has_special': True, 'sorted': True},
            '大樂透': {'table': 'big_lotto', 'lotto_type': 'big', 'balls': 6, 'has_special': True, 'sorted': True},
            '今彩539': {'table': 'lotto_539', 'lotto_type': '539', 'balls': 5, 'has_special': False, 'sorted': True},
            '3星彩': {'table': 'lotto_3star', 'lotto_type': '3star', 'balls': 3, 'has_special': False, 'sorted': False},
            '4星彩': {'table': 'lotto_4star', 'lotto_type': '4star', 'balls': 4, 'has_special': False, 'sorted': False}
        }
        
        cfg = config.get(type_name)
        if not cfg:
            logger.error(f"未知的彩種: {type_name}")
            return
            
        try:
            # 建立 SQL 欄位列表
            cols = [f"num{i}" for i in range(1, cfg['balls'] + 1)]
            if cfg['has_special']:
                cols.append("special_num")
                
            query = f"SELECT issue, date, {', '.join(cols)} FROM {cfg['table']}"
            rows = self.db_manager.execute_query(query)
            
            # 日期解析輔助函數
            def parse_date(date_str):
                for fmt in ('%Y/%m/%d', '%Y-%m-%d'):
                    try:
                        return datetime.strptime(date_str.strip(), fmt)
                    except ValueError:
                        pass
                logger.warning(f"無法解析的日期格式: {date_str}")
                return datetime.min
                
            # 處理與過濾資料
            processed = []
            for r in rows:
                issue = r[0]
                date_str = r[1]
                nums = list(r[2:2+cfg['balls']])
                special = r[2+cfg['balls']] if cfg['has_special'] else None
                
                # 過濾掉 None 值
                nums = [n for n in nums if n is not None]
                
                processed.append({
                    'issue': issue,
                    'date_str': date_str,
                    'date_obj': parse_date(date_str),
                    'nums': sorted(nums) if cfg['sorted'] else nums,
                    'special': special
                })
                
            # 依日期降序、期別降序排列
            processed.sort(key=lambda x: (x['date_obj'], x['issue']), reverse=True)
            
            # 取近 30 期
            recent_prizes = processed[:30]
            
            if not recent_prizes:
                # 顯示查無資料的標籤
                from kivy.uix.label import Label
                no_data_label = Label(
                    text="暫無獎號資料",
                    font_name='ChineseFont',
                    color=(1, 0, 0, 1),
                    size_hint_y=None,
                    height=dp(50)
                )
                layout.add_widget(no_data_label)
                return
                
            for record in recent_prizes:
                # 透過 Factory 建立單一期獎號元件
                row_widget = Factory.RecentPrizeRow()
                row_widget.ids.period_label.text = f"期別: {record['issue']}"
                row_widget.ids.date_label.text = f"開獎日期: {record['date_str']}"
                
                # 動態加入一般號碼球
                balls_layout = row_widget.ids.balls_layout
                for num in record['nums']:
                    ball = ResultBall(number=num, area=1, selected=False, lotto_type=cfg['lotto_type'])
                    balls_layout.add_widget(ball)
                    
                # 動態加入特別號球 (若有)
                if cfg['has_special'] and record['special'] is not None:
                    special_ball = ResultBall(number=record['special'], area=2, selected=False, lotto_type=cfg['lotto_type'])
                    balls_layout.add_widget(special_ball)
                    
                layout.add_widget(row_widget)
                
        except Exception as e:
            logger.exception(f"載入 {type_name} 近期獎號錯誤: {str(e)}")
            from modules.common import show_popup
            show_popup("錯誤", f"載入獎號失敗: {str(e)}")
