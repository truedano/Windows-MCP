"""
Execution logs page implementation.
"""

import tkinter as tk
from tkinter import ttk

from src.gui.page_manager import BasePage


class LogsPage(BasePage):
    """Execution logs page."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize logs page."""
        super().__init__(parent, "Logs", "執行記錄")
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="Execution Logs",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="查看任務執行歷史和日誌",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder content
        placeholder_frame = ttk.LabelFrame(self.frame, text="執行日誌", padding=20)
        placeholder_frame.pack(fill=tk.BOTH, expand=True)
        
        placeholder_label = ttk.Label(
            placeholder_frame,
            text="執行記錄功能將在後續任務中實作\n\n包含功能：\n• 日誌記錄顯示\n• 日誌搜尋和篩選\n• 執行歷史統計\n• 日誌匯出",
            font=("Segoe UI", 11),
            justify=tk.LEFT
        )
        placeholder_label.pack(expand=True)
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        # Will be implemented when actual log management is added
        pass