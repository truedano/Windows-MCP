"""
Schedules management page implementation.
"""

import tkinter as tk
from tkinter import ttk
from typing import List

from src.gui.page_manager import BasePage
from src.gui.widgets.task_list_widget import TaskListWidget
from src.gui.widgets.task_detail_widget import TaskDetailWidget
from src.gui.widgets.control_buttons_widget import ControlButtonsWidget
from src.core.task_manager import TaskManager


class SchedulesPage(BasePage):
    """Schedules management page."""
    
    def __init__(self, parent: tk.Widget, task_manager: TaskManager):
        """Initialize schedules page."""
        super().__init__(parent, "Schedules", "排程管理")
        self.task_manager = task_manager
        self.task_list_widget = None
        self.task_detail_widget = None
        self.control_buttons_widget = None
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Configure grid weights
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="Schedule Management",
            font=("Segoe UI", 18, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="管理排程任務、建立和編輯排程",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.grid(row=0, column=1, sticky="w", pady=(0, 10))
        
        # Main content frame
        main_frame = ttk.Frame(self.frame)
        main_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)
        
        # Task list widget
        task_list_frame = ttk.LabelFrame(main_frame, text="Task List", padding=5)
        task_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        task_list_frame.grid_rowconfigure(0, weight=1)
        task_list_frame.grid_columnconfigure(0, weight=1)
        
        self.task_list_widget = TaskListWidget(task_list_frame, self.task_manager)
        self.task_list_widget.grid(row=0, column=0, sticky="nsew")
        self.task_list_widget.set_selection_callback(self._on_task_selection_changed)
        
        # Task detail panel
        detail_frame = ttk.LabelFrame(main_frame, text="Task Details", padding=5)
        detail_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        detail_frame.grid_rowconfigure(0, weight=1)
        detail_frame.grid_columnconfigure(0, weight=1)
        
        # Task detail widget
        self.task_detail_widget = TaskDetailWidget(detail_frame, self.task_manager)
        self.task_detail_widget.grid(row=0, column=0, sticky="nsew")
        
        # Control buttons panel
        control_frame = ttk.LabelFrame(main_frame, text="Task Operations", padding=5)
        control_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        control_frame.grid_rowconfigure(0, weight=1)
        control_frame.grid_columnconfigure(0, weight=1)
        
        # Control buttons widget
        self.control_buttons_widget = ControlButtonsWidget(control_frame, self.task_manager)
        self.control_buttons_widget.grid(row=0, column=0, sticky="nsew")
        
        # Set up callbacks
        self.control_buttons_widget.set_callbacks(
            on_task_created=self._on_task_operation_completed,
            on_task_updated=self._on_task_operation_completed,
            on_task_deleted=self._on_task_operation_completed,
            on_task_executed=self._on_task_operation_completed
        )
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if self.task_list_widget:
            self.task_list_widget.refresh_tasks()
        if self.task_detail_widget:
            self.task_detail_widget.refresh_current_task()
    
    def _on_task_selection_changed(self, selected_task_ids: List[str]) -> None:
        """Handle task selection changes."""
        # Update control buttons
        if self.control_buttons_widget:
            self.control_buttons_widget.set_selected_tasks(selected_task_ids)
        
        # Update detail display
        if not selected_task_ids:
            self.task_detail_widget.clear_display()
        elif len(selected_task_ids) == 1:
            task_id = selected_task_ids[0]
            task = self.task_manager.get_task(task_id)
            if task:
                self.task_detail_widget.display_task(task)
            else:
                self.task_detail_widget.clear_display()
        else:
            self.task_detail_widget.display_multiple_tasks(selected_task_ids)
    
    def _on_task_operation_completed(self) -> None:
        """Handle completion of task operations."""
        # Refresh the task list to reflect changes
        if self.task_list_widget:
            self.task_list_widget.refresh_tasks()
        
        # Refresh the detail widget if it's showing a task
        if self.task_detail_widget:
            self.task_detail_widget.refresh_current_task()
        
        # Clear selection if tasks were deleted
        selected_ids = self.task_list_widget.get_selected_task_ids() if self.task_list_widget else []
        if selected_ids:
            # Verify that selected tasks still exist
            valid_ids = []
            for task_id in selected_ids:
                if self.task_manager.get_task(task_id):
                    valid_ids.append(task_id)
            
            if len(valid_ids) != len(selected_ids):
                # Some tasks were deleted, update selection
                if self.control_buttons_widget:
                    self.control_buttons_widget.set_selected_tasks(valid_ids)
                
                if not valid_ids:
                    self.task_detail_widget.clear_display()
                elif len(valid_ids) == 1:
                    task = self.task_manager.get_task(valid_ids[0])
                    if task:
                        self.task_detail_widget.display_task(task)
                else:
                    self.task_detail_widget.display_multiple_tasks(valid_ids)