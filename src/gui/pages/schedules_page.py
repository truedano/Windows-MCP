"""
Schedules management page implementation.
"""

import tkinter as tk
from tkinter import ttk

from src.gui.page_manager import BasePage


class SchedulesPage(BasePage):
    """Schedules management page."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize schedules page."""
        super().__init__(parent, "Schedules", "排程管理")
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="Schedule Management",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="管理排程任務、建立和編輯排程",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder content
        placeholder_frame = ttk.LabelFrame(self.frame, text="排程清單", padding=20)
        placeholder_frame.pack(fill=tk.BOTH, expand=True)
        
        placeholder_label = ttk.Label(
            placeholder_frame,
            text="排程管理功能將在後續任務中實作\n\n包含功能：\n• 排程清單顯示\n• 新增/編輯排程\n• 排程狀態管理\n• 批次操作",
            font=("Segoe UI", 11),
            justify=tk.LEFT
        )
        placeholder_label.pack(expand=True)
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        # Will be implemented when actual schedule management is added
        pass