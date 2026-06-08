import logging
import threading
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.clock import Clock
from modules.sync import SyncManager, check_internet, calculate_sha256

logger = logging.getLogger(__name__)

class SyncProgressPopup(Popup):
    """
    Popup to display progress of downloading and updating lottery data.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "系統更新"
        self.title_font = "ChineseFont"
        self.size_hint = (0.85, 0.35)
        self.auto_dismiss = False
        
        self.content_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        self.msg_label = Label(
            text="正在準備更新...", 
            font_name="ChineseFont", 
            font_size=dp(15),
            halign="center", 
            valign="middle",
            size_hint_y=0.4
        )
        self.msg_label.bind(size=self._update_text_size)
        self.content_box.add_widget(self.msg_label)
        
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=0.2)
        self.content_box.add_widget(self.progress_bar)
        
        self.detail_label = Label(
            text="", 
            font_name="ChineseFont", 
            font_size=dp(12),
            color=(0.7, 0.7, 0.7, 1),
            halign="center",
            size_hint_y=0.2
        )
        self.content_box.add_widget(self.detail_label)
        
        self.content = self.content_box

    def _update_text_size(self, instance, size):
        instance.text_size = size

    def update_status(self, text, value=None, detail_text=""):
        self.msg_label.text = text
        if value is not None:
            self.progress_bar.value = value
        self.detail_label.text = detail_text


class RetryConfirmPopup(Popup):
    """
    Popup to ask user whether to retry downloading or skip sync when download/verification fails.
    """
    def __init__(self, file_name, on_yes, on_no, **kwargs):
        super().__init__(**kwargs)
        self.title = "檔案下載或校驗失敗"
        self.title_font = "ChineseFont"
        self.size_hint = (0.85, 0.35)
        self.auto_dismiss = False
        
        content_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        msg_label = Label(
            text=f"檔案 {file_name} 下載或校驗 (SHA-256) 失敗。\n下載可能不完整，是否重新下載？",
            font_name="ChineseFont",
            font_size=dp(14),
            halign="center",
            valign="middle",
            size_hint_y=0.6
        )
        msg_label.bind(size=lambda inst, sz: setattr(inst, 'text_size', sz))
        content_box.add_widget(msg_label)
        
        btn_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.4)
        
        btn_no = Button(
            text="進入App (略過更新)",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#757575')
        )
        btn_no.bind(on_release=lambda x: self._choose(on_no))
        
        btn_yes = Button(
            text="重新下載",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#2196F3')
        )
        btn_yes.bind(on_release=lambda x: self._choose(on_yes))
        
        btn_box.add_widget(btn_no)
        btn_box.add_widget(btn_yes)
        content_box.add_widget(btn_box)
        
        self.content = content_box
        
    def _choose(self, callback):
        self.dismiss()
        if callback:
            callback()


class AppUpdatePopup(Popup):
    """
    Popup to notify user that a new app version is available.
    Provides "稍後" (later) and "前往更新" (go to update) options.
    """
    def __init__(self, remote_ver, on_later, on_update, **kwargs):
        super().__init__(**kwargs)
        self.title = "有新版本發佈"
        self.title_font = "ChineseFont"
        self.size_hint = (0.85, 0.35)
        self.auto_dismiss = False
        
        content_box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        msg_label = Label(
            text=f"系統偵測到新版本 ({remote_ver})。\n建議前往商店更新以獲得最佳體驗。",
            font_name="ChineseFont",
            font_size=dp(14),
            halign="center",
            valign="middle",
            size_hint_y=0.6
        )
        msg_label.bind(size=lambda inst, sz: setattr(inst, 'text_size', sz))
        content_box.add_widget(msg_label)
        
        btn_box = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.4)
        
        btn_later = Button(
            text="稍後",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#757575')
        )
        btn_later.bind(on_release=lambda x: self._choose(on_later))
        
        btn_update = Button(
            text="前往更新",
            font_name="ChineseFont",
            font_size=dp(14),
            background_color=get_color_from_hex('#2196F3')
        )
        btn_update.bind(on_release=lambda x: self._choose(on_update))
        
        btn_box.add_widget(btn_later)
        btn_box.add_widget(btn_update)
        content_box.add_widget(btn_box)
        
        self.content = content_box
        
    def _choose(self, callback):
        self.dismiss()
        if callback:
            callback()


def is_newer_version(local_version, remote_version):
    """
    Compare version strings like '1.0', '1.0.1', '2.1' etc.
    Returns True if remote_version is newer than local_version.
    """
    if not local_version or not remote_version:
        return False
    try:
        local_str = str(local_version).strip()
        remote_str = str(remote_version).strip()
        
        local_parts = [int(x) for x in local_str.split('.')]
        remote_parts = [int(x) for x in remote_str.split('.')]
        
        # Pad with zeros to make them the same length
        max_len = max(len(local_parts), len(remote_parts))
        local_parts += [0] * (max_len - len(local_parts))
        remote_parts += [0] * (max_len - len(remote_parts))
        
        return remote_parts > local_parts
    except Exception as e:
        logger.error(f"Error comparing version strings '{local_version}' vs '{remote_version}': {e}")
        return str(remote_version).strip() != str(local_version).strip()


class SyncWorker:
    """
    Runs database sync loop on a background thread.
    Pauses on error to show confirmation dialog on main thread using threading.Event.
    """
    def __init__(self, app):
        self.app = app
        self.sync_manager = SyncManager()
        self.event = threading.Event()
        self.user_decision = None
        
    def run(self):
        # 1. Check internet
        self.update_ui("正在偵測網路連線...", 10, "")
        if not check_internet():
            logger.info("No internet connection. Skipping update.")
            self.update_ui("無網路連線，進入離線模式...", 100, "")
            Clock.schedule_once(lambda dt: self.finish_sync(), 1.0)
            return

        # 1.5 Check App Version
        self.update_ui("正在檢查程式版本...", 15, "")
        local_app_ver = self.sync_manager.get_local_app_version()
        try:
            remote_app_ver = self.sync_manager.fetch_remote_app_version()
            if remote_app_ver and is_newer_version(local_app_ver, remote_app_ver):
                logger.info(f"New app version available: {remote_app_ver} (local: {local_app_ver})")
                decision = self.ask_user_update(remote_app_ver)
                if decision == 'update':
                    logger.info("User requested store update. Opening browser...")
                    from modules.common import get_store_url
                    import webbrowser
                    webbrowser.open(get_store_url())
        except Exception as e:
            logger.exception(f"App version check failed: {e}")

        # 2. Get local version
        self.update_ui("正在讀取本地版本...", 20, "")
        local_id = self.sync_manager.get_local_version()
        logger.info(f"Local database version: {local_id}")

        # 3. Fetch updates
        self.update_ui("正在檢查伺服器更新...", 35, "")
        try:
            updates = self.sync_manager.fetch_remote_updates(local_id)
        except Exception as e:
            logger.exception(f"Failed to query updates: {e}")
            self.update_ui("無法連接伺服器，略過更新...", 100, "")
            Clock.schedule_once(lambda dt: self.finish_sync(), 1.5)
            return

        if not updates:
            logger.info("Database is up to date.")
            self.update_ui("資料庫已是最新版本", 100, "")
            Clock.schedule_once(lambda dt: self.finish_sync(), 1.0)
            return

        total_updates = len(updates)
        self.update_ui(f"發現 {total_updates} 個更新檔案...", 40, "")
        
        # 4. Start downloading and processing each update
        for idx, update in enumerate(updates):
            file_name = update['file_name']
            expected_checksum = update['checksum']
            update_type = update['update_type']
            version_id = update['id']
            
            # Progress value scaling from 40% to 95%
            progress_base = 40 + int((idx / total_updates) * 55)
            
            success = False
            while not success:
                # UI status
                self.update_ui(
                    f"正在下載更新 ({idx+1}/{total_updates})...", 
                    progress_base, 
                    f"檔案: {file_name}"
                )
                
                try:
                    data_bytes = self.sync_manager.download_csv_file(file_name)
                except Exception as e:
                    logger.error(f"Download failed for {file_name}: {e}")
                    decision = self.ask_user_retry(file_name)
                    if decision == 'retry':
                        continue
                    else:
                        logger.info("User chose to abort sync on download failure.")
                        self.update_ui("已取消更新，進入 App...", 100, "")
                        Clock.schedule_once(lambda dt: self.finish_sync(), 1.0)
                        return
                
                # Check SHA-256
                self.update_ui(
                    f"正在校驗檔案 ({idx+1}/{total_updates})...", 
                    progress_base + 3, 
                    f"檔案: {file_name}"
                )
                calculated_checksum = calculate_sha256(data_bytes)
                if calculated_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {file_name}. Expected: {expected_checksum}, calculated: {calculated_checksum}")
                    decision = self.ask_user_retry(file_name)
                    if decision == 'retry':
                        continue
                    else:
                        logger.info("User chose to abort sync on checksum mismatch.")
                        self.update_ui("已取消更新，進入 App...", 100, "")
                        Clock.schedule_once(lambda dt: self.finish_sync(), 1.0)
                        return
                
                # Process and write to SQLite
                self.update_ui(
                    f"正在更新資料庫 ({idx+1}/{total_updates})...", 
                    progress_base + 6, 
                    f"檔案: {file_name}"
                )
                try:
                    self.sync_manager.process_csv_data(data_bytes, update_type)
                    # Log successful update to SQLite
                    self.sync_manager.save_version_to_local(version_id)
                    success = True
                except Exception as e:
                    logger.exception(f"Failed to process CSV file {file_name}: {e}")
                    self.update_ui("資料庫寫入失敗，略過其餘更新...", 100, "")
                    Clock.schedule_once(lambda dt: self.finish_sync(), 2.0)
                    return
                    
        # All updates completed
        self.update_ui("更新完成！", 100, "資料庫已成功同步。")
        Clock.schedule_once(lambda dt: self.finish_sync(), 1.0)

    def update_ui(self, status, value, detail=""):
        """Schedule UI update on main Kivy thread."""
        Clock.schedule_once(lambda dt: self.app.update_sync_ui(status, value, detail), 0)
        
    def finish_sync(self):
        """Clean up popups and trigger App reload."""
        self.app.dismiss_sync_popup()
        self.app.reload_history_data()

    def ask_user_update(self, remote_ver):
        """Pause worker thread and request version update popup on main thread."""
        self.event.clear()
        Clock.schedule_once(lambda dt: self.app.show_update_popup(remote_ver, self), 0)
        self.event.wait()
        return self.user_decision

    def ask_user_retry(self, file_name):
        """Pause worker thread and request retry popup on main thread."""
        self.event.clear()
        Clock.schedule_once(lambda dt: self.app.show_retry_popup(file_name, self), 0)
        self.event.wait()
        return self.user_decision

    def set_user_decision(self, decision):
        """Resume worker thread with user selection."""
        self.user_decision = decision
        self.event.set()
