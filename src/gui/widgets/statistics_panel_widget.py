"""
Statistics panel widget for displaying key system metrics.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from datetime import datetime

from src.models.statistics import SystemStatistics


class StatisticsCard(ttk.Frame):
    """Individual statistics card widget."""
    
    def __init__(self, parent: tk.Widget, title: str, value: str = "0", 
                 color: str = "#2196F3", **kwargs):
        """
        Initialize statistics card.
        
        Args:
            parent: Parent widget
            title: Card title
            value: Card value
            color: Card accent color
        """
        super().__init__(parent, **kwargs)
        self.title = title
        self.color = color
        
        self._create_widgets()
        self.update_value(value)
    
    def _create_widgets(self):
        """Create card widgets."""
        # Card frame with border
        self.configure(relief="solid", borderwidth=1, padding=15)
        
        # Title label
        self.title_label = ttk.Label(
            self,
            text=self.title,
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        self.title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Value label
        self.value_label = ttk.Label(
            self,
            text="0",
            font=("Segoe UI", 24, "bold"),
            foreground=self.color
        )
        self.value_label.pack(anchor=tk.W)
        
        # Optional subtitle
        self.subtitle_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 8),
            foreground="#999999"
        )
        self.subtitle_label.pack(anchor=tk.W, pady=(2, 0))
    
    def update_value(self, value: str, subtitle: str = ""):
        """
        Update card value and subtitle.
        
        Args:
            value: New value to display
            subtitle: Optional subtitle text
        """
        self.value_label.configure(text=str(value))
        self.subtitle_label.configure(text=subtitle)
        
        # Show/hide subtitle based on content
        if subtitle:
            self.subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        else:
            self.subtitle_label.pack_forget()


class StatisticsPanelWidget(ttk.Frame):
    """Statistics panel widget displaying key system metrics."""
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize statistics panel widget."""
        super().__init__(parent, **kwargs)
        
        self.active_tasks_card: Optional[StatisticsCard] = None
        self.total_executions_card: Optional[StatisticsCard] = None
        self.success_rate_card: Optional[StatisticsCard] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create statistics panel widgets."""
        # Panel title
        title_label = ttk.Label(
            self,
            text="系統統計",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Cards container
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Configure grid weights for responsive layout
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)
        
        # Active Tasks card
        self.active_tasks_card = StatisticsCard(
            cards_frame,
            title="活躍任務",
            color="#4CAF50"
        )
        self.active_tasks_card.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Total Executions card
        self.total_executions_card = StatisticsCard(
            cards_frame,
            title="總執行次數",
            color="#2196F3"
        )
        self.total_executions_card.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        
        # Success Rate card
        self.success_rate_card = StatisticsCard(
            cards_frame,
            title="成功率",
            color="#FF9800"
        )
        self.success_rate_card.grid(row=0, column=2, sticky="ew", padx=(10, 0))
    
    def update_statistics(self, stats: SystemStatistics):
        """
        Update statistics display.
        
        Args:
            stats: System statistics data
        """
        try:
            # Update Active Tasks
            if self.active_tasks_card:
                self.active_tasks_card.update_value(
                    str(stats.active_tasks),
                    f"共 {stats.active_tasks} 個任務"
                )
            
            # Update Total Executions
            if self.total_executions_card:
                self.total_executions_card.update_value(
                    f"{stats.total_executions:,}",
                    f"成功: {stats.successful_executions}, 失敗: {stats.failed_executions}"
                )
            
            # Update Success Rate
            if self.success_rate_card:
                success_rate_text = f"{stats.success_rate:.1f}%"
                if stats.total_executions == 0:
                    subtitle = "尚無執行記錄"
                    color = "#999999"
                elif stats.success_rate >= 95:
                    subtitle = "優秀"
                    color = "#4CAF50"
                elif stats.success_rate >= 80:
                    subtitle = "良好"
                    color = "#FF9800"
                else:
                    subtitle = "需要改善"
                    color = "#F44336"
                
                self.success_rate_card.value_label.configure(foreground=color)
                self.success_rate_card.update_value(success_rate_text, subtitle)
                
        except Exception as e:
            print(f"Error updating statistics: {e}")
    
    def update_from_dict(self, stats_dict: dict):
        """
        Update statistics from dictionary data.
        
        Args:
            stats_dict: Statistics data as dictionary
        """
        try:
            # Update Active Tasks
            if self.active_tasks_card:
                active_tasks = stats_dict.get("active_tasks", 0)
                self.active_tasks_card.update_value(
                    str(active_tasks),
                    f"共 {active_tasks} 個任務"
                )
            
            # Update Total Executions
            if self.total_executions_card:
                total = stats_dict.get("total_executions", 0)
                successful = stats_dict.get("successful_executions", 0)
                failed = stats_dict.get("failed_executions", 0)
                self.total_executions_card.update_value(
                    f"{total:,}",
                    f"成功: {successful}, 失敗: {failed}"
                )
            
            # Update Success Rate
            if self.success_rate_card:
                success_rate = stats_dict.get("success_rate", 0.0)
                total_executions = stats_dict.get("total_executions", 0)
                
                success_rate_text = f"{success_rate:.1f}%"
                if total_executions == 0:
                    subtitle = "尚無執行記錄"
                    color = "#999999"
                elif success_rate >= 95:
                    subtitle = "優秀"
                    color = "#4CAF50"
                elif success_rate >= 80:
                    subtitle = "良好"
                    color = "#FF9800"
                else:
                    subtitle = "需要改善"
                    color = "#F44336"
                
                self.success_rate_card.value_label.configure(foreground=color)
                self.success_rate_card.update_value(success_rate_text, subtitle)
                
        except Exception as e:
            print(f"Error updating statistics from dict: {e}")