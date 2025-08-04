"""
Notification Options Widget for controlling notification settings.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class NotificationOptionsWidget(ttk.LabelFrame):
    """Widget for managing notification options."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the NotificationOptionsWidget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for LabelFrame
        """
        super().__init__(parent, text="通知選項", padding=15, **kwargs)
        
        self.notifications_enabled_var = tk.BooleanVar(value=True)
        self.notification_level_var = tk.StringVar(value="all")
        self.sound_enabled_var = tk.BooleanVar(value=True)
        self.change_callback: Optional[Callable[[dict], None]] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Description
        desc_label = ttk.Label(
            self,
            text="設定系統通知的顯示方式和內容",
            font=("TkDefaultFont", 9),
            foreground="gray"
        )
        desc_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Enable/Disable notifications
        enable_frame = ttk.Frame(self)
        enable_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(enable_frame, text="通知狀態:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Radio buttons for enable/disable
        enable_radio = ttk.Radiobutton(
            enable_frame,
            text="啟用通知",
            variable=self.notifications_enabled_var,
            value=True,
            command=self._on_setting_changed
        )
        enable_radio.pack(anchor=tk.W, padx=(20, 0))
        
        disable_radio = ttk.Radiobutton(
            enable_frame,
            text="停用通知",
            variable=self.notifications_enabled_var,
            value=False,
            command=self._on_setting_changed
        )
        disable_radio.pack(anchor=tk.W, padx=(20, 0))
        
        # Notification level settings
        level_frame = ttk.Frame(self)
        level_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(level_frame, text="通知層級:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        level_options = [
            ("all", "所有通知", "顯示成功、警告和錯誤通知"),
            ("warnings_errors", "警告和錯誤", "只顯示警告和錯誤通知"),
            ("errors_only", "僅錯誤", "只顯示錯誤通知")
        ]
        
        for value, text, desc in level_options:
            radio_frame = ttk.Frame(level_frame)
            radio_frame.pack(fill=tk.X, padx=(20, 0))
            
            radio = ttk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.notification_level_var,
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
        
        # Sound settings
        sound_frame = ttk.Frame(self)
        sound_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sound_frame, text="音效設定:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        sound_check = ttk.Checkbutton(
            sound_frame,
            text="播放通知音效",
            variable=self.sound_enabled_var,
            command=self._on_setting_changed
        )
        sound_check.pack(anchor=tk.W, padx=(20, 0))
        
        # Preview section
        preview_frame = ttk.Frame(self)
        preview_frame.pack(fill=tk.X)
        
        ttk.Label(preview_frame, text="測試通知:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        test_buttons_frame = ttk.Frame(preview_frame)
        test_buttons_frame.pack(fill=tk.X, padx=(20, 0))
        
        ttk.Button(
            test_buttons_frame,
            text="測試成功通知",
            command=lambda: self._test_notification("success")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            test_buttons_frame,
            text="測試警告通知",
            command=lambda: self._test_notification("warning")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            test_buttons_frame,
            text="測試錯誤通知",
            command=lambda: self._test_notification("error")
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
    
    def _update_status_info(self):
        """Update status information."""
        if not self.notifications_enabled_var.get():
            status = "🔕 通知已停用"
            color = "red"
        else:
            level = self.notification_level_var.get()
            sound = "有音效" if self.sound_enabled_var.get() else "無音效"
            
            level_text = {
                "all": "所有通知",
                "warnings_errors": "警告和錯誤",
                "errors_only": "僅錯誤"
            }.get(level, "未知")
            
            status = f"🔔 通知已啟用 - {level_text}, {sound}"
            color = "green"
        
        self.status_label.config(text=status, foreground=color)
    
    def _test_notification(self, notification_type: str):
        """
        Test notification display.
        
        Args:
            notification_type: Type of notification to test
        """
        if not self.notifications_enabled_var.get():
            tk.messagebox.showinfo("測試通知", "通知功能已停用，無法測試")
            return
        
        level = self.notification_level_var.get()
        
        # Check if this notification type should be shown
        should_show = False
        if level == "all":
            should_show = True
        elif level == "warnings_errors" and notification_type in ["warning", "error"]:
            should_show = True
        elif level == "errors_only" and notification_type == "error":
            should_show = True
        
        if should_show:
            messages = {
                "success": ("測試成功通知", "這是一個成功通知的範例"),
                "warning": ("測試警告通知", "這是一個警告通知的範例"),
                "error": ("測試錯誤通知", "這是一個錯誤通知的範例")
            }
            
            title, message = messages.get(notification_type, ("測試通知", "測試訊息"))
            
            if notification_type == "error":
                tk.messagebox.showerror(title, message)
            elif notification_type == "warning":
                tk.messagebox.showwarning(title, message)
            else:
                tk.messagebox.showinfo(title, message)
            
            # Simulate sound if enabled
            if self.sound_enabled_var.get():
                try:
                    # Try to play system sound
                    import winsound
                    if notification_type == "error":
                        winsound.MessageBeep(winsound.MB_ICONHAND)
                    elif notification_type == "warning":
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    else:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except ImportError:
                    # winsound not available, just show message
                    pass
        else:
            tk.messagebox.showinfo("測試通知", f"根據目前設定，{notification_type}通知不會顯示")
    
    def get_settings(self) -> dict:
        """
        Get current notification settings.
        
        Returns:
            Dictionary of current settings
        """
        return {
            "notifications_enabled": self.notifications_enabled_var.get(),
            "notification_level": self.notification_level_var.get(),
            "sound_enabled": self.sound_enabled_var.get()
        }
    
    def set_settings(self, settings: dict):
        """
        Set notification settings.
        
        Args:
            settings: Dictionary of settings to apply
        """
        if "notifications_enabled" in settings:
            self.notifications_enabled_var.set(settings["notifications_enabled"])
        
        if "notification_level" in settings:
            self.notification_level_var.set(settings["notification_level"])
        
        if "sound_enabled" in settings:
            self.sound_enabled_var.set(settings["sound_enabled"])
        
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
        # Check if notification level is valid
        valid_levels = ["all", "warnings_errors", "errors_only"]
        return self.notification_level_var.get() in valid_levels