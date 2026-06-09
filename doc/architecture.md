# System Architecture: [lotto_app]

## 技術棧與開發環境 (Technology Stack)

* 運行環境 (Runtime)：[Python 3.11+]
* 核心框架 (Framework)：[Kivy]
* 資料庫 (Database)：[APP內使用SQLite / 網路使用Supabase]

## 專案架構
### APP內
```
Local專案根目錄/
├── main.py	        			#主程式
├── modules/
│    ├── _init_.py
│    ├── common.py          	#包含共用類（如 LotteryTypeScreen、LotteryImageButton）
│    ├── powerlotto.py      	#威力彩相關邏輯
│    ├── biglotto.py        	#大樂透相關邏輯
│    ├── lotto539.py        	#今彩539相關邏輯
│    ├── lotto3star.py      	#三星彩相關邏輯
│    └── lotto4star.py      	#四星彩相關邏輯
├── kv/
│    ├── common.kv          	#共用介面定義
│    ├── powerlotto.kv      	#威力彩介面
│    ├── biglotto.kv        	#大樂透介面
│    ├── lotto539.kv       		#今彩539介面
│    ├── lotto3star.kv    		#三星彩介面
│    └── lotto4star.kv     		#四星彩介面
├── images/
│    ├── logo.png               #主標題圖片
│    ├── power.png              #正常狀態
│    ├── power_pressed.png      #按下狀態
│    ├── big.png                #正常狀態
│    ├── big_pressed.png        #按下狀態
│    ├── lotto539.png           #正常狀態
│    ├── lotto539_pressed.png   #按下狀態
│    ├── lotto3star.png         #正常狀態
│    ├── lotto3star_pressed.png #按下狀態
│    ├── lotto4star.png         #正常狀態
│    └── lotto4star_pressed.png #按下狀態
├── doc/                        #系統文件資料夾
│    ├── context.md             #專案背景知識
│    └── architecture.md        #專案檔案架構及資料庫說明
├── fonts/
│    ├── NotoSansTC-Regular.ttf
│    ├── mingliu.ttc
│    ├── msjh.ttc
│    ├── msjhbd.ttc
│    └── msjhl.ttc
└── data/
     ├── lotto_history.db			#台灣彩券歷史獎號SQLite資料庫
     │     └── Table
     │          ├── power_lotto		#威力彩歷史獎號table
     │          │    └── field
     │          │         ├──id            #INTEGER
     │          │         ├──game_name     #TEXT 彩券名稱
     │          │         ├──issue         #TEXT 期別
     │          │         ├──date          #TEXT 開獎日期
     │          │         ├──total_sales   #INTEGER 銷售總額
     │          │         ├──tickets_sold  #INTEGER 銷售注數
     │          │         ├──total_prize   #INTEGER 總獎金
     │          │         ├──num1          #INTEGER 獎號1
     │          │         ├──num2          #INTEGER 獎號2
     │          │         ├──num3          #INTEGER 獎號3
     │          │         ├──num4          #INTEGER 獎號4
     │          │         ├──num5          #INTEGER 獎號5
     │          │         ├──num6          #INTEGER 獎號6
     │          │         └──special_num   #INTEGER 第二區
     │          ├── big_lotto       #大樂透歷史獎號table
     │          │    └── field
     │          │         ├──id            #INTEGER
     │          │         ├──game_name     #TEXT 彩券名稱
     │          │         ├──issue         #TEXT 期別
     │          │         ├──date          #TEXT 開獎日期
     │          │         ├──total_sales   #INTEGER 銷售總額
     │          │         ├──tickets_sold  #INTEGER 銷售注數
     │          │         ├──total_prize   #INTEGER 總獎金
     │          │         ├──num1          #INTEGER 獎號1
     │          │         ├──num2          #INTEGER 獎號2
     │          │         ├──num3          #INTEGER 獎號3
     │          │         ├──num4          #INTEGER 獎號4
     │          │         ├──num5          #INTEGER 獎號5
     │          │         ├──num6          #INTEGER 獎號6
     │          │         └──special_num   #INTEGER 特別號
     │          ├── lotto_539       #今彩539歷史獎號table
     │          │    └── field
     │          │         ├──id            #INTEGER
     │          │         ├──game_name     #TEXT 彩券名稱
     │          │         ├──issue         #TEXT 期別
     │          │         ├──date          #TEXT 開獎日期
     │          │         ├──total_sales   #INTEGER 銷售總額
     │          │         ├──tickets_sold  #INTEGER 銷售注數
     │          │         ├──total_prize   #INTEGER 總獎金
     │          │         ├──num1          #INTEGER 獎號1
     │          │         ├──num2          #INTEGER 獎號2
     │          │         ├──num3          #INTEGER 獎號3
     │          │         ├──num4          #INTEGER 獎號4
     │          │         └──num5          #INTEGER 獎號5
     │          ├── lotto_3star     #三星彩歷史獎號table
     │          │    └── field
     │          │         ├──id            #INTEGER
     │          │         ├──game_name     #TEXT 彩券名稱
     │          │         ├──issue         #TEXT 期別
     │          │         ├──date          #TEXT 開獎日期
     │          │         ├──total_sales   #INTEGER 銷售總額
     │          │         ├──tickets_sold  #INTEGER 銷售注數
     │          │         ├──total_prize   #INTEGER 總獎金
     │          │         ├──num1          #INTEGER 獎號1-佰位
     │          │         ├──num2          #INTEGER 獎號2-拾位
     │          │         └──num3          #INTEGER 獎號3-個位
     │          ├── lotto_4star    #四星彩歷史獎號table
     │          │    └── field
     │          │         ├──id            #INTEGER
     │          │         ├──game_name     #TEXT 彩券名稱
     │          │         ├──issue         #TEXT 期別
     │          │         ├──date          #TEXT 開獎日期
     │          │         ├──total_sales   #INTEGER 銷售總額
     │          │         ├──tickets_sold  #INTEGER 銷售注數
     │          │         ├──total_prize   #INTEGER 總獎金
     │          │         ├──num1          #INTEGER 獎號1-仟位
     │          │         ├──num2          #INTEGER 獎號2-佰位
     │          │         ├──num3          #INTEGER 獎號3-拾位
     │          │         └──num4          #INTEGER 獎號4-個位
     │          ├── app_ver        #App版本table
     │          │    └── field
     │          │         ├──ver_num       #TEXT App版本號
     │          │         └──ver_date      #TEXT App版本日期
     │          └── updated_data   #已更新獎號DataCSV檔版本table
     │                └── field
     │                     ├──id            #TEXT 已更新獎號DataCSV檔版本號
     │                     └──updated_at    #TEXT 已更新獎號DataCSV檔更新日期
     └── custom.db 	#客戶DB
            └── Table
                 └── custom_numbers #儲存自選號table
                       └── field
                            ├──id            #INTEGER
                            ├──lottery_type  #TEXT 彩券種類 power:威力彩、big:大樂透、539:今彩539、3star:三星彩、4star:四星彩
                            ├──num1          #INTEGER 獎號1
                            ├──num2          #INTEGER 獎號2
                            ├──num3          #INTEGER 獎號3
                            ├──num4          #INTEGER 獎號4
                            ├──num5          #INTEGER 獎號5
                            ├──num6          #INTEGER 獎號6
                            ├──special_num   #INTEGER 第二區或特別號
                            └──created_time  #TIMESTAMP 建立日期時間

```

