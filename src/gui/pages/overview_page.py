"""
System overview page implementation.
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from src.gui.page_manager import BasePage
from src.models.statistics import SystemStatistics, ActivityItem, SystemStatus


class OverviewPage(BasePage):
    """System overview page showing statistics and status."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize overview page."""
        super().__init__(parent, "Overview", "系統概覽")
        self.logger = logging.getLogger(__name__)
        
        # Widget references
        self.statistics_panel: Optional[any] = None
        self.recent_activity_widget: Optional[any] = None
        self.system_status_widget: Optional[any] = None
        
        # Data managers
        self._statistics_manager: Optional[any] = None
        self._task_manager: Optional[any] = None
        self._scheduler_engine: Optional[any] = None
        
        # Auto-refresh timer
        self._refresh_timer: Optional[str] = None
        self._refresh_interval = 5000  # 5 seconds
        
        # Initialize data managers
        self._initialize_managers()
    
    def _initialize_managers(self):
        """Initialize data managers."""
        try:
            # Import managers
            from src.core.task_manager import get_task_manager
            from src.core.scheduler_engine import get_scheduler_engine
            from src.core.log_manager import get_log_manager
            
            self._task_manager = get_task_manager()
            self._scheduler_engine = get_scheduler_engine()
            self._log_manager = get_log_manager()
            
        except ImportError as e:
            self.logger.warning(f"Could not import managers: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing managers: {e}")
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        self._create_page_title()
        
        # Main content area with scrollable frame
        self._create_main_content()
        
        # Start auto-refresh
        self._start_auto_refresh()
    
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
    
    def _create_main_content(self):
        """Create main content area with all widgets."""
        # Main container with scrollable area
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store references
        self.canvas = canvas
        self.scrollable_frame = scrollable_frame
        
        # Create content sections
        self._create_statistics_section()
        self._create_recent_activity_section()
        self._create_system_status_section()
    
    def _create_statistics_section(self):
        """Create statistics panel section."""
        try:
            from ..widgets.statistics_panel_widget import StatisticsPanelWidget
            
            self.statistics_panel = StatisticsPanelWidget(self.scrollable_frame)
            self.statistics_panel.pack(fill=tk.X, pady=(0, 20))
            
        except ImportError as e:
            self.logger.error(f"Could not import StatisticsPanelWidget: {e}")
            self._create_fallback_statistics()
    
    def _create_recent_activity_section(self):
        """Create recent activity section."""
        try:
            from ..widgets.recent_activity_widget import RecentActivityWidget
            
            self.recent_activity_widget = RecentActivityWidget(self.scrollable_frame, max_items=10)
            self.recent_activity_widget.pack(fill=tk.X, pady=(0, 20))
            
        except ImportError as e:
            self.logger.error(f"Could not import RecentActivityWidget: {e}")
            self._create_fallback_activity()
    
    def _create_system_status_section(self):
        """Create system status section."""
        try:
            from ..widgets.system_status_widget import SystemStatusWidget
            
            self.system_status_widget = SystemStatusWidget(self.scrollable_frame)
            self.system_status_widget.pack(fill=tk.X, pady=(0, 20))
            
        except ImportError as e:
            self.logger.error(f"Could not import SystemStatusWidget: {e}")
            self._create_fallback_status()
    
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
    
    
    def _create_fallback_statistics(self):
        """Create fallback statistics display."""
        stats_frame = ttk.LabelFrame(self.scrollable_frame, text="系統統計", padding=15)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(stats_frame, text="統計資訊載入中...", foreground="#666666").pack()
    
    def _create_fallback_activity(self):
        """Create fallback activity display."""
        activity_frame = ttk.LabelFrame(self.scrollable_frame, text="最近活動", padding=15)
        activity_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(activity_frame, text="活動記錄載入中...", foreground="#666666").pack()
    
    def _create_fallback_status(self):
        """Create fallback status display."""
        status_frame = ttk.LabelFrame(self.scrollable_frame, text="系統狀態", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(status_frame, text="系統狀態載入中...", foreground="#666666").pack()
    
    def _start_auto_refresh(self):
        """Start auto-refresh timer."""
        if self._refresh_timer:
            self.frame.after_cancel(self._refresh_timer)
        
        self._refresh_timer = self.frame.after(self._refresh_interval, self._auto_refresh)
    
    def _auto_refresh(self):
        """Auto-refresh callback."""
        if self.is_active and self.is_initialized:
            self.refresh_content()
        
        # Schedule next refresh
        self._refresh_timer = self.frame.after(self._refresh_interval, self._auto_refresh)
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if not self.is_initialized:
            return
        
        try:
            # Get current statistics
            statistics = self._get_current_statistics()
            
            # Update all widgets
            self._update_statistics_display(statistics)
            self._update_activity_display(statistics)
            self._update_status_display(statistics)
            
        except Exception as e:
            self.logger.error(f"Error refreshing overview content: {e}")
    
    def _get_current_statistics(self) -> SystemStatistics:
        """
        Get current system statistics.
        
        Returns:
            SystemStatistics object with current data
        """
        try:
            # Get data from managers
            active_tasks = self._get_active_tasks_count()
            execution_stats = self._get_execution_statistics()
            recent_activities = self._get_recent_activities()
            system_status = self._get_system_status()
            
            # Create statistics object using the correct model structure
            statistics = SystemStatistics(
                active_tasks=active_tasks,
                total_executions=execution_stats.get("total", 0),
                successful_executions=execution_stats.get("successful", 0),
                failed_executions=execution_stats.get("failed", 0),
                success_rate=execution_stats.get("success_rate", 0.0),
                recent_activities=recent_activities,
                system_status=system_status,
                uptime=self._get_system_uptime(),
                last_updated=datetime.now()
            )
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error getting current statistics: {e}")
            return self._get_default_statistics()
    
    def _get_active_tasks_count(self) -> int:
        """Get count of active tasks."""
        try:
            if self._task_manager:
                tasks = self._task_manager.get_all_tasks()
                return len([task for task in tasks if task.status.value in ["active", "scheduled"]])
            return 0
        except Exception:
            return 0
    
    def _get_execution_statistics(self) -> Dict[str, any]:
        """Get execution statistics."""
        try:
            if self._log_manager:
                stats = self._log_manager.get_execution_statistics()
                return {
                    "total": stats.total_executions,
                    "successful": stats.successful_executions,
                    "failed": stats.failed_executions,
                    "success_rate": stats.success_rate
                }
            return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}
        except Exception:
            return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}
    
    def _get_recent_activities(self) -> List[ActivityItem]:
        """Get recent activities."""
        try:
            if self._log_manager:
                logs = self._log_manager.get_logs(page=1, page_size=10, filters={})
                activities = []
                
                for log in logs:
                    status = "success" if log.result.success else "failure"
                    activity = ActivityItem(
                        timestamp=log.execution_time,
                        task_name=f"{log.schedule_name}",
                        action="execute",
                        result=status,
                        message=log.result.message
                    )
                    activities.append(activity)
                
                return activities
            return []
        except Exception:
            return []
    
    def _get_system_status(self) -> SystemStatus:
        """Get current system status."""
        try:
            scheduler_running = False
            if self._scheduler_engine:
                scheduler_running = getattr(self._scheduler_engine, 'is_running', False)
            
            # Get next task info
            next_task_name = None
            next_task_time = None
            
            if self._task_manager:
                tasks = self._task_manager.get_all_tasks()
                upcoming_tasks = [task for task in tasks if task.next_execution]
                if upcoming_tasks:
                    next_task = min(upcoming_tasks, key=lambda t: t.next_execution)
                    next_task_name = next_task.name
                    next_task_time = next_task.next_execution
            
            # Format next task info
            next_task_info = "無排程任務"
            if next_task_name and next_task_time:
                next_task_info = f"{next_task_name} ({next_task_time.strftime('%H:%M')})"
            
            return SystemStatus(
                scheduler_running=scheduler_running,
                windows_mcp_connected=True,  # Assume connected for now
                logging_enabled=True,  # Assume enabled for now
                next_task_name=next_task_name,
                next_task_time=next_task_time,
                active_tasks_count=self._get_active_tasks_count()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return SystemStatus(
                scheduler_running=False,
                windows_mcp_connected=False,
                logging_enabled=True,
                next_task_name=None,
                next_task_time=None,
                active_tasks_count=0
            )
    
    def _get_system_uptime(self) -> timedelta:
        """Get system uptime."""
        try:
            if self._scheduler_engine and hasattr(self._scheduler_engine, 'start_time'):
                return datetime.now() - self._scheduler_engine.start_time
            return timedelta()
        except Exception:
            return timedelta()
    
    def _get_default_statistics(self) -> SystemStatistics:
        """Get default statistics when data is unavailable."""
        return SystemStatistics.create_empty()
    
    def _update_statistics_display(self, statistics: SystemStatistics):
        """Update statistics panel display."""
        try:
            if self.statistics_panel:
                self.statistics_panel.update_statistics(statistics)
        except Exception as e:
            self.logger.error(f"Error updating statistics display: {e}")
    
    def _update_activity_display(self, statistics: SystemStatistics):
        """Update recent activity display."""
        try:
            if self.recent_activity_widget:
                self.recent_activity_widget.update_from_statistics(statistics)
        except Exception as e:
            self.logger.error(f"Error updating activity display: {e}")
    
    def _update_status_display(self, statistics: SystemStatistics):
        """Update system status display."""
        try:
            if self.system_status_widget:
                self.system_status_widget.update_from_statistics(statistics)
        except Exception as e:
            self.logger.error(f"Error updating status display: {e}")
    
    def load_overview_data(self):
        """Load overview data from all sources."""
        try:
            self.refresh_content()
        except Exception as e:
            self.logger.error(f"Error loading overview data: {e}")
    
    def refresh_statistics(self):
        """Refresh statistics data."""
        try:
            statistics = self._get_current_statistics()
            self._update_statistics_display(statistics)
        except Exception as e:
            self.logger.error(f"Error refreshing statistics: {e}")
    
    def update_recent_activity(self):
        """Update recent activity data."""
        try:
            statistics = self._get_current_statistics()
            self._update_activity_display(statistics)
        except Exception as e:
            self.logger.error(f"Error updating recent activity: {e}")
    
    def update_system_status(self):
        """Update system status data."""
        try:
            statistics = self._get_current_statistics()
            self._update_status_display(statistics)
        except Exception as e:
            self.logger.error(f"Error updating system status: {e}")
    
    def add_activity(self, description: str, status: str, details: Optional[str] = None):
        """
        Add a new activity to the recent activities.
        
        Args:
            description: Activity description
            status: Activity status ("success", "failure", "warning", "info")
            details: Optional additional details
        """
        try:
            activity = ActivityItem(
                timestamp=datetime.now(),
                task_name=description,
                action="system",
                result=status,
                message=details
            )
            
            if self.recent_activity_widget:
                self.recent_activity_widget.add_activity(activity)
                
        except Exception as e:
            self.logger.error(f"Error adding activity: {e}")
    
    def get_statistics(self) -> SystemStatistics:
        """
        Get current statistics data.
        
        Returns:
            SystemStatistics object
        """
        return self._get_current_statistics()
    
    def destroy(self):
        """Clean up resources when page is destroyed."""
        # Cancel auto-refresh timer
        if self._refresh_timer:
            self.frame.after_cancel(self._refresh_timer)
            self._refresh_timer = None
        
        super().destroy()