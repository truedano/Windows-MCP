"""
Status Monitor Widget for displaying system status and statistics.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Optional, Callable

from ...models.statistics import SystemStatistics, SystemStatus, ActivityItem
from ...core.scheduler_engine import get_scheduler_engine


class StatusMonitorWidget(ttk.Frame):
    """Widget for monitoring and displaying system status and statistics."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the StatusMonitorWidget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for Frame
        """
        super().__init__(parent, **kwargs)
        
        self.scheduler_engine = get_scheduler_engine()
        self.statistics: Optional[SystemStatistics] = None
        self.refresh_callback: Optional[Callable] = None
        self.update_interval = 5000  # 5 seconds
        self.update_job = None
        
        self._setup_ui()
        self._start_auto_update()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="系統狀態監控", 
            font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Statistics cards container
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        self._create_statistics_cards(stats_frame)
        
        # System status section
        status_frame = ttk.LabelFrame(main_frame, text="系統狀態", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self._create_system_status(status_frame)
        
        # Recent activity section
        activity_frame = ttk.LabelFrame(main_frame, text="最近活動", padding=10)
        activity_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_recent_activity(activity_frame)
        
        # Refresh button
        refresh_frame = ttk.Frame(main_frame)
        refresh_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_button = ttk.Button(
            refresh_frame,
            text="重新整理",
            command=self._manual_refresh
        )
        self.refresh_button.pack(side=tk.RIGHT)
        
        # Last updated label
        self.last_updated_label = ttk.Label(
            refresh_frame,
            text="最後更新: --",
            font=("TkDefaultFont", 8)
        )
        self.last_updated_label.pack(side=tk.LEFT)
    
    def _create_statistics_cards(self, parent):
        """Create statistics cards."""
        # Active tasks card
        self.active_tasks_frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        self.active_tasks_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(
            self.active_tasks_frame, 
            text="活躍任務", 
            font=("TkDefaultFont", 10, "bold")
        ).pack(pady=(10, 5))
        
        self.active_tasks_value = ttk.Label(
            self.active_tasks_frame, 
            text="--", 
            font=("TkDefaultFont", 20, "bold"),
            foreground="blue"
        )
        self.active_tasks_value.pack(pady=(0, 10))
        
        # Total executions card
        self.total_executions_frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        self.total_executions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(
            self.total_executions_frame, 
            text="總執行次數", 
            font=("TkDefaultFont", 10, "bold")
        ).pack(pady=(10, 5))
        
        self.total_executions_value = ttk.Label(
            self.total_executions_frame, 
            text="--", 
            font=("TkDefaultFont", 20, "bold"),
            foreground="green"
        )
        self.total_executions_value.pack(pady=(0, 10))
        
        # Success rate card
        self.success_rate_frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        self.success_rate_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(
            self.success_rate_frame, 
            text="成功率", 
            font=("TkDefaultFont", 10, "bold")
        ).pack(pady=(10, 5))
        
        self.success_rate_value = ttk.Label(
            self.success_rate_frame, 
            text="--", 
            font=("TkDefaultFont", 20, "bold"),
            foreground="orange"
        )
        self.success_rate_value.pack(pady=(0, 10))
    
    def _create_system_status(self, parent):
        """Create system status indicators."""
        # Status indicators frame
        indicators_frame = ttk.Frame(parent)
        indicators_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Scheduler status
        scheduler_frame = ttk.Frame(indicators_frame)
        scheduler_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(scheduler_frame, text="排程引擎:").pack(side=tk.LEFT)
        self.scheduler_status_label = ttk.Label(
            scheduler_frame, 
            text="● 運行中", 
            foreground="green"
        )
        self.scheduler_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Windows-MCP status
        mcp_frame = ttk.Frame(indicators_frame)
        mcp_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(mcp_frame, text="Windows-MCP:").pack(side=tk.LEFT)
        self.mcp_status_label = ttk.Label(
            mcp_frame, 
            text="● 已連接", 
            foreground="green"
        )
        self.mcp_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Logging status
        logging_frame = ttk.Frame(indicators_frame)
        logging_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(logging_frame, text="日誌記錄:").pack(side=tk.LEFT)
        self.logging_status_label = ttk.Label(
            logging_frame, 
            text="● 已啟用", 
            foreground="green"
        )
        self.logging_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Next task info
        next_task_frame = ttk.Frame(indicators_frame)
        next_task_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(next_task_frame, text="下一個任務:").pack(side=tk.LEFT)
        self.next_task_label = ttk.Label(
            next_task_frame, 
            text="無排程任務"
        )
        self.next_task_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Uptime info
        uptime_frame = ttk.Frame(indicators_frame)
        uptime_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(uptime_frame, text="運行時間:").pack(side=tk.LEFT)
        self.uptime_label = ttk.Label(
            uptime_frame, 
            text="--"
        )
        self.uptime_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def _create_recent_activity(self, parent):
        """Create recent activity list."""
        # Activity list with scrollbar
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Activity listbox
        self.activity_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("TkDefaultFont", 9),
            height=8
        )
        self.activity_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.activity_listbox.yview)
        
        # Configure colors for different status types
        self.activity_listbox.tag_configure("success", foreground="green")
        self.activity_listbox.tag_configure("failure", foreground="red")
        self.activity_listbox.tag_configure("warning", foreground="orange")
        self.activity_listbox.tag_configure("info", foreground="blue")
    
    def _start_auto_update(self):
        """Start automatic status updates."""
        self._update_status()
        self.update_job = self.after(self.update_interval, self._start_auto_update)
    
    def _stop_auto_update(self):
        """Stop automatic status updates."""
        if self.update_job:
            self.after_cancel(self.update_job)
            self.update_job = None
    
    def _update_status(self):
        """Update the status display."""
        try:
            # Get current statistics from scheduler engine
            if hasattr(self.scheduler_engine, 'get_statistics'):
                self.statistics = self.scheduler_engine.get_statistics()
            else:
                # Create mock statistics for testing
                self.statistics = self._create_mock_statistics()
            
            self._update_statistics_display()
            self._update_system_status_display()
            self._update_recent_activity_display()
            self._update_last_updated()
            
        except Exception as e:
            print(f"Error updating status: {e}")
            # Show error in UI
            self._show_error_status()
    
    def _create_mock_statistics(self) -> SystemStatistics:
        """Create mock statistics for testing."""
        return SystemStatistics(
            active_tasks=5,
            total_executions=127,
            successful_executions=121,
            failed_executions=6,
            success_rate=95.3,
            recent_activities=[
                ActivityItem(
                    timestamp=datetime.now() - timedelta(minutes=5),
                    description="每日備份任務",
                    status="success",
                    details="備份完成"
                ),
                ActivityItem(
                    timestamp=datetime.now() - timedelta(minutes=15),
                    description="關閉瀏覽器",
                    status="success",
                    details="成功關閉Chrome"
                ),
                ActivityItem(
                    timestamp=datetime.now() - timedelta(minutes=30),
                    description="系統清理",
                    status="failure",
                    details="權限不足"
                )
            ],
            system_status=SystemStatus(
                scheduler_running=True,
                windows_mcp_connected=True,
                logging_enabled=True,
                next_task_name="每日備份",
                next_task_time=datetime.now() + timedelta(hours=2, minutes=30),
                active_tasks_count=5
            ),
            uptime=timedelta(hours=12, minutes=45),
            last_updated=datetime.now()
        )
    
    def _update_statistics_display(self):
        """Update statistics cards."""
        if not self.statistics:
            return
        
        self.active_tasks_value.config(text=str(self.statistics.active_tasks))
        self.total_executions_value.config(text=f"{self.statistics.total_executions:,}")
        self.success_rate_value.config(text=f"{self.statistics.success_rate:.1f}%")
        
        # Update colors based on values
        if self.statistics.success_rate >= 95:
            self.success_rate_value.config(foreground="green")
        elif self.statistics.success_rate >= 80:
            self.success_rate_value.config(foreground="orange")
        else:
            self.success_rate_value.config(foreground="red")
    
    def _update_system_status_display(self):
        """Update system status indicators."""
        if not self.statistics or not self.statistics.system_status:
            return
        
        status = self.statistics.system_status
        
        # Scheduler status
        if status.scheduler_running:
            self.scheduler_status_label.config(text="● 運行中", foreground="green")
        else:
            self.scheduler_status_label.config(text="● 已停止", foreground="red")
        
        # Windows-MCP status
        if status.windows_mcp_connected:
            self.mcp_status_label.config(text="● 已連接", foreground="green")
        else:
            self.mcp_status_label.config(text="● 未連接", foreground="red")
        
        # Logging status
        if status.logging_enabled:
            self.logging_status_label.config(text="● 已啟用", foreground="green")
        else:
            self.logging_status_label.config(text="● 已停用", foreground="orange")
        
        # Next task
        next_task_text = status.get_next_task_description()
        self.next_task_label.config(text=next_task_text)
        
        # Uptime
        uptime_text = self.statistics.get_formatted_uptime()
        self.uptime_label.config(text=uptime_text)
    
    def _update_recent_activity_display(self):
        """Update recent activity list."""
        if not self.statistics:
            return
        
        # Clear current items
        self.activity_listbox.delete(0, tk.END)
        
        # Add recent activities
        for activity in self.statistics.recent_activities:
            time_str = activity.timestamp.strftime("%H:%M")
            status_icon = self._get_status_icon(activity.status)
            text = f"[{time_str}] {status_icon} {activity.description}"
            
            self.activity_listbox.insert(tk.END, text)
            
            # Set color based on status
            index = self.activity_listbox.size() - 1
            if activity.status == "success":
                self.activity_listbox.itemconfig(index, foreground="green")
            elif activity.status == "failure":
                self.activity_listbox.itemconfig(index, foreground="red")
            elif activity.status == "warning":
                self.activity_listbox.itemconfig(index, foreground="orange")
            else:
                self.activity_listbox.itemconfig(index, foreground="blue")
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for status."""
        icons = {
            "success": "✓",
            "failure": "✗",
            "warning": "⚠",
            "info": "ℹ"
        }
        return icons.get(status, "•")
    
    def _update_last_updated(self):
        """Update last updated timestamp."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.last_updated_label.config(text=f"最後更新: {time_str}")
    
    def _show_error_status(self):
        """Show error status in UI."""
        self.active_tasks_value.config(text="錯誤")
        self.total_executions_value.config(text="錯誤")
        self.success_rate_value.config(text="錯誤")
        
        self.scheduler_status_label.config(text="● 錯誤", foreground="red")
        self.mcp_status_label.config(text="● 錯誤", foreground="red")
        self.logging_status_label.config(text="● 錯誤", foreground="red")
        self.next_task_label.config(text="無法取得資訊")
        self.uptime_label.config(text="--")
        
        self.activity_listbox.delete(0, tk.END)
        self.activity_listbox.insert(tk.END, "無法載入活動記錄")
    
    def _manual_refresh(self):
        """Handle manual refresh button click."""
        self._update_status()
        if self.refresh_callback:
            self.refresh_callback()
    
    def set_refresh_callback(self, callback: Callable):
        """Set callback for refresh events."""
        self.refresh_callback = callback
    
    def set_update_interval(self, interval: int):
        """
        Set auto-update interval.
        
        Args:
            interval: Update interval in milliseconds
        """
        self.update_interval = interval
        # Restart auto-update with new interval
        self._stop_auto_update()
        self._start_auto_update()
    
    def get_statistics(self) -> Optional[SystemStatistics]:
        """Get current statistics."""
        return self.statistics
    
    def destroy(self):
        """Clean up resources when widget is destroyed."""
        self._stop_auto_update()
        super().destroy()