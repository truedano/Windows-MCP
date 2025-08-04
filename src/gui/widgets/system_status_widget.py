"""
System status widget for displaying current system state.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from datetime import datetime

from src.models.statistics import SystemStatus, SystemStatistics


class StatusIndicator(ttk.Frame):
    """Status indicator widget with colored dot and text."""
    
    def __init__(self, parent: tk.Widget, label: str, **kwargs):
        """
        Initialize status indicator.
        
        Args:
            parent: Parent widget
            label: Status label text
        """
        super().__init__(parent, **kwargs)
        self.label_text = label
        self.status = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create status indicator widgets."""
        # Configure grid
        self.columnconfigure(1, weight=1)
        
        # Status dot (using Unicode circle)
        self.status_dot = ttk.Label(
            self,
            text="●",
            font=("Segoe UI", 12),
            foreground="#F44336"  # Red for inactive
        )
        self.status_dot.grid(row=0, column=0, padx=(0, 8))
        
        # Status label
        self.status_label = ttk.Label(
            self,
            text=self.label_text,
            font=("Segoe UI", 10)
        )
        self.status_label.grid(row=0, column=1, sticky="w")
    
    def update_status(self, active: bool, custom_text: Optional[str] = None):
        """
        Update status indicator.
        
        Args:
            active: Whether status is active
            custom_text: Optional custom text to display
        """
        self.status = active
        
        # Update dot color
        color = "#4CAF50" if active else "#F44336"  # Green for active, red for inactive
        self.status_dot.configure(foreground=color)
        
        # Update label text
        text = custom_text if custom_text else self.label_text
        status_text = "執行中" if active else "停止"
        self.status_label.configure(text=f"{text}: {status_text}")


class SystemStatusWidget(ttk.Frame):
    """System status widget displaying current system state."""
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize system status widget."""
        super().__init__(parent, **kwargs)
        
        self.scheduler_status: Optional[StatusIndicator] = None
        self.windows_mcp_status: Optional[StatusIndicator] = None
        self.logging_status: Optional[StatusIndicator] = None
        self.next_task_label: Optional[ttk.Label] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create system status widgets."""
        # Widget title
        title_label = ttk.Label(
            self,
            text="系統狀態",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Status container
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Scheduler status
        self.scheduler_status = StatusIndicator(status_frame, "排程引擎")
        self.scheduler_status.pack(fill=tk.X, pady=2)
        
        # Windows MCP status
        self.windows_mcp_status = StatusIndicator(status_frame, "Windows-MCP")
        self.windows_mcp_status.pack(fill=tk.X, pady=2)
        
        # Logging status
        self.logging_status = StatusIndicator(status_frame, "日誌記錄")
        self.logging_status.pack(fill=tk.X, pady=2)
        
        # Next task info
        self._create_next_task_info()
    
    def _create_next_task_info(self):
        """Create next task information display."""
        # Next task frame
        next_task_frame = ttk.LabelFrame(self, text="下一個任務", padding=10)
        next_task_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Next task label
        self.next_task_label = ttk.Label(
            next_task_frame,
            text="無排程任務",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        self.next_task_label.pack(anchor=tk.W)
    
    def update_status(self, status: SystemStatus):
        """
        Update system status display.
        
        Args:
            status: System status data
        """
        try:
            # Update scheduler status
            if self.scheduler_status:
                self.scheduler_status.update_status(status.scheduler_running)
            
            # Update Windows MCP status
            if self.windows_mcp_status:
                self.windows_mcp_status.update_status(status.windows_mcp_connected)
            
            # Update logging status
            if self.logging_status:
                self.logging_status.update_status(status.logging_enabled)
            
            # Update next task info
            if self.next_task_label:
                next_task_text = status.get_next_task_description()
                self.next_task_label.configure(text=next_task_text)
                
        except Exception as e:
            print(f"Error updating system status: {e}")
    
    def update_from_dict(self, status_dict: dict):
        """
        Update system status from dictionary data.
        
        Args:
            status_dict: Status data as dictionary
        """
        try:
            # Update scheduler status
            if self.scheduler_status:
                scheduler_running = status_dict.get("scheduler_running", False)
                self.scheduler_status.update_status(scheduler_running)
            
            # Update Windows MCP status
            if self.windows_mcp_status:
                mcp_connected = status_dict.get("windows_mcp_connected", False)
                self.windows_mcp_status.update_status(mcp_connected)
            
            # Update logging status
            if self.logging_status:
                logging_enabled = status_dict.get("logging_enabled", True)
                self.logging_status.update_status(logging_enabled)
            
            # Update next task info
            if self.next_task_label:
                next_task_name = status_dict.get("next_task_name")
                next_task_time = status_dict.get("next_task_time")
                
                if next_task_name and next_task_time:
                    try:
                        task_time = datetime.fromisoformat(next_task_time)
                        now = datetime.now()
                        time_diff = task_time - now
                        
                        if time_diff.total_seconds() < 0:
                            next_task_text = f"{next_task_name} - 已逾期"
                        elif time_diff.total_seconds() < 60:
                            seconds = int(time_diff.total_seconds())
                            next_task_text = f"{next_task_name} - {seconds}秒後"
                        elif time_diff.total_seconds() < 3600:
                            minutes = int(time_diff.total_seconds() / 60)
                            next_task_text = f"{next_task_name} - {minutes}分鐘後"
                        else:
                            hours = int(time_diff.total_seconds() / 3600)
                            minutes = int((time_diff.total_seconds() % 3600) / 60)
                            next_task_text = f"{next_task_name} - {hours}小時{minutes}分鐘後"
                    except:
                        next_task_text = f"{next_task_name} - 時間未知"
                else:
                    next_task_text = "無排程任務"
                
                self.next_task_label.configure(text=next_task_text)
                
        except Exception as e:
            print(f"Error updating system status from dict: {e}")
    
    def update_from_statistics(self, stats: SystemStatistics):
        """
        Update status from system statistics.
        
        Args:
            stats: System statistics containing status data
        """
        self.update_status(stats.system_status)