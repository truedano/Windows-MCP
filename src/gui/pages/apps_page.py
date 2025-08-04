"""
Applications monitoring page implementation.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..page_manager import BasePage
from ..widgets.app_monitor_panel import AppMonitorPanel
from ...models.data_models import App
from ...models.execution import ExecutionResult


class AppsPage(BasePage):
    """Applications monitoring page for viewing and controlling running applications."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize applications page."""
        super().__init__(parent, "Apps", "應用程式監控")
        
        # Components
        self.app_monitor_panel: Optional[AppMonitorPanel] = None
        
        # State
        self.is_initialized = False
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame or self.is_initialized:
            return
        
        # Page title and description
        self._create_page_title()
        
        # Create main content
        self._create_content()
        
        self.is_initialized = True
    
    def _create_page_title(self):
        """Create page title and description."""
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Title
        title_label = ttk.Label(
            title_frame,
            text="應用程式監控",
            font=("Microsoft JhengHei UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W)
        
        # Description
        desc_label = ttk.Label(
            title_frame,
            text="監控和控制當前運行的Windows應用程式。",
            font=("Microsoft JhengHei UI", 10),
            foreground="gray"
        )
        desc_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_content(self):
        """Create the main page content."""
        # Main content frame
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create application monitor panel
        self.app_monitor_panel = AppMonitorPanel(content_frame)
        self.app_monitor_panel.pack(fill=tk.BOTH, expand=True)
    
    def on_page_enter(self) -> None:
        """Called when page becomes active."""
        super().on_page_enter()
        
        # Refresh applications when entering the page
        if self.app_monitor_panel:
            self.app_monitor_panel.refresh_apps()
    
    def on_page_leave(self) -> None:
        """Called when page becomes inactive."""
        super().on_page_leave()
    
    def refresh_content(self) -> None:
        """Refresh page content."""
        if self.app_monitor_panel:
            self.app_monitor_panel.refresh_apps()
    
    def get_selected_app(self) -> Optional[App]:
        """
        Get the currently selected application.
        
        Returns:
            Selected application or None
        """
        if self.app_monitor_panel:
            return self.app_monitor_panel.get_selected_app()
        return None
    
    def set_refresh_interval(self, interval: int):
        """
        Set the auto-refresh interval for application monitoring.
        
        Args:
            interval: Refresh interval in seconds
        """
        if self.app_monitor_panel:
            self.app_monitor_panel.set_refresh_interval(interval)
    
    def cleanup(self):
        """Clean up resources when page is destroyed."""
        if self.app_monitor_panel:
            self.app_monitor_panel.destroy()
        super().cleanup()