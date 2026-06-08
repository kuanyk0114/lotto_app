#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫表格移轉程式
將 custom_numbers 表格從 lotto_history.db 移轉到 custom.db

功能：
1. 檢查來源資料庫中的 custom_numbers 表格
2. 創建新的 custom.db 資料庫
3. 複製表格結構和資料
4. 驗證資料完整性
5. 備份原始資料

作者：系統管理員
日期：2024年當前
"""

import sqlite3
import os
import shutil
from datetime import datetime
import traceback

class DatabaseTableMover:
    def __init__(self):
        self.source_db = 'lotto_history.db'
        self.target_db = 'custom.db'
        self.backup_db = f'lotto_history_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        self.table_name = 'custom_numbers'
        
    def log(self, message):
        """記錄訊息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def check_source_database(self):
        """檢查來源資料庫和表格"""
        self.log("檢查來源資料庫...")
        
        if not os.path.exists(self.source_db):
            self.log(f"❌ 來源資料庫 {self.source_db} 不存在")
            return False
            
        try:
            conn = sqlite3.connect(self.source_db)
            cursor = conn.cursor()
            
            # 檢查表格是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (self.table_name,))
            
            if not cursor.fetchone():
                self.log(f"❌ 表格 {self.table_name} 在來源資料庫中不存在")
                conn.close()
                return False
                
            # 檢查表格結構
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            self.log(f"✅ 找到表格 {self.table_name}，包含 {len(columns)} 個欄位")
            
            for col in columns:
                self.log(f"   - {col[1]} ({col[2]})")
                
            # 檢查資料筆數
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            self.log(f"✅ 表格包含 {count} 筆資料")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ 檢查來源資料庫時發生錯誤: {str(e)}")
            return False
            
    def backup_source_database(self):
        """備份來源資料庫"""
        self.log("備份來源資料庫...")
        
        try:
            shutil.copy2(self.source_db, self.backup_db)
            self.log(f"✅ 已備份來源資料庫到 {self.backup_db}")
            return True
        except Exception as e:
            self.log(f"❌ 備份失敗: {str(e)}")
            return False
            
    def create_target_database(self):
        """創建目標資料庫"""
        self.log("創建目標資料庫...")
        
        try:
            # 如果目標資料庫已存在，先備份
            if os.path.exists(self.target_db):
                backup_name = f"custom_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(self.target_db, backup_name)
                self.log(f"✅ 已備份現有的 {self.target_db} 到 {backup_name}")
                
            # 創建新的目標資料庫
            conn = sqlite3.connect(self.target_db)
            self.log(f"✅ 已創建目標資料庫 {self.target_db}")
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ 創建目標資料庫失敗: {str(e)}")
            return False
            
    def copy_table_structure(self):
        """複製表格結構"""
        self.log("複製表格結構...")
        
        try:
            # 連接來源資料庫
            source_conn = sqlite3.connect(self.source_db)
            source_cursor = source_conn.cursor()
            
            # 獲取表格創建語句
            source_cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (self.table_name,))
            
            create_sql = source_cursor.fetchone()[0]
            self.log(f"✅ 獲取表格創建語句: {create_sql}")
            
            # 連接目標資料庫並創建表格
            target_conn = sqlite3.connect(self.target_db)
            target_cursor = target_conn.cursor()
            
            target_cursor.execute(create_sql)
            target_conn.commit()
            
            self.log(f"✅ 已在目標資料庫中創建表格 {self.table_name}")
            
            source_conn.close()
            target_conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ 複製表格結構失敗: {str(e)}")
            traceback.print_exc()
            return False
            
    def copy_table_data(self):
        """複製表格資料"""
        self.log("複製表格資料...")
        
        try:
            # 連接來源資料庫
            source_conn = sqlite3.connect(self.source_db)
            source_cursor = source_conn.cursor()
            
            # 獲取所有資料
            source_cursor.execute(f"SELECT * FROM {self.table_name}")
            rows = source_cursor.fetchall()
            
            if not rows:
                self.log("⚠️ 來源表格沒有資料需要複製")
                source_conn.close()
                return True
                
            # 獲取欄位名稱
            source_cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            # 連接目標資料庫
            target_conn = sqlite3.connect(self.target_db)
            target_cursor = target_conn.cursor()
            
            # 準備插入語句
            placeholders = ','.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO {self.table_name} VALUES ({placeholders})"
            
            # 批量插入資料
            target_cursor.executemany(insert_sql, rows)
            target_conn.commit()
            
            self.log(f"✅ 已複製 {len(rows)} 筆資料到目標資料庫")
            
            source_conn.close()
            target_conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ 複製表格資料失敗: {str(e)}")
            traceback.print_exc()
            return False
            
    def verify_data_integrity(self):
        """驗證資料完整性"""
        self.log("驗證資料完整性...")
        
        try:
            # 連接來源資料庫
            source_conn = sqlite3.connect(self.source_db)
            source_cursor = source_conn.cursor()
            
            # 連接目標資料庫
            target_conn = sqlite3.connect(self.target_db)
            target_cursor = target_conn.cursor()
            
            # 比較資料筆數
            source_cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            source_count = source_cursor.fetchone()[0]
            
            target_cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            target_count = target_cursor.fetchone()[0]
            
            if source_count != target_count:
                self.log(f"❌ 資料筆數不一致: 來源 {source_count}, 目標 {target_count}")
                return False
                
            # 比較資料內容（簡單檢查）
            source_cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY id")
            source_data = source_cursor.fetchall()
            
            target_cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY id")
            target_data = target_cursor.fetchall()
            
            if source_data != target_data:
                self.log("❌ 資料內容不一致")
                return False
                
            self.log(f"✅ 資料完整性驗證通過: {source_count} 筆資料完全一致")
            
            source_conn.close()
            target_conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ 驗證資料完整性失敗: {str(e)}")
            traceback.print_exc()
            return False
            
    def remove_source_table(self):
        """從來源資料庫移除表格"""
        self.log("從來源資料庫移除表格...")
        
        try:
            conn = sqlite3.connect(self.source_db)
            cursor = conn.cursor()
            
            cursor.execute(f"DROP TABLE {self.table_name}")
            conn.commit()
            
            self.log(f"✅ 已從來源資料庫移除表格 {self.table_name}")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ 移除來源表格失敗: {str(e)}")
            return False
            
    def show_final_status(self):
        """顯示最終狀態"""
        self.log("=" * 50)
        self.log("移轉完成狀態報告")
        self.log("=" * 50)
        
        # 檢查來源資料庫
        if os.path.exists(self.source_db):
            try:
                conn = sqlite3.connect(self.source_db)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (self.table_name,))
                if cursor.fetchone():
                    self.log(f"⚠️ 來源資料庫仍包含 {self.table_name} 表格")
                else:
                    self.log(f"✅ 來源資料庫已移除 {self.table_name} 表格")
                conn.close()
            except Exception as e:
                self.log(f"❌ 檢查來源資料庫失敗: {str(e)}")
        
        # 檢查目標資料庫
        if os.path.exists(self.target_db):
            try:
                conn = sqlite3.connect(self.target_db)
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                count = cursor.fetchone()[0]
                self.log(f"✅ 目標資料庫包含 {count} 筆自選號資料")
                conn.close()
            except Exception as e:
                self.log(f"❌ 檢查目標資料庫失敗: {str(e)}")
                
        # 檢查備份檔案
        if os.path.exists(self.backup_db):
            size = os.path.getsize(self.backup_db)
            self.log(f"✅ 備份檔案 {self.backup_db} ({size} bytes)")
            
    def run(self):
        """執行完整的移轉流程"""
        self.log("開始資料庫表格移轉程序")
        self.log("=" * 50)
        
        # 步驟1: 檢查來源資料庫
        if not self.check_source_database():
            self.log("❌ 移轉失敗: 來源資料庫檢查未通過")
            return False
            
        # 步驟2: 備份來源資料庫
        if not self.backup_source_database():
            self.log("❌ 移轉失敗: 無法備份來源資料庫")
            return False
            
        # 步驟3: 創建目標資料庫
        if not self.create_target_database():
            self.log("❌ 移轉失敗: 無法創建目標資料庫")
            return False
            
        # 步驟4: 複製表格結構
        if not self.copy_table_structure():
            self.log("❌ 移轉失敗: 無法複製表格結構")
            return False
            
        # 步驟5: 複製表格資料
        if not self.copy_table_data():
            self.log("❌ 移轉失敗: 無法複製表格資料")
            return False
            
        # 步驟6: 驗證資料完整性
        if not self.verify_data_integrity():
            self.log("❌ 移轉失敗: 資料完整性驗證未通過")
            return False
            
        # 步驟7: 移除來源表格
        if not self.remove_source_table():
            self.log("❌ 移轉失敗: 無法移除來源表格")
            return False
            
        # 步驟8: 顯示最終狀態
        self.show_final_status()
        
        self.log("=" * 50)
        self.log("🎉 資料庫表格移轉成功完成！")
        self.log("=" * 50)
        return True

def main():
    """主程式"""
    print("資料庫表格移轉程式")
    print("將 custom_numbers 表格從 lotto_history.db 移轉到 custom.db")
    print()
    
    # 確認執行
    response = input("確定要執行移轉嗎？(y/N): ").strip().lower()
    if response != 'y':
        print("移轉已取消")
        return
        
    # 執行移轉
    mover = DatabaseTableMover()
    success = mover.run()
    
    if success:
        print("\n移轉完成！")
        print("請檢查以下檔案：")
        print(f"- {mover.target_db} (新的自選號資料庫)")
        print(f"- {mover.backup_db} (原始資料庫備份)")
    else:
        print("\n移轉失敗！請檢查錯誤訊息並重試。")

if __name__ == "__main__":
    main()