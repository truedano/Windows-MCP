"""
System overview page implementation.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, List, Tuple

from src.gui.page_manager import BasePage


class OverviewPage(BasePage):
    """System overview page showing statistics and status."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize overview page."""
        super().__init__(parent, "Overview", "系統概覽")
        
        # Statistics data
        self.stats_data = {
            "active_tasks": 12,
            "total_executions": 1247,
            "success_rate": 95.2
        }
        
        # Recent activities
        self.recent_activities = [
            ("[10:30]", "Daily Backup", "Success"),
            ("[10:15]", "Close Browser", "Success"),
            ("[10:00]", "System Cleanup", "Failed"),
            ("[09:45]", "Launch Calculator", "Success")
        ]
        
        # System status
        self.system_status = {
            "scheduler_engine": "Running",
            "windows_mcp": "Connected",
            "log_recording": "Enabled",
            "next_task": "Daily Backup in 2h 30m"
        }
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        self._create_page_title()
        
        # Status monitor section (replaces old statistics, activity, and status sections)
        self._create_statistics_section()
    
    def _create_page_title(self):
        """Create page title."""
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame,
            text="System Overview",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(
            title_frame,
            text="系統狀態概覽和統計資訊",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_statistics_section(self):
        """Create statistics cards section using StatusMonitorWidget."""
        from ..widgets import StatusMonitorWidget
        
        # Create status monitor widget
        self.status_monitor = StatusMonitorWidget(self.frame)
        self.status_monitor.pack(fill=tk.BOTH, expand=True, pady=(0, 25))
    
    def _create_stat_card(self, parent: tk.Widget, title: str, subtitle: str, 
                         value: str, color: str) -> ttk.Frame:
        """
        Create a statistics card.
        
        Args:
            parent: Parent widget
            title: Card title
            subtitle: Card subtitle
            value: Statistics value
            color: Card accent color
            
        Returns:
            Card frame widget
        """
        # Card frame with border
        card = ttk.LabelFrame(parent, padding=15)
        
        # Title
        title_label = ttk.Label(
            card,
            text=title,
            font=("Segoe UI", 10, "bold"),
            foreground=color
        )
        title_label.pack(anchor=tk.W)
        
        # Subtitle
        subtitle_label = ttk.Label(
            card,
            text=subtitle,
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(2, 8))
        
        # Value
        value_label = ttk.Label(
            card,
            text=value,
            font=("Segoe UI", 24, "bold"),
            foreground=color
        )
        value_label.pack(anchor=tk.CENTER)
        
        return card
    
    def _format_stat_value(self, key: str) -> str:
        """
        Format statistics value for display.
        
        Args:
            key: Statistics key
            
        Returns:
            Formatted value string
        """
        value = self.stats_data.get(key, 0)
        
        if key == "success_rate":
            return f"{value}%"
        elif key == "total_executions":
            return f"{value:,}"
        else:
            return str(value)
    
    def _create_recent_activity_section(self):
        """Create recent activity section."""
        activity_frame = ttk.Frame(self.frame)
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 25))
        
        # Section title
        title_label = ttk.Label(
            activity_frame,
            text="Recent Activity",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Activity list frame
        list_frame = ttk.LabelFrame(activity_frame, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create activity list
        self.activity_listbox = tk.Listbox(
            list_frame,
            font=("Consolas", 10),
            height=6,
            selectmode=tk.SINGLE,
            activestyle="none"
        )
        
        # Scrollbar for activity list
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.activity_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.activity_listbox.yview)
        
        # Pack activity list and scrollbar
        self.activity_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate activity list
        self._populate_activity_list()
    
    def _populate_activity_list(self):
        """Populate the activity list with recent activities."""
        self.activity_listbox.delete(0, tk.END)
        
        for time, task, status in self.recent_activities:
            status_symbol = "✓" if status == "Success" else "✗"
            status_color = "#107c10" if status == "Success" else "#d83b01"
            
            activity_text = f"{time} {task} - {status_symbol} {status}"
            self.activity_listbox.insert(tk.END, activity_text)
            
            # Color coding would require custom listbox implementation
            # For now, using text symbols
    
    def _create_system_status_section(self):
        """Create system status section."""
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill=tk.X)
        
        # Section title
        title_label = ttk.Label(
            status_frame,
            text="System Status",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Status items frame
        items_frame = ttk.LabelFrame(status_frame, padding=15)
        items_frame.pack(fill=tk.X)
        
        # Status items
        status_items = [
            ("Scheduler Engine", self.system_status["scheduler_engine"]),
            ("Windows-MCP", self.system_status["windows_mcp"]),
            ("Log Recording", self.system_status["log_recording"]),
            ("Next Task", self.system_status["next_task"])
        ]
        
        for i, (label, status) in enumerate(status_items):
            item_frame = ttk.Frame(items_frame)
            item_frame.pack(fill=tk.X, pady=3)
            
            # Status indicator
            if status in ["Running", "Connected", "Enabled"]:
                indicator = "●"
                color = "#107c10"
            else:
                indicator = "○"
                color = "#666666"
            
            # Label
            label_text = ttk.Label(
                item_frame,
                text=f"{label}:",
                font=("Segoe UI", 10),
                width=20
            )
            label_text.pack(side=tk.LEFT)
            
            # Status
            status_text = ttk.Label(
                item_frame,
                text=f"{indicator} {status}",
                font=("Segoe UI", 10),
                foreground=color
            )
            status_text.pack(side=tk.LEFT)
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if not self.is_initialized:
            return
        
        # Update statistics
        self._update_statistics()
        
        # Update recent activities
        self._update_recent_activities()
        
        # Update system status
        self._update_system_status()
    
    def _update_statistics(self):
        """Update statistics display."""
        # In a real implementation, this would fetch current data
        # For now, we'll simulate some changes
        import random
        
        # Simulate minor changes in statistics
        self.stats_data["active_tasks"] = random.randint(10, 15)
        self.stats_data["total_executions"] += random.randint(0, 5)
        self.stats_data["success_rate"] = round(random.uniform(94.0, 97.0), 1)
        
        # Update display would require rebuilding cards or updating labels
        # This is a simplified version
    
    def _update_recent_activities(self):
        """Update recent activities list."""
        # Refresh the activity list
        self._populate_activity_list()
    
    def _update_system_status(self):
        """Update system status display."""
        # Update status information
        # In a real implementation, this would check actual system status
        pass
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get current statistics data.
        
        Returns:
            Dictionary of statistics
        """
        return self.stats_data.copy()
    
    def add_activity(self, time: str, task: str, status: str):
        """
        Add a new activity to the recent activities list.
        
        Args:
            time: Activity time
            task: Task name
            status: Execution status
        """
        # Add to beginning of list
        self.recent_activities.insert(0, (time, task, status))
        
        # Keep only last 10 activities
        if len(self.recent_activities) > 10:
            self.recent_activities = self.recent_activities[:10]
        
        # Refresh display if page is active
        if self.is_active:
            self._populate_activity_list()
    
    def update_system_status(self, component: str, status: str):
        """
        Update system status for a component.
        
        Args:
            component: Component name
            status: New status
        """
        if component in self.system_status:
            self.system_status[component] = status
            
            # Refresh display if page is active
            if self.is_active:
                self._update_system_status()