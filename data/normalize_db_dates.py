import sqlite3
import os
import shutil
from datetime import datetime

db_path = r"d:\我的專案\台彩程式\lotto_app\data\lotto_history.db"
backup_path = db_path + ".bak"

def normalize_date(date_str):
    if not date_str:
        return date_str
    # 移除前後空白
    date_str = date_str.strip()
    
    # 支援 '/' 或 '-' 分割的日期
    for fmt in ('%Y/%m/%d', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(date_str, fmt)
            # 統一輸出成 YYYY/MM/DD (補零)
            return dt.strftime('%Y/%m/%d')
        except ValueError:
            pass
            
    # 如果格式比較奇怪，嘗試手動解析
    try:
        # 例如 2008/1/2 或 2008-1-2
        parts = date_str.replace('-', '/').split('/')
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            # 處理民國年與西元年
            if y < 1000:
                y += 1911 # 預防萬一
            return f"{y:04d}/{m:02d}/{d:02d}"
    except Exception:
        pass
        
    return date_str

def main():
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
        
    # 1. 備份資料庫
    print(f"Creating backup of database to {backup_path}...")
    shutil.copy2(db_path, backup_path)
    print("Backup created successfully.")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    tables = ['power_lotto', 'big_lotto', 'lotto_539', 'lotto_3star', 'lotto_4star']
    
    for table in tables:
        print(f"\nProcessing table: {table}")
        
        # 檢查該表的主鍵欄位名稱，一般是 issue
        c.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in c.fetchall()]
        
        # 我們將使用 issue 和 date
        if 'issue' not in columns or 'date' not in columns:
            print(f"Skipping {table}: required columns (issue, date) not found.")
            continue
            
        c.execute(f"SELECT issue, date FROM {table}")
        rows = c.fetchall()
        
        updated_count = 0
        updates = []
        
        for issue, date_val in rows:
            normalized = normalize_date(date_val)
            if normalized != date_val:
                updates.append((normalized, issue))
                
        if updates:
            print(f"Found {len(updates)} rows to update in {table}. Updating...")
            c.executemany(f"UPDATE {table} SET date = ? WHERE issue = ?", updates)
            conn.commit()
            print(f"Successfully updated {len(updates)} rows in {table}.")
        else:
            print(f"No date normalization needed for {table}.")
            
    conn.close()
    print("\nDatabase migration complete!")

if __name__ == "__main__":
    main()
