"""
Schedule detail page implementation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from datetime import datetime

from src.gui.page_manager import BasePage
from src.models.task import Task, TaskStatus
from src.models.schedule import ScheduleType
from src.core.task_manager import TaskManager


class ScheduleDetailPage(BasePage):
    """Schedule detail page with modern web-style design."""
    
    def __init__(self, parent: tk.Widget, task_manager: TaskManager):
        """Initialize schedule detail page."""
        super().__init__(parent, "ScheduleDetail", "排程詳細")
        self.task_manager = task_manager
        self.current_task: Optional[Task] = None
        self.on_back_clicked: Optional[Callable[[], None]] = None
        self.on_edit_clicked: Optional[Callable[[str], None]] = None
        
        # Sub-widgets
        self.schedule_info_widget: Optional[ScheduleInfoWidget] = None
        self.options_panel: Optional[OptionsPanel] = None
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Configure grid weights
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Header section
        self._create_header()
        
        # Main content area
        self._create_main_content()
        
        # Action buttons
        self._create_action_buttons()
    
    def _create_header(self) -> None:
        """Create the header section."""
        header_frame = ttk.Frame(self.frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Page title
        title_label = ttk.Label(
            header_frame,
            text="Schedule Details",
            font=("Segoe UI", 24, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame,
            text="View and manage the details of your scheduled tasks.",
            font=("Segoe UI", 11),
            foreground="#666666"
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
    
    def _create_main_content(self) -> None:
        """Create the main content area."""
        # Main content frame with padding
        content_frame = ttk.Frame(self.frame)
        content_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Schedule info widget
        self.schedule_info_widget = ScheduleInfoWidget(content_frame)
        self.schedule_info_widget.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        # Options panel
        self.options_panel = OptionsPanel(content_frame)
        self.options_panel.grid(row=1, column=0, sticky="ew")
    
    def _create_action_buttons(self) -> None:
        """Create the action buttons."""
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure(0, weight=1)
        
        # Button container (right-aligned)
        button_container = ttk.Frame(button_frame)
        button_container.grid(row=0, column=0, sticky="e")
        
        # Back button
        self.back_button = ttk.Button(
            button_container,
            text="← Back",
            command=self._on_back_clicked,
            width=12
        )
        self.back_button.pack(side="left", padx=(0, 10))
        
        # Edit button
        self.edit_button = ttk.Button(
            button_container,
            text="✏️ Edit",
            command=self._on_edit_clicked,
            width=12
        )
        self.edit_button.pack(side="left")
    
    def load_task(self, task_id: str) -> bool:
        """
        Load and display a task.
        
        Args:
            task_id: ID of the task to load
            
        Returns:
            bool: True if task was loaded successfully
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            messagebox.showerror("Error", f"Task not found: {task_id}")
            return False
        
        self.current_task = task
        self._update_display()
        return True
    
    def _update_display(self) -> None:
        """Update the display with current task information."""
        if not self.current_task:
            return
        
        # Update schedule info
        if self.schedule_info_widget:
            self.schedule_info_widget.update_info(self.current_task)
        
        # Update options panel
        if self.options_panel:
            self.options_panel.update_options(self.current_task)
    
    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        if self.on_back_clicked:
            self.on_back_clicked()
    
    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        if self.current_task and self.on_edit_clicked:
            self.on_edit_clicked(self.current_task.id)
    
    def set_navigation_callbacks(self, 
                                on_back: Optional[Callable[[], None]] = None,
                                on_edit: Optional[Callable[[str], None]] = None) -> None:
        """
        Set navigation callback functions.
        
        Args:
            on_back: Called when back button is clicked
            on_edit: Called when edit button is clicked
        """
        self.on_back_clicked = on_back
        self.on_edit_clicked = on_edit
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if self.current_task:
            # Reload task data
            updated_task = self.task_manager.get_task(self.current_task.id)
            if updated_task:
                self.current_task = updated_task
                self._update_display()
            else:
                # Task was deleted, go back
                if self.on_back_clicked:
                    self.on_back_clicked()


