import requests
import hashlib
import sqlite3
import os
import csv
import io
import logging
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

def check_internet(timeout=3):
    """
    Check if internet is available by sending a HEAD request to Supabase URL.
    """
    try:
        # Use HEAD request for low overhead
        requests.head("https://wyyiyuinfgbqbeykenin.supabase.co", timeout=timeout)
        return True
    except Exception as e:
        logger.debug(f"Internet connection check failed: {e}")
        return False

def calculate_sha256(data_bytes):
    """
    Calculate SHA-256 checksum of data bytes.
    """
    return hashlib.sha256(data_bytes).hexdigest()

class SyncManager:
    """
    Manages downloading, verifying, and updating lottery historical data from Supabase.
    """
    def __init__(self, db_path=None):
        self.supabase_url = "https://wyyiyuinfgbqbeykenin.supabase.co"
        self.supabase_key = "sb_publishable_WKf4yO8K_3xP6q---1j-Ww_emFIPiXe"
        self.bucket_id = "lotto_new_number"
        
        # Default DB path relative to modules/sync.py
        if db_path is None:
            self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "lotto_history.db"))
        else:
            self.db_path = db_path
            
        logger.info(f"SyncManager initialized with DB path: {self.db_path}")
        self.client = None
        
    def init_client(self):
        """Lazy initialization of the Supabase Client."""
        if not self.client:
            self.client = create_client(self.supabase_url, self.supabase_key)
            
    def get_local_version(self):
        """
        Read the latest version ID from local SQLite database.
        Returns '0' if no record exists.
        """
        if not os.path.exists(self.db_path):
            logger.warning(f"Database file not found at: {self.db_path}")
            return "0"
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure updated_data table exists (just in case)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS updated_data (
                    id TEXT PRIMARY KEY,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
            
            cursor.execute("SELECT id FROM updated_data")
            rows = cursor.fetchall()
            if not rows:
                return "0"
            
            # Find the maximum version id as an integer
            max_id = 0
            for r in rows:
                try:
                    val = int(r[0])
                    if val > max_id:
                        max_id = val
                except ValueError:
                    pass
            return str(max_id)
        except Exception as e:
            logger.exception(f"Error reading local version: {e}")
            return "0"
        finally:
            if conn:
                conn.close()
                
    def get_local_app_version(self):
        """
        Read the app version from local SQLite database 'app_ver' table.
        Returns '1.0' if no record exists.
        """
        if not os.path.exists(self.db_path):
            logger.warning(f"Database file not found at: {self.db_path}")
            return "1.0"
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure app_ver table exists (just in case)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_ver (
                    ver_num TEXT PRIMARY KEY,
                    ver_date TEXT NOT NULL
                )
            """)
            conn.commit()
            
            cursor.execute("SELECT ver_num FROM app_ver ORDER BY ROWID DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row[0]
            return "1.0"
        except Exception as e:
            logger.error(f"Error reading local app version: {e}")
            return "1.0"
        finally:
            if conn:
                conn.close()

    def fetch_remote_app_version(self):
        """
        Query Supabase app_ver table for the latest version.
        Returns the version string or None if not found/error.
        """
        self.init_client()
        try:
            res = self.client.table("app_ver").select("*").execute()
            if res.data:
                records = res.data
                # Sort by ver_date descending to get the latest version info
                records.sort(key=lambda x: x.get('ver_date', ''), reverse=True)
                latest_ver = records[0].get('ver_num')
                logger.info(f"Latest app version from Supabase: {latest_ver}")
                return latest_ver
            return None
        except Exception as e:
            logger.exception(f"Error fetching remote app version from Supabase: {e}")
            raise e
            
    def fetch_remote_updates(self, local_id):
        """
        Query Supabase data_list table for updates with id > local_id.
        Returns sorted list of rows.
        """
        self.init_client()
        try:
            res = self.client.table("data_list").select("*").execute()
            
            local_id_val = int(local_id)
            updates = []
            for row in res.data:
                try:
                    row_id_val = int(row['id'])
                    if row_id_val > local_id_val:
                        updates.append(row)
                except ValueError:
                    pass
            
            # Sort updates by integer value of id in ascending order
            updates.sort(key=lambda x: int(x['id']))
            logger.info(f"Found {len(updates)} updates from Supabase (local_id={local_id})")
            return updates
        except Exception as e:
            logger.exception(f"Error fetching remote updates from Supabase: {e}")
            raise e
            
    def download_csv_file(self, file_name):
        """
        Download CSV file bytes from Supabase storage bucket.
        """
        self.init_client()
        try:
            logger.info(f"Downloading {file_name} from bucket {self.bucket_id}")
            data_bytes = self.client.storage.from_(self.bucket_id).download(file_name)
            return data_bytes
        except Exception as e:
            logger.exception(f"Error downloading CSV file {file_name}: {e}")
            raise e

    def process_csv_data(self, csv_data_bytes, update_type):
        """
        Parse CSV rows and insert/update/delete records in SQLite database under a single transaction.
        """
        # Mapping from CSV Game Name to SQLite table and expected columns count
        GAME_MAPPING = {
            "威力彩": {"table": "power_lotto", "cols": 13},
            "大樂透": {"table": "big_lotto", "cols": 13},
            "今彩539": {"table": "lotto_539", "cols": 11},
            "三星彩": {"table": "lotto_3star", "cols": 9},
            "四星彩": {"table": "lotto_4star", "cols": 10}
        }
        
        TABLE_COLUMNS = {
            "power_lotto": ["game_name", "issue", "date", "total_sales", "tickets_sold", "total_prize", "num1", "num2", "num3", "num4", "num5", "num6", "special_num"],
            "big_lotto": ["game_name", "issue", "date", "total_sales", "tickets_sold", "total_prize", "num1", "num2", "num3", "num4", "num5", "num6", "special_num"],
            "lotto_539": ["game_name", "issue", "date", "total_sales", "tickets_sold", "total_prize", "num1", "num2", "num3", "num4", "num5"],
            "lotto_3star": ["game_name", "issue", "date", "total_sales", "tickets_sold", "total_prize", "num1", "num2", "num3"],
            "lotto_4star": ["game_name", "issue", "date", "total_sales", "tickets_sold", "total_prize", "num1", "num2", "num3", "num4"]
        }

        def parse_int(val):
            if not val or val.strip() == '':
                return None
            try:
                return int(float(val))
            except ValueError:
                return None

        # Decode using utf-8-sig to automatically strip potential BOM character (\ufeff)
        csv_text = csv_data_bytes.decode('utf-8-sig')
        f = io.StringIO(csv_text)
        reader = csv.reader(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Enable WAL mode for performance
            cursor.execute('PRAGMA journal_mode=WAL')
            
            row_count = 0
            for row in reader:
                if not row or len(row) == 0:
                    continue
                
                game_name = row[0].strip()
                if game_name not in GAME_MAPPING:
                    logger.warning(f"Unknown game name in CSV row: {game_name}")
                    continue
                    
                mapping = GAME_MAPPING[game_name]
                table = mapping["table"]
                expected_cols = mapping["cols"]
                
                # Ensure row has correct column count
                if len(row) < expected_cols:
                    row = row + [""] * (expected_cols - len(row))
                else:
                    row = row[:expected_cols]
                    
                columns = TABLE_COLUMNS[table]
                
                # Build values array with type casting
                vals = [
                    row[0].strip(),      # game_name
                    row[1].strip(),      # issue
                    row[2].strip(),      # date
                    parse_int(row[3]),   # total_sales
                    parse_int(row[4]),   # tickets_sold
                    parse_int(row[5]),   # total_prize
                ]
                for x in row[6:expected_cols]:
                    vals.append(parse_int(x))
                    
                # Apply database action according to update_type
                if update_type == 'A':
                    # Add: Insert or Ignore on conflict
                    cols_str = ", ".join(columns)
                    placeholders = ", ".join(["?"] * len(vals))
                    sql = f"INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})"
                    cursor.execute(sql, vals)
                elif update_type == 'U':
                    # Update: Insert or Replace (overwrites on UNIQUE constraint conflict)
                    cols_str = ", ".join(columns)
                    placeholders = ", ".join(["?"] * len(vals))
                    sql = f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders})"
                    cursor.execute(sql, vals)
                elif update_type == 'D':
                    # Delete: Delete by issue
                    sql = f"DELETE FROM {table} WHERE issue = ?"
                    cursor.execute(sql, (row[1].strip(),))
                    
                row_count += 1
                
            conn.commit()
            logger.info(f"Successfully applied {row_count} rows from CSV (update_type={update_type}) to SQLite")
            return row_count
        except Exception as e:
            conn.rollback()
            logger.exception(f"Transaction failed during CSV processing: {e}")
            raise e
        finally:
            conn.close()

    def save_version_to_local(self, version_id):
        """
        Update local updated_data version log table.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT OR REPLACE INTO updated_data (id, updated_at) 
                VALUES (?, ?)
            """, (version_id, now_str))
            conn.commit()
            logger.info(f"Saved version {version_id} in local updated_data log at {now_str}")
        except Exception as e:
            logger.exception(f"Failed to log version {version_id} in local database: {e}")
            raise e
        finally:
            conn.close()
