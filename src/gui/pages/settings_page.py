"""
Modern Settings page implementation with widget components.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional

from src.gui.page_manager import BasePage
from src.core.config_manager import get_config_manager, ConfigObserver
from src.models.config import AppConfig


class SettingsPage(BasePage, ConfigObserver):
    """Modern settings page with specialized widget components."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize settings page."""
        super().__init__(parent, "Settings", "系統設定")
        self.config_manager = get_config_manager()
        self.config_manager.add_observer(self)
        self._updating = False
        
        # Widget references
        self.schedule_frequency_widget: Optional[Any] = None
        self.notification_options_widget: Optional[Any] = None
        self.log_recording_widget: Optional[Any] = None
        self.additional_widgets: Dict[str, tk.Widget] = {}
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="Settings",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="配置應用程式設定和偏好",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(5, 20))
        
        # Create main content frame with scrollable area
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Import the new widgets
        from ..widgets import ScheduleFrequencyWidget, NotificationOptionsWidget, LogRecordingOptionsWidget
        
        # Schedule Frequency Widget
        self.schedule_frequency_widget = ScheduleFrequencyWidget(main_frame)
        self.schedule_frequency_widget.pack(fill=tk.X, pady=(0, 15))
        self.schedule_frequency_widget.set_change_callback(self._on_frequency_changed)
        
        # Notification Options Widget
        self.notification_options_widget = NotificationOptionsWidget(main_frame)
        self.notification_options_widget.pack(fill=tk.X, pady=(0, 15))
        self.notification_options_widget.set_change_callback(self._on_notification_changed)
        
        # Log Recording Options Widget
        self.log_recording_widget = LogRecordingOptionsWidget(main_frame)
        self.log_recording_widget.pack(fill=tk.X, pady=(0, 15))
        self.log_recording_widget.set_change_callback(self._on_logging_changed)
        
        # Additional settings section
        self._create_additional_settings(main_frame)
        
        # Action buttons
        self._create_action_buttons()
        
        # Load current settings
        self._load_settings()
    
    def _create_additional_settings(self, parent: ttk.Frame):
        """Create additional settings section."""
        # Advanced settings frame
        advanced_frame = ttk.LabelFrame(parent, text="進階設定", padding=15)
        advanced_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Retry settings
        retry_frame = ttk.Frame(advanced_frame)
        retry_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(retry_frame, text="最大重試次數:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        retry_input_frame = ttk.Frame(retry_frame)
        retry_input_frame.pack(fill=tk.X, padx=(20, 0))
        
        self.additional_widgets["max_retry_attempts"] = ttk.Spinbox(
            retry_input_frame,
            from_=0,
            to=10,
            width=5,
            value=3
        )
        self.additional_widgets["max_retry_attempts"].pack(side=tk.LEFT)
        
        ttk.Label(retry_input_frame, text="次").pack(side=tk.LEFT, padx=(5, 0))
        
        # Startup settings
        startup_frame = ttk.Frame(advanced_frame)
        startup_frame.pack(fill=tk.X)
        
        ttk.Label(startup_frame, text="啟動選項:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        startup_options_frame = ttk.Frame(startup_frame)
        startup_options_frame.pack(fill=tk.X, padx=(20, 0))
        
        self.additional_widgets["auto_start_scheduler"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            startup_options_frame,
            text="自動啟動排程器",
            variable=self.additional_widgets["auto_start_scheduler"]
        ).pack(anchor=tk.W)
        
        self.additional_widgets["minimize_to_tray"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            startup_options_frame,
            text="最小化到系統匣",
            variable=self.additional_widgets["minimize_to_tray"]
        ).pack(anchor=tk.W)
        
        self.additional_widgets["debug_mode"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            startup_options_frame,
            text="除錯模式",
            variable=self.additional_widgets["debug_mode"]
        ).pack(anchor=tk.W)
    
    def _create_action_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Save button (primary action)
        save_button = ttk.Button(
            button_frame, 
            text="儲存設定", 
            command=self._save_settings
        )
        save_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Reset button
        ttk.Button(
            button_frame, 
            text="重設為預設值", 
            command=self._reset_settings
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Export button
        ttk.Button(
            button_frame, 
            text="匯出設定", 
            command=self._export_settings
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Import button
        ttk.Button(
            button_frame, 
            text="匯入設定", 
            command=self._import_settings
        ).pack(side=tk.RIGHT)
    
    def _on_frequency_changed(self, frequency: int):
        """Handle frequency setting changes."""
        if not self._updating:
            try:
                self.config_manager.set_setting("schedule_check_frequency", frequency)
            except Exception as e:
                messagebox.showerror("錯誤", f"無法更新排程頻率: {e}")
    
    def _on_notification_changed(self, settings: dict):
        """Handle notification setting changes."""
        if not self._updating:
            try:
                self.config_manager.set_setting("notifications_enabled", settings.get("notifications_enabled", True))
                # Store additional notification settings if needed
                for key, value in settings.items():
                    if key.startswith("notification_"):
                        self.config_manager.set_setting(key, value)
            except Exception as e:
                messagebox.showerror("錯誤", f"無法更新通知設定: {e}")
    
    def _on_logging_changed(self, settings: dict):
        """Handle logging setting changes."""
        if not self._updating:
            try:
                self.config_manager.set_setting("log_recording_enabled", settings.get("logging_enabled", True))
                if "retention_days" in settings:
                    self.config_manager.set_setting("log_retention_days", settings["retention_days"])
                # Store additional logging settings
                for key, value in settings.items():
                    if key.startswith("log_"):
                        self.config_manager.set_setting(key, value)
            except Exception as e:
                messagebox.showerror("錯誤", f"無法更新日誌設定: {e}")
    
    def _load_settings(self) -> None:
        """Load current settings into widgets."""
        self._updating = True
        try:
            config = self.config_manager.get_config()
            
            # Load schedule frequency
            if self.schedule_frequency_widget:
                self.schedule_frequency_widget.set_frequency(config.schedule_check_frequency)
            
            # Load notification settings
            if self.notification_options_widget:
                notification_settings = {
                    "notifications_enabled": config.notifications_enabled,
                    "notification_level": getattr(config, "notification_level", "all"),
                    "sound_enabled": getattr(config, "notification_sound_enabled", True)
                }
                self.notification_options_widget.set_settings(notification_settings)
            
            # Load logging settings
            if self.log_recording_widget:
                logging_settings = {
                    "logging_enabled": config.log_recording_enabled,
                    "log_level": getattr(config, "log_level", "info"),
                    "retention_days": config.log_retention_days,
                    "max_file_size_mb": getattr(config, "max_log_file_size_mb", 10),
                    "auto_cleanup": getattr(config, "auto_cleanup_logs", True),
                    "log_path": getattr(config, "log_path", "logs/")
                }
                self.log_recording_widget.set_settings(logging_settings)
            
            # Load additional settings
            if "max_retry_attempts" in self.additional_widgets:
                self.additional_widgets["max_retry_attempts"].set(config.max_retry_attempts)
            
            if "auto_start_scheduler" in self.additional_widgets:
                self.additional_widgets["auto_start_scheduler"].set(config.auto_start_scheduler)
            
            if "minimize_to_tray" in self.additional_widgets:
                self.additional_widgets["minimize_to_tray"].set(config.minimize_to_tray)
            
            if "debug_mode" in self.additional_widgets:
                self.additional_widgets["debug_mode"].set(config.debug_mode)
                
        except Exception as e:
            messagebox.showerror("錯誤", f"載入設定時發生錯誤: {e}")
        finally:
            self._updating = False
    
    def _save_settings(self) -> None:
        """Save all settings."""
        try:
            # Validate all widgets
            if not self._validate_all_settings():
                messagebox.showerror("錯誤", "設定驗證失敗，請檢查輸入值")
                return
            
            # Collect settings from all widgets
            updates = {}
            
            # Schedule frequency
            if self.schedule_frequency_widget:
                updates["schedule_check_frequency"] = self.schedule_frequency_widget.get_frequency()
            
            # Notification settings
            if self.notification_options_widget:
                notif_settings = self.notification_options_widget.get_settings()
                updates["notifications_enabled"] = notif_settings.get("notifications_enabled", True)
                # Store additional notification settings
                for key, value in notif_settings.items():
                    if key != "notifications_enabled":
                        updates[f"notification_{key}"] = value
            
            # Logging settings
            if self.log_recording_widget:
                log_settings = self.log_recording_widget.get_settings()
                updates["log_recording_enabled"] = log_settings.get("logging_enabled", True)
                updates["log_retention_days"] = log_settings.get("retention_days", 30)
                # Store additional logging settings
                for key, value in log_settings.items():
                    if key not in ["logging_enabled", "retention_days"]:
                        updates[f"log_{key}"] = value
            
            # Additional settings
            if "max_retry_attempts" in self.additional_widgets:
                updates["max_retry_attempts"] = int(self.additional_widgets["max_retry_attempts"].get())
            
            if "auto_start_scheduler" in self.additional_widgets:
                updates["auto_start_scheduler"] = self.additional_widgets["auto_start_scheduler"].get()
            
            if "minimize_to_tray" in self.additional_widgets:
                updates["minimize_to_tray"] = self.additional_widgets["minimize_to_tray"].get()
            
            if "debug_mode" in self.additional_widgets:
                updates["debug_mode"] = self.additional_widgets["debug_mode"].get()
            
            # Apply updates
            for key, value in updates.items():
                self.config_manager.set_setting(key, value)
            
            # Save configuration
            if self.config_manager.save_config():
                messagebox.showinfo("成功", "設定已儲存")
            else:
                messagebox.showerror("錯誤", "無法儲存設定")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤: {e}")
    
    def _reset_settings(self) -> None:
        """Reset all settings to defaults."""
        if messagebox.askyesno("確認", "確定要重設所有設定為預設值嗎？"):
            try:
                if self.config_manager.reset_to_defaults():
                    self._load_settings()
                    messagebox.showinfo("成功", "設定已重設為預設值")
                else:
                    messagebox.showerror("錯誤", "無法重設設定")
            except Exception as e:
                messagebox.showerror("錯誤", f"重設設定時發生錯誤: {e}")
    
    def _export_settings(self) -> None:
        """Export settings to file."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="匯出設定",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                if self.config_manager.export_config(file_path):
                    messagebox.showinfo("成功", f"設定已匯出到 {file_path}")
                else:
                    messagebox.showerror("錯誤", "無法匯出設定")
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出設定時發生錯誤: {e}")
    
    def _import_settings(self) -> None:
        """Import settings from file."""
        try:
            file_path = filedialog.askopenfilename(
                title="匯入設定",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                if messagebox.askyesno("確認", "匯入設定將覆蓋目前的設定，確定要繼續嗎？"):
                    if self.config_manager.import_config(file_path):
                        self._load_settings()
                        messagebox.showinfo("成功", f"設定已從 {file_path} 匯入")
                    else:
                        messagebox.showerror("錯誤", "無法匯入設定")
                        
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入設定時發生錯誤: {e}")
    
    def _validate_all_settings(self) -> bool:
        """Validate all settings."""
        try:
            # Validate schedule frequency
            if self.schedule_frequency_widget and not self.schedule_frequency_widget.validate():
                return False
            
            # Validate notification settings
            if self.notification_options_widget and not self.notification_options_widget.validate():
                return False
            
            # Validate logging settings
            if self.log_recording_widget and not self.log_recording_widget.validate():
                return False
            
            # Validate additional settings
            if "max_retry_attempts" in self.additional_widgets:
                try:
                    retry_attempts = int(self.additional_widgets["max_retry_attempts"].get())
                    if not (0 <= retry_attempts <= 10):
                        return False
                except ValueError:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if not self._updating:
            self._load_settings()
    
    def on_config_changed(self, setting_key: str, old_value, new_value) -> None:
        """Handle configuration changes from other sources."""
        if not self._updating:
            # Reload settings to reflect external changes
            self._load_settings()
    
    def destroy(self):
        """Clean up resources when page is destroyed."""
        if hasattr(self, 'config_manager'):
            self.config_manager.remove_observer(self)
        super().destroy()