class ScheduleInfoWidget(ttk.Frame):
    """Widget for displaying schedule basic information."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize schedule info widget."""
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.grid_columnconfigure(1, weight=1)
        
        # Schedule Name
        self._create_info_row(0, "Schedule Name", "")
        
        # Target Window
        self._create_info_row(1, "Target Window", "")
        
        # Trigger Time
        self._create_info_row(2, "Trigger Time", "")
        
        # Action
        self._create_info_row(3, "Action", "")
        
        # Status
        self._create_info_row(4, "Status", "")
        
        # Created
        self._create_info_row(5, "Created", "")
        
        # Last Executed
        self._create_info_row(6, "Last Executed", "")
        
        # Next Execution
        self._create_info_row(7, "Next Execution", "")
    
    def _create_info_row(self, row: int, label_text: str, value_text: str) -> None:
        """Create an information row."""
        # Label
        label = ttk.Label(
            self,
            text=label_text,
            font=("Segoe UI", 12, "bold"),
            foreground="#333333"
        )
        label.grid(row=row, column=0, sticky="w", pady=8)
        
        # Value
        value = ttk.Label(
            self,
            text=value_text,
            font=("Segoe UI", 14),
            foreground="#000000"
        )
        value.grid(row=row, column=1, sticky="w", padx=(20, 0), pady=8)
        
        # Store references for updates
        setattr(self, f"_label_{row}", label)
        setattr(self, f"_value_{row}", value)
    
    def update_info(self, task: Task) -> None:
        """Update the displayed information."""
        # Schedule Name
        self._value_0.config(text=task.name)
        
        # Target Window
        self._value_1.config(text=task.target_app)
        
        # Trigger Time
        trigger_text = self._format_trigger_time(task)
        self._value_2.config(text=trigger_text)
        
        # Action
        action_text = self._format_action(task)
        self._value_3.config(text=action_text)
        
        # Status
        status_text, status_color = self._format_status(task.status)
        self._value_4.config(text=status_text, foreground=status_color)
        
        # Created
        created_text = task.created_at.strftime("%Y-%m-%d %H:%M:%S")
        self._value_5.config(text=created_text)
        
        # Last Executed
        if task.last_executed:
            last_exec_text = task.last_executed.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_exec_text = "Never"
        self._value_6.config(text=last_exec_text)
        
        # Next Execution
        if task.next_execution:
            next_exec_text = task.next_execution.strftime("%Y-%m-%d %H:%M:%S")
        else:
            next_exec_text = "Not scheduled"
        self._value_7.config(text=next_exec_text)
    
    def _format_trigger_time(self, task: Task) -> str:
        """Format trigger time for display."""
        schedule = task.schedule
        
        if schedule.schedule_type == ScheduleType.ONCE:
            return f"Once at {schedule.start_time.strftime('%Y-%m-%d %H:%M')}"
        elif schedule.schedule_type == ScheduleType.DAILY:
            return f"Every day at {schedule.start_time.strftime('%H:%M')}"
        elif schedule.schedule_type == ScheduleType.WEEKLY:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            if schedule.days_of_week:
                day_names = [days[i] for i in schedule.days_of_week]
                return f"Every {', '.join(day_names)} at {schedule.start_time.strftime('%H:%M')}"
            else:
                return f"Weekly at {schedule.start_time.strftime('%H:%M')}"
        elif schedule.schedule_type == ScheduleType.MONTHLY:
            return f"Monthly on day {schedule.start_time.day} at {schedule.start_time.strftime('%H:%M')}"
        else:
            return f"Custom schedule starting {schedule.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def _format_action(self, task: Task) -> str:
        """Format action for display."""
        action_names = {
            "LAUNCH_APP": "Launch Application",
            "CLOSE_APP": "Close Application",
            "FOCUS_WINDOW": "Focus Window",
            "MINIMIZE_WINDOW": "Minimize Window",
            "MAXIMIZE_WINDOW": "Maximize Window",
            "RESTORE_WINDOW": "Restore Window",
            "RESIZE_WINDOW": "Resize Window",
            "MOVE_WINDOW": "Move Window",
            "SEND_KEYS": "Send Keys",
            "CLICK_ELEMENT": "Click Element"
        }
        
        action_type = task.action_type.value if hasattr(task.action_type, 'value') else str(task.action_type)
        return action_names.get(action_type, action_type)
    
    def _format_status(self, status: TaskStatus) -> tuple:
        """Format status for display with color."""
        status_info = {
            TaskStatus.PENDING: ("⏳ Pending", "#FFA500"),
            TaskStatus.RUNNING: ("▶️ Running", "#007ACC"),
            TaskStatus.COMPLETED: ("✅ Completed", "#28A745"),
            TaskStatus.FAILED: ("❌ Failed", "#DC3545"),
            TaskStatus.DISABLED: ("⏸️ Disabled", "#6C757D")
        }
        return status_info.get(status, ("❓ Unknown", "#000000"))


class OptionsPanel(ttk.LabelFrame):
    """Widget for displaying schedule options."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize options panel."""
        super().__init__(parent, text="Options", padding=20)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.grid_columnconfigure(1, weight=1)
        
        # Repeat option
        self._create_option_row(0, "Repeat", "")
        
        # Conditional Trigger option
        self._create_option_row(1, "Conditional Trigger", "")
        
        # Retry option
        self._create_option_row(2, "Retry on Failure", "")
        
        # End time option
        self._create_option_row(3, "End Time", "")
    
    def _create_option_row(self, row: int, label_text: str, value_text: str) -> None:
        """Create an option row."""
        # Label
        label = ttk.Label(
            self,
            text=label_text,
            font=("Segoe UI", 11, "bold"),
            foreground="#333333"
        )
        label.grid(row=row, column=0, sticky="w", pady=5)
        
        # Value
        value = ttk.Label(
            self,
            text=value_text,
            font=("Segoe UI", 11),
            foreground="#666666"
        )
        value.grid(row=row, column=1, sticky="e", pady=5)
        
        # Store references for updates
        setattr(self, f"_option_label_{row}", label)
        setattr(self, f"_option_value_{row}", value)
    
    def update_options(self, task: Task) -> None:
        """Update the displayed options."""
        schedule = task.schedule
        
        # Repeat
        if schedule.repeat_enabled:
            repeat_text = "✅ Enabled"
        else:
            repeat_text = "❌ Disabled"
        self._option_value_0.config(text=repeat_text)
        
        # Conditional Trigger
        if schedule.conditional_trigger and schedule.conditional_trigger.enabled:
            condition_text = f"✅ {schedule.conditional_trigger.condition_type.value}"
            if schedule.conditional_trigger.condition_value:
                condition_text += f": '{schedule.conditional_trigger.condition_value}'"
        else:
            condition_text = "❌ Disabled"
        self._option_value_1.config(text=condition_text)
        
        # Retry on Failure
        if task.max_retries > 0:
            retry_text = f"✅ Up to {task.max_retries} times"
            if task.retry_count > 0:
                retry_text += f" (attempted {task.retry_count})"
        else:
            retry_text = "❌ Disabled"
        self._option_value_2.config(text=retry_text)
        
        # End Time
        if schedule.end_time:
            end_time_text = f"⏰ {schedule.end_time.strftime('%Y-%m-%d %H:%M')}"
        else:
            end_time_text = "♾️ No end time"
        self._option_value_3.config(text=end_time_text)