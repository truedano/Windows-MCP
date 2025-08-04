"""
Settings page implementation.
"""

import tkinter as tk
from tkinter import ttk

from src.gui.page_manager import BasePage


class SettingsPage(BasePage):
    """System settings page."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize settings page."""
        super().__init__(parent, "Settings", "系統設定")
    
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
        
        # Placeholder content
        placeholder_frame = ttk.LabelFrame(self.frame, text="系統配置", padding=20)
        placeholder_frame.pack(fill=tk.BOTH, expand=True)
        
        placeholder_label = ttk.Label(
            placeholder_frame,
            text="系統設定功能將在後續任務中實作\n\n包含功能：\n• 一般設定\n• 通知設定\n• 介面主題\n• 進階選項",
            font=("Segoe UI", 11),
            justify=tk.LEFT
        )
        placeholder_label.pack(expand=True)
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        # Will be implemented when actual settings management is added
        pass