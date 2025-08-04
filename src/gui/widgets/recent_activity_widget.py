"""
Recent activity widget for displaying system activity history.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional
from datetime import datetime

from src.models.statistics import ActivityItem, SystemStatistics


class ActivityListItem(ttk.Frame):
    """Individual activity list item."""
    
    def __init__(self, parent: tk.Widget, activity: ActivityItem, **kwargs):
        """
        Initialize activity list item.
        
        Args:
            parent: Parent widget
            activity: Activity item data
        """
        super().__init__(parent, **kwargs)
        self.activity = activity
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create activity item widgets."""
        # Configure grid
        self.columnconfigure(1, weight=1)
        
        # Status indicator
        status_colors = {
            "success": "#4CAF50",
            "failure": "#F44336", 
            "warning": "#FF9800",
            "info": "#2196F3"
        }
        
        status_color = status_colors.get(self.activity.status, "#999999")
        
        status_frame = tk.Frame(self, width=4, bg=status_color)
        status_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        status_frame.grid_propagate(False)
        
        # Content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=1, sticky="ew", pady=5)
        content_frame.columnconfigure(1, weight=1)
        
        # Time label
        time_str = self.activity.timestamp.strftime("%H:%M")
        time_label = ttk.Label(
            content_frame,
            text=f"[{time_str}]",
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        time_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Description label
        desc_label = ttk.Label(
            content_frame,
            text=self.activity.description,
            font=("Segoe UI", 9)
        )
        desc_label.grid(row=0, column=1, sticky="w")
        
        # Status label
        status_text = {
            "success": "成功",
            "failure": "失敗",
            "warning": "警告", 
            "info": "資訊"
        }.get(self.activity.status, self.activity.status)
        
        status_label = ttk.Label(
            content_frame,
            text=status_text,
            font=("Segoe UI", 9),
            foreground=status_color
        )
        status_label.grid(row=0, column=2, sticky="e", padx=(10, 0))


class RecentActivityWidget(ttk.Frame):
    """Recent activity widget displaying system activity history."""
    
    def __init__(self, parent: tk.Widget, max_items: int = 10, **kwargs):
        """
        Initialize recent activity widget.
        
        Args:
            parent: Parent widget
            max_items: Maximum number of items to display
        """
        super().__init__(parent, **kwargs)
        self.max_items = max_items
        self.activity_items: List[ActivityItem] = []
        
        self.activity_list_frame: Optional[ttk.Frame] = None
        self.no_activity_label: Optional[ttk.Label] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create recent activity widgets."""
        # Widget title
        title_label = ttk.Label(
            self,
            text="最近活動",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Scrollable frame for activity list
        self._create_scrollable_list()
        
        # Show initial empty state
        self._show_empty_state()
    
    def _create_scrollable_list(self):
        """Create scrollable activity list."""
        # Container frame
        container_frame = ttk.Frame(self)
        container_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(
            container_frame,
            height=200,
            highlightthickness=0,
            bg="#FFFFFF"
        )
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        
        # Scrollable frame
        self.activity_list_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=self.activity_list_frame, anchor="nw")
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update scroll region when frame size changes
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.activity_list_frame.bind("<Configure>", configure_scroll_region)
        
        # Store references
        self.canvas = canvas
        self.scrollbar = scrollbar
    
    def _show_empty_state(self):
        """Show empty state when no activities."""
        if self.no_activity_label:
            self.no_activity_label.destroy()
        
        self.no_activity_label = ttk.Label(
            self.activity_list_frame,
            text="尚無活動記錄",
            font=("Segoe UI", 10),
            foreground="#999999"
        )
        self.no_activity_label.pack(pady=20)
    
    def _hide_empty_state(self):
        """Hide empty state."""
        if self.no_activity_label:
            self.no_activity_label.destroy()
            self.no_activity_label = None
    
    def add_activity(self, activity: ActivityItem):
        """
        Add a new activity item.
        
        Args:
            activity: Activity item to add
        """
        # Add to beginning of list
        self.activity_items.insert(0, activity)
        
        # Limit to max items
        if len(self.activity_items) > self.max_items:
            self.activity_items = self.activity_items[:self.max_items]
        
        # Refresh display
        self._refresh_display()
    
    def clear_old_activities(self):
        """Clear old activities beyond max limit."""
        if len(self.activity_items) > self.max_items:
            self.activity_items = self.activity_items[:self.max_items]
            self._refresh_display()
    
    def update_activities(self, activities: List[ActivityItem]):
        """
        Update with new list of activities.
        
        Args:
            activities: List of activity items
        """
        self.activity_items = activities[:self.max_items]
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the activity display."""
        # Clear existing items
        for widget in self.activity_list_frame.winfo_children():
            widget.destroy()
        
        # Show activities or empty state
        if not self.activity_items:
            self._show_empty_state()
        else:
            self._hide_empty_state()
            
            # Create activity items
            for activity in self.activity_items:
                item_widget = ActivityListItem(self.activity_list_frame, activity)
                item_widget.pack(fill=tk.X, pady=2)
        
        # Update scroll region
        self.activity_list_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def update_from_statistics(self, stats: SystemStatistics):
        """
        Update activities from system statistics.
        
        Args:
            stats: System statistics containing recent activities
        """
        self.update_activities(stats.recent_activities)
    
    def update_from_dict(self, activities_data: List[dict]):
        """
        Update activities from dictionary data.
        
        Args:
            activities_data: List of activity dictionaries
        """
        try:
            activities = [ActivityItem.from_dict(data) for data in activities_data]
            self.update_activities(activities)
        except Exception as e:
            print(f"Error updating activities from dict: {e}")