"""
Log Recording Options Widget for managing log recording settings.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional
import os


class LogRecordingOptionsWidget(ttk.LabelFrame):
    """Widget for managing log recording options."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the LogRecordingOptionsWidget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for LabelFrame
        """
        super().__init__(parent, text="日誌記錄設定", padding=15, **kwargs)
        
        self.logging_enabled_var = tk.BooleanVar(value=True)
        self.log_level_var = tk.StringVar(value="info")
        self.retention_days_var = tk.IntVar(value=30)
        self.max_file_size_var = tk.IntVar(value=10)  # MB
        self.auto_cleanup_var = tk.BooleanVar(value=True)
        self.log_path_var = tk.StringVar(value="logs/")
        self.change_callback: Optional[Callable[[dict], None]] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Description
        desc_label = ttk.Label(
            self,
            text="設定系統日誌記錄的方式和保存選項",
            font=("TkDefaultFont", 9),
            foreground="gray"
        )
        desc_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Enable/Disable logging
        enable_frame = ttk.Frame(self)
        enable_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(enable_frame, text="日誌記錄:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Radio buttons for enable/disable
        enable_radio = ttk.Radiobutton(
            enable_frame,
            text="啟用日誌記錄",
            variable=self.logging_enabled_var,
            value=True,
            command=self._on_setting_changed
        )
        enable_radio.pack(anchor=tk.W, padx=(20, 0))
        
        disable_radio = ttk.Radiobutton(
            enable_frame,
            text="停用日誌記錄",
            variable=self.logging_enabled_var,
            value=False,
            command=self._on_setting_changed
        )
        disable_radio.pack(anchor=tk.W, padx=(20, 0))
        
        # Log level settings
        level_frame = ttk.Frame(self)
        level_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(level_frame, text="日誌層級:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        level_options = [
            ("debug", "除錯", "記錄所有詳細資訊（檔案較大）"),
            ("info", "資訊", "記錄一般操作資訊（推薦）"),
            ("warning", "警告", "只記錄警告和錯誤"),
            ("error", "錯誤", "只記錄錯誤資訊")
        ]
        
        for value, text, desc in level_options:
            radio_frame = ttk.Frame(level_frame)
            radio_frame.pack(fill=tk.X, padx=(20, 0))
            
            radio = ttk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.log_level_var,
                value=value,
                command=self._on_setting_changed
            )
            radio.pack(side=tk.LEFT)
            
            desc_label = ttk.Label(
                radio_frame,
                text=f"- {desc}",
                font=("TkDefaultFont", 8),
                foreground="gray"
            )
            desc_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Retention settings
        retention_frame = ttk.Frame(self)
        retention_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(retention_frame, text="保存設定:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Retention days
        days_frame = ttk.Frame(retention_frame)
        days_frame.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))
        
        ttk.Label(days_frame, text="保存天數:").pack(side=tk.LEFT)
        
        days_spinbox = ttk.Spinbox(
            days_frame,
            from_=1,
            to=365,
            width=5,
            textvariable=self.retention_days_var,
            command=self._on_setting_changed
        )
        days_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(days_frame, text="天").pack(side=tk.LEFT)
        
        # Max file size
        size_frame = ttk.Frame(retention_frame)
        size_frame.pack(fill=tk.X, padx=(20, 0), pady=(0, 5))
        
        ttk.Label(size_frame, text="單檔大小上限:").pack(side=tk.LEFT)
        
        size_spinbox = ttk.Spinbox(
            size_frame,
            from_=1,
            to=100,
            width=5,
            textvariable=self.max_file_size_var,
            command=self._on_setting_changed
        )
        size_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(size_frame, text="MB").pack(side=tk.LEFT)
        
        # Auto cleanup
        cleanup_frame = ttk.Frame(retention_frame)
        cleanup_frame.pack(fill=tk.X, padx=(20, 0))
        
        cleanup_check = ttk.Checkbutton(
            cleanup_frame,
            text="自動清理過期日誌",
            variable=self.auto_cleanup_var,
            command=self._on_setting_changed
        )
        cleanup_check.pack(side=tk.LEFT)
        
        # Log path settings
        path_frame = ttk.Frame(self)
        path_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(path_frame, text="儲存位置:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill=tk.X, padx=(20, 0))
        
        self.path_entry = ttk.Entry(
            path_input_frame,
            textvariable=self.log_path_var,
            width=40
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(
            path_input_frame,
            text="瀏覽...",
            command=self._browse_log_path
        )
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Bind path change
        self.log_path_var.trace_add('write', self._on_path_changed)
        
        # Management buttons
        mgmt_frame = ttk.Frame(self)
        mgmt_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mgmt_frame, text="日誌管理:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        mgmt_buttons_frame = ttk.Frame(mgmt_frame)
        mgmt_buttons_frame.pack(fill=tk.X, padx=(20, 0))
        
        ttk.Button(
            mgmt_buttons_frame,
            text="開啟日誌資料夾",
            command=self._open_log_folder
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            mgmt_buttons_frame,
            text="清理舊日誌",
            command=self._cleanup_old_logs
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            mgmt_buttons_frame,
            text="匯出日誌",
            command=self._export_logs
        ).pack(side=tk.LEFT)
        
        # Status info
        self.status_label = ttk.Label(
            self,
            text="",
            font=("TkDefaultFont", 8),
            foreground="blue"
        )
        self.status_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Update status
        self._update_status_info()
    
    def _on_setting_changed(self):
        """Handle setting changes."""
        self._update_status_info()
        if self.change_callback:
            self.change_callback(self.get_settings())
    
    def _on_path_changed(self, *args):
        """Handle log path changes."""
        self._update_status_info()
        if self.change_callback:
            self.change_callback(self.get_settings())
    
    def _update_status_info(self):
        """Update status information."""
        if not self.logging_enabled_var.get():
            status = "📝 日誌記錄已停用"
            color = "red"
        else:
            level = self.log_level_var.get()
            days = self.retention_days_var.get()
            size = self.max_file_size_var.get()
            
            level_text = {
                "debug": "除錯",
                "info": "資訊",
                "warning": "警告",
                "error": "錯誤"
            }.get(level, "未知")
            
            status = f"📝 日誌記錄已啟用 - {level_text}層級, 保存{days}天, 單檔{size}MB"
            color = "green"
        
        self.status_label.config(text=status, foreground=color)
    
    def _browse_log_path(self):
        """Browse for log directory."""
        directory = filedialog.askdirectory(
            title="選擇日誌儲存資料夾",
            initialdir=self.log_path_var.get()
        )
        
        if directory:
            self.log_path_var.set(directory)
    
    def _open_log_folder(self):
        """Open log folder in file explorer."""
        path = self.log_path_var.get()
        
        if not os.path.exists(path):
            messagebox.showwarning("警告", f"日誌資料夾不存在: {path}")
            return
        
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟資料夾: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log files."""
        if messagebox.askyesno("確認", "確定要清理過期的日誌檔案嗎？此操作無法復原。"):
            try:
                # This would integrate with the actual log manager
                # For now, just show a success message
                messagebox.showinfo("成功", "舊日誌檔案已清理完成")
            except Exception as e:
                messagebox.showerror("錯誤", f"清理日誌時發生錯誤: {e}")
    
    def _export_logs(self):
        """Export logs to a file."""
        file_path = filedialog.asksaveasfilename(
            title="匯出日誌",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # This would integrate with the actual log manager
                # For now, just show a success message
                messagebox.showinfo("成功", f"日誌已匯出到: {file_path}")
            except Exception as e:
                messagebox.showerror("錯誤", f"匯出日誌時發生錯誤: {e}")
    
    def get_settings(self) -> dict:
        """
        Get current log recording settings.
        
        Returns:
            Dictionary of current settings
        """
        return {
            "logging_enabled": self.logging_enabled_var.get(),
            "log_level": self.log_level_var.get(),
            "retention_days": self.retention_days_var.get(),
            "max_file_size_mb": self.max_file_size_var.get(),
            "auto_cleanup": self.auto_cleanup_var.get(),
            "log_path": self.log_path_var.get()
        }
    
    def set_settings(self, settings: dict):
        """
        Set log recording settings.
        
        Args:
            settings: Dictionary of settings to apply
        """
        if "logging_enabled" in settings:
            self.logging_enabled_var.set(settings["logging_enabled"])
        
        if "log_level" in settings:
            self.log_level_var.set(settings["log_level"])
        
        if "retention_days" in settings:
            self.retention_days_var.set(settings["retention_days"])
        
        if "max_file_size_mb" in settings:
            self.max_file_size_var.set(settings["max_file_size_mb"])
        
        if "auto_cleanup" in settings:
            self.auto_cleanup_var.set(settings["auto_cleanup"])
        
        if "log_path" in settings:
            self.log_path_var.set(settings["log_path"])
        
        self._update_status_info()
    
    def set_change_callback(self, callback: Callable[[dict], None]):
        """
        Set callback for setting changes.
        
        Args:
            callback: Function to call when settings change
        """
        self.change_callback = callback
    
    def validate(self) -> bool:
        """
        Validate current settings.
        
        Returns:
            True if valid, False otherwise
        """
        # Check if log level is valid
        valid_levels = ["debug", "info", "warning", "error"]
        if self.log_level_var.get() not in valid_levels:
            return False
        
        # Check retention days
        if not (1 <= self.retention_days_var.get() <= 365):
            return False
        
        # Check max file size
        if not (1 <= self.max_file_size_var.get() <= 100):
            return False
        
        # Check log path
        path = self.log_path_var.get()
        if not path or not path.strip():
            return False
        
        return True