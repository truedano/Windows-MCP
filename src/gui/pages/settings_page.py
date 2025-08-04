"""
Settings page implementation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any

from src.gui.page_manager import BasePage
from src.core.config_manager import get_config_manager, ConfigObserver
from src.models.config import AppConfig


class SettingsPage(BasePage, ConfigObserver):
    """System settings page with configuration management."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize settings page."""
        super().__init__(parent, "Settings", "系統設定")
        self.config_manager = get_config_manager()
        self.config_manager.add_observer(self)
        self.widgets: Dict[str, tk.Widget] = {}
        self._updating = False
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="System Settings",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="配置應用程式設定和偏好",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Create notebook for different setting categories
        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # General settings tab
        self._create_general_tab(notebook)
        
        # UI settings tab
        self._create_ui_tab(notebook)
        
        # Advanced settings tab
        self._create_advanced_tab(notebook)
        
        # Action buttons
        self._create_action_buttons()
        
        # Load current settings
        self._load_settings()
    
    def _create_general_tab(self, notebook: ttk.Notebook) -> None:
        """Create general settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="一般設定")
        
        # Schedule check frequency
        freq_frame = ttk.LabelFrame(frame, text="排程檢查頻率", padding=10)
        freq_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(freq_frame, text="檢查間隔 (秒):").pack(anchor=tk.W)
        freq_var = tk.IntVar()
        freq_spinbox = ttk.Spinbox(
            freq_frame, from_=1, to=60, textvariable=freq_var, width=10
        )
        freq_spinbox.pack(anchor=tk.W, pady=(5, 0))
        self.widgets["schedule_check_frequency"] = freq_var
        
        # Notifications
        notif_frame = ttk.LabelFrame(frame, text="通知設定", padding=10)
        notif_frame.pack(fill=tk.X, padx=10, pady=5)
        
        notif_var = tk.BooleanVar()
        notif_check = ttk.Checkbutton(
            notif_frame, text="啟用通知", variable=notif_var
        )
        notif_check.pack(anchor=tk.W)
        self.widgets["notifications_enabled"] = notif_var
        
        # Logging
        log_frame = ttk.LabelFrame(frame, text="日誌設定", padding=10)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        log_var = tk.BooleanVar()
        log_check = ttk.Checkbutton(
            log_frame, text="啟用日誌記錄", variable=log_var
        )
        log_check.pack(anchor=tk.W)
        self.widgets["log_recording_enabled"] = log_var
        
        ttk.Label(log_frame, text="日誌保留天數:").pack(anchor=tk.W, pady=(10, 0))
        retention_var = tk.IntVar()
        retention_spinbox = ttk.Spinbox(
            log_frame, from_=1, to=365, textvariable=retention_var, width=10
        )
        retention_spinbox.pack(anchor=tk.W, pady=(5, 0))
        self.widgets["log_retention_days"] = retention_var
    
    def _create_ui_tab(self, notebook: ttk.Notebook) -> None:
        """Create UI settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="介面設定")
        
        # Theme settings
        theme_frame = ttk.LabelFrame(frame, text="介面主題", padding=10)
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(theme_frame, text="主題:").pack(anchor=tk.W)
        theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(
            theme_frame, textvariable=theme_var, 
            values=["default", "dark", "light"], state="readonly", width=15
        )
        theme_combo.pack(anchor=tk.W, pady=(5, 0))
        self.widgets["ui_theme"] = theme_var
        
        # Language settings
        lang_frame = ttk.LabelFrame(frame, text="語言設定", padding=10)
        lang_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(lang_frame, text="語言:").pack(anchor=tk.W)
        lang_var = tk.StringVar()
        lang_combo = ttk.Combobox(
            lang_frame, textvariable=lang_var,
            values=["zh-TW", "zh-CN", "en-US"], state="readonly", width=15
        )
        lang_combo.pack(anchor=tk.W, pady=(5, 0))
        self.widgets["language"] = lang_var
        
        # Window settings
        window_frame = ttk.LabelFrame(frame, text="視窗設定", padding=10)
        window_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(window_frame, text="預設寬度:").pack(anchor=tk.W)
        width_var = tk.IntVar()
        width_spinbox = ttk.Spinbox(
            window_frame, from_=800, to=3840, textvariable=width_var, width=10
        )
        width_spinbox.pack(anchor=tk.W, pady=(5, 0))
        self.widgets["window_width"] = width_var
        
        ttk.Label(window_frame, text="預設高度:").pack(anchor=tk.W, pady=(10, 0))
        height_var = tk.IntVar()
        height_spinbox = ttk.Spinbox(
            window_frame, from_=600, to=2160, textvariable=height_var, width=10
        )
        height_spinbox.pack(anchor=tk.W, pady=(5, 0))
        self.widgets["window_height"] = height_var
    
    def _create_advanced_tab(self, notebook: ttk.Notebook) -> None:
        """Create advanced settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="進階設定")
        
        # Retry settings
        retry_frame = ttk.LabelFrame(frame, text="重試設定", padding=10)
        retry_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(retry_frame, text="最大重試次數:").pack(anchor=tk.W)
        retry_var = tk.IntVar()
        retry_spinbox = ttk.Spinbox(
            retry_frame, from_=0, to=10, textvariable=retry_var, width=10
        )
        retry_spinbox.pack(anchor=tk.W, pady=(5, 0))
        self.widgets["max_retry_attempts"] = retry_var
        
        # Startup settings
        startup_frame = ttk.LabelFrame(frame, text="啟動設定", padding=10)
        startup_frame.pack(fill=tk.X, padx=10, pady=5)
        
        auto_start_var = tk.BooleanVar()
        auto_start_check = ttk.Checkbutton(
            startup_frame, text="自動啟動排程器", variable=auto_start_var
        )
        auto_start_check.pack(anchor=tk.W)
        self.widgets["auto_start_scheduler"] = auto_start_var
        
        minimize_var = tk.BooleanVar()
        minimize_check = ttk.Checkbutton(
            startup_frame, text="最小化到系統匣", variable=minimize_var
        )
        minimize_check.pack(anchor=tk.W)
        self.widgets["minimize_to_tray"] = minimize_var
        
        splash_var = tk.BooleanVar()
        splash_check = ttk.Checkbutton(
            startup_frame, text="顯示啟動畫面", variable=splash_var
        )
        splash_check.pack(anchor=tk.W)
        self.widgets["show_splash_screen"] = splash_var
        
        debug_var = tk.BooleanVar()
        debug_check = ttk.Checkbutton(
            startup_frame, text="除錯模式", variable=debug_var
        )
        debug_check.pack(anchor=tk.W)
        self.widgets["debug_mode"] = debug_var
    
    def _create_action_buttons(self) -> None:
        """Create action buttons."""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Save button
        save_btn = ttk.Button(
            button_frame, text="儲存設定", command=self._save_settings
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Reset button
        reset_btn = ttk.Button(
            button_frame, text="重設為預設值", command=self._reset_settings
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        export_btn = ttk.Button(
            button_frame, text="匯出設定", command=self._export_settings
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Import button
        import_btn = ttk.Button(
            button_frame, text="匯入設定", command=self._import_settings
        )
        import_btn.pack(side=tk.LEFT, padx=5)
    
    def _load_settings(self) -> None:
        """Load current settings into widgets."""
        self._updating = True
        try:
            config = self.config_manager.get_config()
            
            for key, widget in self.widgets.items():
                value = getattr(config, key, None)
                if value is not None:
                    widget.set(value)
        finally:
            self._updating = False
    
    def _save_settings(self) -> None:
        """Save current settings."""
        try:
            # Collect values from widgets
            updates = {}
            for key, widget in self.widgets.items():
                updates[key] = widget.get()
            
            # Apply updates
            for key, value in updates.items():
                success = self.config_manager.set_setting(key, value, save_immediately=False)
                if not success:
                    messagebox.showerror("錯誤", f"無法設定 {key}: 值無效")
                    self._load_settings()  # Reload original values
                    return
            
            # Save configuration
            if self.config_manager.save_config():
                messagebox.showinfo("成功", "設定已儲存")
            else:
                messagebox.showerror("錯誤", "無法儲存設定")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤: {e}")
    
    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
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
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if not self._updating:
            self._load_settings()
    
    def on_config_changed(self, setting_key: str, old_value, new_value) -> None:
        """Handle configuration changes from other sources."""
        if not self._updating and setting_key in self.widgets:
            self.widgets[setting_key].set(new_value)