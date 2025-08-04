"""
Help page implementation.
"""

import tkinter as tk
from tkinter import ttk

from src.gui.page_manager import BasePage


class HelpPage(BasePage):
    """Help and support page."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize help page."""
        super().__init__(parent, "Help", "說明文件")
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="Help & Support",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="使用指南、FAQ和支援資訊",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder content
        placeholder_frame = ttk.LabelFrame(self.frame, text="說明內容", padding=20)
        placeholder_frame.pack(fill=tk.BOTH, expand=True)
        
        placeholder_label = ttk.Label(
            placeholder_frame,
            text="說明文件功能將在後續任務中實作\n\n包含功能：\n• 使用指南\n• 常見問題 (FAQ)\n• 功能說明\n• 聯絡支援",
            font=("Segoe UI", 11),
            justify=tk.LEFT
        )
        placeholder_label.pack(expand=True)
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        # Will be implemented when actual help content is added
        pass