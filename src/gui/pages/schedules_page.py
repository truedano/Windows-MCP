"""
Schedules management page implementation.
"""

import tkinter as tk
from tkinter import ttk
from typing import List

from src.gui.page_manager import BasePage
from src.gui.widgets.task_list_widget import TaskListWidget
from src.gui.widgets.task_detail_widget import TaskDetailWidget
from src.core.task_manager import TaskManager


class SchedulesPage(BasePage):
    """Schedules management page."""
    
    def __init__(self, parent: tk.Widget, task_manager: TaskManager):
        """Initialize schedules page."""
        super().__init__(parent, "Schedules", "排程管理")
        self.task_manager = task_manager
        self.task_list_widget = None
        self.task_detail_widget = None
    
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
        
        # Task list widget
        task_list_frame = ttk.LabelFrame(main_frame, text="任務清單", padding=5)
        task_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        task_list_frame.grid_rowconfigure(0, weight=1)
        task_list_frame.grid_columnconfigure(0, weight=1)
        
        self.task_list_widget = TaskListWidget(task_list_frame, self.task_manager)
        self.task_list_widget.grid(row=0, column=0, sticky="nsew")
        self.task_list_widget.set_selection_callback(self._on_task_selection_changed)
        
        # Task detail and control panel
        detail_frame = ttk.LabelFrame(main_frame, text="Task Details", padding=5)
        detail_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        detail_frame.grid_rowconfigure(1, weight=1)
        detail_frame.grid_columnconfigure(0, weight=1)
        
        # Control buttons
        control_frame = ttk.Frame(detail_frame)
        control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.new_button = ttk.Button(
            control_frame,
            text="New Task",
            command=self._create_new_task,
            width=12
        )
        self.new_button.pack(side="left", padx=(0, 5))
        
        self.edit_button = ttk.Button(
            control_frame,
            text="Edit Task",
            command=self._edit_selected_task,
            state="disabled",
            width=12
        )
        self.edit_button.pack(side="left", padx=(0, 5))
        
        self.delete_button = ttk.Button(
            control_frame,
            text="Delete Task",
            command=self._delete_selected_tasks,
            state="disabled",
            width=12
        )
        self.delete_button.pack(side="left", padx=(0, 5))
        
        self.execute_button = ttk.Button(
            control_frame,
            text="Execute Now",
            command=self._execute_selected_task,
            state="disabled",
            width=12
        )
        self.execute_button.pack(side="left")
        
        # Task detail widget
        self.task_detail_widget = TaskDetailWidget(detail_frame, self.task_manager)
        self.task_detail_widget.grid(row=1, column=0, sticky="nsew")
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if self.task_list_widget:
            self.task_list_widget.refresh_tasks()
        if self.task_detail_widget:
            self.task_detail_widget.refresh_current_task()
    
    def _on_task_selection_changed(self, selected_task_ids: List[str]) -> None:
        """Handle task selection changes."""
        # Update button states
        has_selection = len(selected_task_ids) > 0
        single_selection = len(selected_task_ids) == 1
        
        self.edit_button.config(state="normal" if single_selection else "disabled")
        self.delete_button.config(state="normal" if has_selection else "disabled")
        self.execute_button.config(state="normal" if single_selection else "disabled")
        
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
    
    
    def _create_new_task(self) -> None:
        """Create a new task."""
        # TODO: Implement task creation dialog
        print("Create new task - TODO: Implement task creation dialog")
    
    def _edit_selected_task(self) -> None:
        """Edit the selected task."""
        selected_ids = self.task_list_widget.get_selected_task_ids()
        if len(selected_ids) == 1:
            # TODO: Implement task editing dialog
            print(f"Edit task {selected_ids[0]} - TODO: Implement task editing dialog")
    
    def _delete_selected_tasks(self) -> None:
        """Delete the selected tasks."""
        selected_ids = self.task_list_widget.get_selected_task_ids()
        if selected_ids:
            # TODO: Implement confirmation dialog and deletion
            print(f"Delete tasks {selected_ids} - TODO: Implement confirmation dialog")
    
    def _execute_selected_task(self) -> None:
        """Execute the selected task immediately."""
        selected_ids = self.task_list_widget.get_selected_task_ids()
        if len(selected_ids) == 1:
            task_id = selected_ids[0]
            try:
                # TODO: Implement immediate task execution
                print(f"Execute task {task_id} - TODO: Implement immediate execution")
            except Exception as e:
                print(f"Error executing task {task_id}: {e}")