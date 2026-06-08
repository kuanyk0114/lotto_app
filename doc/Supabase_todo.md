# 新增自動連線SupaBase更新獎號功能
## SupaBase的相關參數
SUPABASE_URL=https://wyyiyuinfgbqbeykenin.supabase.co
SUPABASE_KEY=sb_publishable_WKf4yO8K_3xP6q---1j-Ww_emFIPiXe
Storage Bucket name:lotto_new_number
bucket_id = 'lotto_new_number
## 任務目標
1. 登入App時先檢查是否連線網路若未連線直接進入App,有連線則進入更新獎號程序
2. 讀取local路徑data\lotto_history.db內updated_data table的id field這個欄位代表App已更新的獎號版本號
3. 連線SupaBase找出data_list.id比local的data\lotto_history.db內updated_data.id大的所有記錄
4. 若無則無需更新,直接進入主程式
5. 若有則依序讀取SupaBase上data_list.id比local updated_data.id大的記錄的該筆file_name欄位所記載的檔名,去下載SupaBase儲存桶上的檔案
6. 下載完成後計算該案的SHA-256 總和校驗碼若與SupaBase上data_list.checksum不相同代表下載失敗,詢問是否繼續下載,選否則放棄下載及更新步驟進入App,選是則重新下載
7. 若SHA-256 總和校驗碼正確則進入更新步驟
8. 讀取SupaBase上data_list.id該筆data_list.update_type
  - A代表這個版本的 CSV 檔案內的每筆記錄應新增至 App 的 SQLite 資料庫中data\lotto_history.db相對的table
  - U代表這個版本的 CSV 檔案內的每筆記錄應更新或替換 App 的 SQLite 資料庫中data\lotto_history.db相對的table現有的記錄
  - D代表這個版本的 CSV 檔案內的每筆記應從 App 的 SQLite 資料庫中data\lotto_history.db相對的table內刪除
9. 更新成功將此次更新的SupaBase內data_list.id寫入local的data\lotto_history.db內updated_data.id及updated_at寫入更新完成的日期和時間
10. 直到SupaBase內data_list.id沒有比local的data\lotto_history.db內updated_data.id大的,代表已全部更新完成,進入App主程式
## Bucket內CSV檔的記錄結構
  遊戲名稱,期別,開獎日期,銷售總額,銷售注數,總獎金,獎號1,獎號2,獎號3,獎號4,獎號5,獎號6,第二區
  ### **不同遊戲名稱對應的欄位數不同說明如下**
  - 威名彩:包含所有欄位
  - 大樂透:包含所有欄位
  - 今彩539:到獎號5,不含獎號6及第二區
  - 三星彩:到獎號3,不含獎號4,獎號5,獎號6,第二區
  - 四星彩:到獎號4,不含獎號5,獎號6,第二區
  ### **遊戲名稱對應local data\lotto_history.db內table如下** 
  每筆CSV記錄寫入各對應table內
- 威力彩對應data\lotto_history.db內table  power_lotto 
- 大樂透對應data\lotto_history.db內table  big_lotto              
- 彩539對應data\lotto_history.db內table lotto_539              
- 三星彩對應data\lotto_history.db內table  lotto_3star            
- 四星彩對應data\lotto_history.db內table  lotto_4star