### SupaBase

#### SupaBase URL及 Publishable key

SUPABASE_URL: https://wyyiyuinfgbqbeykenin.supabase.co
Publishable key(SUPABASE_KEY):
sb_publishable_WKf4yO8K_3xP6q---1j-Ww_emFIPiXe


#### Supabase table
```資料表
Tablet
├── data_list	                    #SupaBase  PostgreSQL 資料表，記錄所有可供下載的更新檔案資訊
│    └── field
│         ├── id           TEXT PRIMARY KEY			            #唯一識別碼，版本號
│         ├── file_name    TEXT NOT NULL				            #檔案名稱
│         ├── checksum     TEXT NOT NULL                         #檔案的 SHA-256 總和校驗碼
│         ├── update_type  TEXT NOT NULL                 		#更新類型（A:新增, U:更新, D:刪除）
│         └── created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW() 	#此筆資料建立的時間
│
└── app_ver        #App版本table
      └── field
            ├──ver_num       #TEXT App版本號
            └──ver_date      #TEXT App版本日期


```
#### Supabase BUCKETS
```BUCKETS
Storage Bucket name:lotto_new_number
bucket_id = 'lotto_new_number'
Storage\Files\BUCKETS\lotto_new_number\*.csv		#儲存所有獎號增量CSV檔，每一個檔案都相對記錄在data_list.file_name
```

#### Bucket內CSV檔的記錄結構
  遊戲名稱,期別,開獎日期,銷售總額,銷售注數,總獎金,獎號1,獎號2,獎號3,獎號4,獎號5,獎號6,第二區
  ##### **不同遊戲名稱對應的欄位數不同說明** 
  - 威名彩:包含所有欄位
  - 大樂透:到獎號6,不含第二區
  - 今彩539:到獎號5,不含獎號6及第二區
  - 三星彩:到獎號3,不含獎號4,獎號5,獎號6,第二區
  - 四星彩:到獎號4,不含獎號5,獎號6,第二區
  ##### **遊戲名稱對應local data\lotto_history.db內table如下**
  每筆CSV記錄寫入各對應table內 
- 威力彩對應data\lotto_history.db內table  power_lotto 
- 大樂透對應data\lotto_history.db內table  big_lotto              
- 彩539對應data\lotto_history.db內table lotto_539              
- 三星彩對應data\lotto_history.db內table  lotto_3star            
- 四星彩對應data\lotto_history.db內table  lotto_4star