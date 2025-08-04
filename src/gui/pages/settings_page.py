"""
Modern Settings page implementation with widget components.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List  # Fixed import

from src.gui.page_manager import BasePage
from src.core.config_manager import get_config_manager, ConfigObserver
from src.models.config import AppConfig
import logging


class SettingsPage(BasePage, ConfigObserver):
    """Modern settings page with specialized widget components."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize settings page."""
        super().__init__(parent, "Settings", "系統設定")
        self.config_manager = get_config_manager()
        self.config_manager.add_observer(self)
        self._updating = False
        self.logger = logging.getLogger(__name__)
        
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
        """
        Save all settings with comprehensive validation and error handling.
        """
        try:
            # Step 1: Validate all settings
            if not self._validate_all_settings():
                return  # Validation errors already shown
            
            # Step 2: Collect settings from all widgets
            updates = self._collect_all_settings()
            if not updates:
                messagebox.showwarning("警告", "沒有設定需要儲存")
                return
            
            # Step 3: Apply settings with rollback capability
            old_config = self.config_manager.get_config()
            success = self._apply_settings_with_rollback(updates)
            
            if success:
                # Step 4: Apply immediate changes (restart services if needed)
                self._apply_immediate_changes(updates, old_config)
                messagebox.showinfo("成功", "設定已儲存並應用")
            else:
                messagebox.showerror("錯誤", "無法儲存設定，已回復到原始狀態")
                
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤: {e}")
    
    def _collect_all_settings(self) -> Dict[str, Any]:
        """
        Collect all settings from widgets.
        
        Returns:
            Dict containing all current settings
        """
        updates = {}
        
        try:
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
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Error collecting settings: {e}")
            return {}
    
    def _apply_settings_with_rollback(self, updates: Dict[str, Any]) -> bool:
        """
        Apply settings with rollback capability.
        
        Args:
            updates: Settings to apply
            
        Returns:
            bool: True if all settings applied successfully
        """
        # Store original values for rollback
        original_values = {}
        applied_keys = []
        
        try:
            # Apply each setting
            for key, value in updates.items():
                original_values[key] = self.config_manager.get_setting(key)
                if self.config_manager.set_setting(key, value, save_immediately=False):
                    applied_keys.append(key)
                else:
                    raise ValueError(f"Failed to set {key} to {value}")
            
            # Save configuration
            if self.config_manager.save_config():
                self.logger.info(f"Successfully applied {len(applied_keys)} settings")
                return True
            else:
                raise ValueError("Failed to save configuration")
                
        except Exception as e:
            self.logger.error(f"Error applying settings, rolling back: {e}")
            
            # Rollback applied settings
            for key in applied_keys:
                if key in original_values:
                    self.config_manager.set_setting(key, original_values[key], save_immediately=False)
            
            return False
    
    def _apply_immediate_changes(self, updates: Dict[str, Any], old_config) -> None:
        """
        Apply changes that require immediate action.
        
        Args:
            updates: Applied settings
            old_config: Previous configuration
        """
        try:
            restart_required = []
            
            # Check for settings that require service restart
            critical_settings = [
                "schedule_check_frequency",
                "log_recording_enabled", 
                "debug_mode"
            ]
            
            for setting in critical_settings:
                if setting in updates:
                    old_value = getattr(old_config, setting, None)
                    new_value = updates[setting]
                    if old_value != new_value:
                        restart_required.append(setting)
            
            # Notify about restart requirements
            if restart_required:
                restart_msg = "以下設定變更需要重新啟動服務才能生效：\n\n"
                restart_msg += "\n".join(f"• {self._get_setting_display_name(setting)}" for setting in restart_required)
                restart_msg += "\n\n是否要立即重新啟動相關服務？"
                
                if messagebox.askyesno("重新啟動服務", restart_msg):
                    self._restart_services(restart_required)
            
        except Exception as e:
            self.logger.error(f"Error applying immediate changes: {e}")
    
    def _restart_services(self, settings: List[str]) -> None:
        """
        Restart services affected by setting changes.
        
        Args:
            settings: List of changed settings
        """
        try:
            # Import scheduler engine if available
            from src.core.scheduler_engine import get_scheduler_engine
            
            scheduler = get_scheduler_engine()
            
            if "schedule_check_frequency" in settings:
                # Restart scheduler with new frequency
                if hasattr(scheduler, 'restart'):
                    scheduler.restart()
                    self.logger.info("Scheduler restarted with new frequency")
            
            if "log_recording_enabled" in settings or "debug_mode" in settings:
                # Reconfigure logging
                if hasattr(scheduler, 'reconfigure_logging'):
                    scheduler.reconfigure_logging()
                    self.logger.info("Logging reconfigured")
            
        except ImportError:
            self.logger.warning("Scheduler engine not available for restart")
        except Exception as e:
            self.logger.error(f"Error restarting services: {e}")
            messagebox.showwarning("警告", f"重新啟動服務時發生錯誤: {e}")
    
    def _get_setting_display_name(self, setting_key: str) -> str:
        """
        Get display name for setting key.
        
        Args:
            setting_key: Internal setting key
            
        Returns:
            User-friendly display name
        """
        display_names = {
            "schedule_check_frequency": "排程檢查頻率",
            "log_recording_enabled": "日誌記錄",
            "debug_mode": "除錯模式",
            "notifications_enabled": "通知設定",
            "max_retry_attempts": "最大重試次數"
        }
        return display_names.get(setting_key, setting_key)
    
    def _create_temp_config(self) -> Optional[AppConfig]:
        """
        Create temporary config for validation.
        
        Returns:
            Temporary AppConfig instance or None if creation fails
        """
        try:
            current_config = self.config_manager.get_config()
            updates = self._collect_all_settings()
            
            # Create a copy of current config
            temp_config_dict = current_config.to_dict()
            
            # Apply updates
            for key, value in updates.items():
                if key in temp_config_dict:
                    temp_config_dict[key] = value
            
            # Create and return temporary config
            return AppConfig.from_dict(temp_config_dict)
            
        except Exception as e:
            self.logger.error(f"Error creating temporary config: {e}")
            return None
    
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
        """
        Validate all settings before saving.
        
        Returns:
            bool: True if all settings are valid
        """
        validation_errors = []
        
        try:
            # Validate schedule frequency
            if self.schedule_frequency_widget:
                if hasattr(self.schedule_frequency_widget, 'validate'):
                    if not self.schedule_frequency_widget.validate():
                        validation_errors.append("排程檢查頻率設定無效")
                else:
                    # Fallback validation
                    frequency = self.schedule_frequency_widget.get_frequency()
                    if not (1 <= frequency <= 3600):  # 1 second to 1 hour
                        validation_errors.append("排程檢查頻率必須在 1-3600 秒之間")
            
            # Validate notification settings
            if self.notification_options_widget:
                if hasattr(self.notification_options_widget, 'validate'):
                    if not self.notification_options_widget.validate():
                        validation_errors.append("通知設定無效")
            
            # Validate logging settings
            if self.log_recording_widget:
                if hasattr(self.log_recording_widget, 'validate'):
                    if not self.log_recording_widget.validate():
                        validation_errors.append("日誌記錄設定無效")
                else:
                    # Fallback validation
                    log_settings = self.log_recording_widget.get_settings()
                    retention_days = log_settings.get("retention_days", 30)
                    if not (1 <= retention_days <= 365):
                        validation_errors.append("日誌保留天數必須在 1-365 天之間")
            
            # Validate additional settings
            if "max_retry_attempts" in self.additional_widgets:
                try:
                    retry_attempts = int(self.additional_widgets["max_retry_attempts"].get())
                    if not (0 <= retry_attempts <= 10):
                        validation_errors.append("最大重試次數必須在 0-10 次之間")
                except ValueError:
                    validation_errors.append("最大重試次數必須是有效的數字")
            
            # Create a temporary config to validate overall consistency
            temp_config = self._create_temp_config()
            if temp_config and not temp_config.validate():
                validation_errors.append("整體設定配置無效")
            
            # Show validation errors if any
            if validation_errors:
                error_message = "設定驗證失敗：\n\n" + "\n".join(f"• {error}" for error in validation_errors)
                messagebox.showerror("驗證錯誤", error_message)
                return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("驗證錯誤", f"驗證設定時發生錯誤: {e}")
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