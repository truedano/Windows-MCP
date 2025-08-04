"""
Task detail widget implementation.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.models.task import Task, TaskStatus
from src.models.action import ActionType
from src.models.schedule import ScheduleType
from src.core.task_manager import TaskManager


class TaskDetailWidget(ttk.Frame):
    """Widget for displaying detailed task information."""
    
    def __init__(self, parent: tk.Widget, task_manager: TaskManager):
        """
        Initialize task detail widget.
        
        Args:
            parent: Parent widget
            task_manager: Task manager instance
        """
        super().__init__(parent)
        self.task_manager = task_manager
        self.current_task: Optional[Task] = None
        
        self._setup_ui()
        self._show_empty_state()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create scrollable frame
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Bind mouse wheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _clear_content(self) -> None:
        """Clear all content from the scrollable frame."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
    
    def _show_empty_state(self) -> None:
        """Show empty state when no task is selected."""
        self._clear_content()
        
        empty_frame = ttk.Frame(self.scrollable_frame)
        empty_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Empty state icon and text
        empty_label = ttk.Label(
            empty_frame,
            text="📋",
            font=("Segoe UI", 48)
        )
        empty_label.pack(pady=(50, 10))
        
        message_label = ttk.Label(
            empty_frame,
            text="Select a task to view details",
            font=("Segoe UI", 12),
            foreground="#666666"
        )
        message_label.pack()
        
        instruction_label = ttk.Label(
            empty_frame,
            text="Click on a task in the list to see its detailed information,\nincluding schedule settings, execution history, and parameters.",
            font=("Segoe UI", 10),
            foreground="#999999",
            justify=tk.CENTER
        )
        instruction_label.pack(pady=(10, 0))
    
    def _show_multi_selection_state(self, count: int) -> None:
        """Show state when multiple tasks are selected."""
        self._clear_content()
        
        multi_frame = ttk.Frame(self.scrollable_frame)
        multi_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Multi-selection icon and text
        multi_label = ttk.Label(
            multi_frame,
            text="📋📋",
            font=("Segoe UI", 48)
        )
        multi_label.pack(pady=(50, 10))
        
        message_label = ttk.Label(
            multi_frame,
            text=f"{count} tasks selected",
            font=("Segoe UI", 12, "bold")
        )
        message_label.pack()
        
        instruction_label = ttk.Label(
            multi_frame,
            text="Batch operations available:\n• Delete selected tasks\n• Export task configurations\n• Bulk status changes",
            font=("Segoe UI", 10),
            foreground="#666666",
            justify=tk.CENTER
        )
        instruction_label.pack(pady=(10, 0))
    
    def _create_section(self, title: str, icon: str = "") -> ttk.LabelFrame:
        """Create a section with title and optional icon."""
        section_title = f"{icon} {title}" if icon else title
        section = ttk.LabelFrame(
            self.scrollable_frame,
            text=section_title,
            padding=15
        )
        section.pack(fill=tk.X, padx=10, pady=5)
        return section
    
    def _create_info_row(self, parent: tk.Widget, label: str, value: str, 
                        value_color: str = "#000000", value_font: tuple = None) -> None:
        """Create an information row with label and value."""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=2)
        
        # Label
        label_widget = ttk.Label(
            row_frame,
            text=f"{label}:",
            font=("Segoe UI", 10, "bold"),
            width=15,
            anchor="w"
        )
        label_widget.pack(side=tk.LEFT)
        
        # Value
        value_font = value_font or ("Segoe UI", 10)
        value_widget = ttk.Label(
            row_frame,
            text=value,
            font=value_font,
            foreground=value_color,
            anchor="w"
        )
        value_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
    
    def _get_status_info(self, status: TaskStatus) -> tuple:
        """Get status display information."""
        status_info = {
            TaskStatus.PENDING: ("⏳ Pending", "#FFA500"),
            TaskStatus.RUNNING: ("▶️ Running", "#007ACC"),
            TaskStatus.COMPLETED: ("✅ Completed", "#28A745"),
            TaskStatus.FAILED: ("❌ Failed", "#DC3545"),
            TaskStatus.DISABLED: ("⏸️ Disabled", "#6C757D")
        }
        return status_info.get(status, ("❓ Unknown", "#000000"))
    
    def _get_action_type_info(self, action_type: ActionType) -> str:
        """Get localized action type text."""
        action_texts = {
            ActionType.LAUNCH_APP: "🚀 Launch Application",
            ActionType.CLOSE_APP: "❌ Close Application",
            ActionType.FOCUS_WINDOW: "🎯 Focus Window",
            ActionType.MINIMIZE_WINDOW: "⬇️ Minimize Window",
            ActionType.MAXIMIZE_WINDOW: "⬆️ Maximize Window",
            ActionType.RESTORE_WINDOW: "↩️ Restore Window",
            ActionType.RESIZE_WINDOW: "📏 Resize Window",
            ActionType.MOVE_WINDOW: "📍 Move Window",
            ActionType.SEND_KEYS: "⌨️ Send Keys",
            ActionType.CLICK_ELEMENT: "👆 Click Element"
        }
        return action_texts.get(action_type, f"❓ {action_type.value if hasattr(action_type, 'value') else str(action_type)}")
    
    def _get_schedule_type_info(self, schedule_type: ScheduleType) -> str:
        """Get localized schedule type text."""
        schedule_texts = {
            ScheduleType.ONCE: "🔂 One Time",
            ScheduleType.DAILY: "📅 Daily",
            ScheduleType.WEEKLY: "📆 Weekly",
            ScheduleType.MONTHLY: "🗓️ Monthly",
            ScheduleType.CUSTOM: "⚙️ Custom"
        }
        return schedule_texts.get(schedule_type, f"❓ {schedule_type.value if hasattr(schedule_type, 'value') else str(schedule_type)}")
    
    def _format_datetime(self, dt: Optional[datetime]) -> str:
        """Format datetime for display."""
        if not dt:
            return "Never"
        
        now = datetime.now()
        if dt.date() == now.date():
            return f"Today {dt.strftime('%H:%M:%S')}"
        elif dt.year == now.year:
            return dt.strftime("%m/%d %H:%M:%S")
        else:
            return dt.strftime("%Y/%m/%d %H:%M:%S")
    
    def _create_basic_info_section(self, task: Task) -> None:
        """Create basic task information section."""
        section = self._create_section("Basic Information", "ℹ️")
        
        self._create_info_row(section, "Task Name", task.name, "#000000", ("Segoe UI", 10, "bold"))
        self._create_info_row(section, "Task ID", task.id, "#666666", ("Consolas", 9))
        self._create_info_row(section, "Target App", task.target_app, "#000000")
        
        # Status with color
        status_text, status_color = self._get_status_info(task.status)
        self._create_info_row(section, "Status", status_text, status_color, ("Segoe UI", 10, "bold"))
        
        # Action type
        action_text = self._get_action_type_info(task.action_type)
        self._create_info_row(section, "Action Type", action_text)
        
        self._create_info_row(section, "Created", self._format_datetime(task.created_at))
        self._create_info_row(section, "Retry Count", f"{task.retry_count}/{task.max_retries}")
    
    def _create_schedule_section(self, task: Task) -> None:
        """Create schedule information section."""
        section = self._create_section("Schedule Configuration", "⏰")
        
        schedule = task.schedule
        schedule_text = self._get_schedule_type_info(schedule.schedule_type)
        self._create_info_row(section, "Type", schedule_text)
        
        self._create_info_row(section, "Start Time", self._format_datetime(schedule.start_time))
        
        if schedule.end_time:
            self._create_info_row(section, "End Time", self._format_datetime(schedule.end_time))
        
        if schedule.interval:
            interval_text = str(schedule.interval)
            self._create_info_row(section, "Interval", interval_text)
        
        if schedule.days_of_week:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            selected_days = [days[i] for i in schedule.days_of_week]
            self._create_info_row(section, "Days of Week", ", ".join(selected_days))
        
        repeat_text = "Yes" if schedule.repeat_enabled else "No"
        self._create_info_row(section, "Repeat Enabled", repeat_text)
    
    def _create_execution_section(self, task: Task) -> None:
        """Create execution information section."""
        section = self._create_section("Execution Information", "🔄")
        
        last_exec_text = self._format_datetime(task.last_executed)
        last_exec_color = "#28A745" if task.last_executed else "#999999"
        self._create_info_row(section, "Last Executed", last_exec_text, last_exec_color)
        
        next_exec_text = self._format_datetime(task.next_execution)
        next_exec_color = "#007ACC" if task.next_execution else "#999999"
        self._create_info_row(section, "Next Execution", next_exec_text, next_exec_color)
        
        # Execution history button
        history_frame = ttk.Frame(section)
        history_frame.pack(fill=tk.X, pady=(10, 0))
        
        history_button = ttk.Button(
            history_frame,
            text="📊 View Execution History",
            command=lambda: self._show_execution_history(task.id)
        )
        history_button.pack(side=tk.LEFT)
    
    def _create_parameters_section(self, task: Task) -> None:
        """Create action parameters section."""
        if not task.action_params:
            return
        
        section = self._create_section("Action Parameters", "⚙️")
        
        for key, value in task.action_params.items():
            # Format value based on type
            if isinstance(value, dict):
                value_text = f"{len(value)} items"
            elif isinstance(value, list):
                value_text = f"{len(value)} items"
            elif isinstance(value, str) and len(value) > 50:
                value_text = f"{value[:47]}..."
            else:
                value_text = str(value)
            
            self._create_info_row(section, key.replace("_", " ").title(), value_text)
    
    def _show_execution_history(self, task_id: str) -> None:
        """Show execution history for the task."""
        # TODO: Implement execution history dialog
        print(f"Show execution history for task: {task_id}")
    
    def display_task(self, task: Task) -> None:
        """
        Display detailed information for a task.
        
        Args:
            task: Task to display
        """
        self.current_task = task
        self._clear_content()
        
        # Create all sections
        self._create_basic_info_section(task)
        self._create_schedule_section(task)
        self._create_execution_section(task)
        self._create_parameters_section(task)
        
        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def display_multiple_tasks(self, task_ids: List[str]) -> None:
        """
        Display information for multiple selected tasks.
        
        Args:
            task_ids: List of task IDs
        """
        self.current_task = None
        self._show_multi_selection_state(len(task_ids))
    
    def clear_display(self) -> None:
        """Clear the display and show empty state."""
        self.current_task = None
        self._show_empty_state()
    
    def refresh_current_task(self) -> None:
        """Refresh the currently displayed task."""
        if self.current_task:
            # Reload task from manager
            updated_task = self.task_manager.get_task(self.current_task.id)
            if updated_task:
                self.display_task(updated_task)
            else:
                self.clear_display()
    
    def get_current_task(self) -> Optional[Task]:
        """Get the currently displayed task."""
        return self.current_task