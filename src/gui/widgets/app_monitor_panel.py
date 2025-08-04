"""
Application Monitor Panel that combines app list and detail widgets.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ...models.data_models import App
from ...models.execution import ExecutionResult
from .app_list_widget import AppListWidget
from .app_detail_widget import AppDetailWidget


class AppMonitorPanel(ttk.Frame):
    """Panel that combines application list and detail widgets for comprehensive app monitoring."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the AppMonitorPanel.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for Frame
        """
        super().__init__(parent, **kwargs)
        
        self.current_app: Optional[App] = None
        
        self._setup_ui()
        self._connect_widgets()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create main paned window for resizable layout
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Application list
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=2)
        
        # Application list title
        list_title = ttk.Label(left_frame, text="Running Applications", font=("TkDefaultFont", 12, "bold"))
        list_title.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        # Application list widget
        self.app_list_widget = AppListWidget(left_frame)
        self.app_list_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel: Application details
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=1)
        
        # Application detail widget
        self.app_detail_widget = AppDetailWidget(right_frame)
        self.app_detail_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Set initial pane sizes (60% for list, 40% for details)
        self.after_idle(lambda: self.paned_window.sashpos(0, 600))
    
    def _connect_widgets(self):
        """Connect the widgets to work together."""
        # Set up app selection callback
        self.app_list_widget.set_app_selection_callback(self._on_app_selected)
        
        # Set up action completion callback
        self.app_detail_widget.set_action_completed_callback(self._on_action_completed)
    
    def _on_app_selected(self, app: App):
        """
        Handle application selection from the list.
        
        Args:
            app: Selected application
        """
        self.current_app = app
        self.app_detail_widget.set_app(app)
    
    def _on_action_completed(self, result: ExecutionResult):
        """
        Handle completion of an action on an application.
        
        Args:
            result: Result of the action execution
        """
        # If the action was successful and might have changed app state, refresh the list
        if result.success and result.operation in ['close_app', 'minimize_window', 'maximize_window', 'focus_window']:
            # Delay refresh slightly to allow system to update
            self.after(1000, self.app_list_widget.refresh_apps)
    
    def refresh_apps(self):
        """Refresh the applications list."""
        self.app_list_widget.refresh_apps()
    
    def get_selected_app(self) -> Optional[App]:
        """Get the currently selected application."""
        return self.current_app
    
    def set_refresh_interval(self, interval: int):
        """
        Set the auto-refresh interval for the application list.
        
        Args:
            interval: Refresh interval in seconds
        """
        self.app_list_widget.set_refresh_interval(interval)
    
    def destroy(self):
        """Clean up resources when panel is destroyed."""
        # Clean up the app list widget's background thread
        if hasattr(self, 'app_list_widget'):
            self.app_list_widget.destroy()
        super().destroy()