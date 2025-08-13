"""
Control buttons widget implementation for task operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable
from datetime import datetime

from src.models.task import Task, TaskStatus
from src.core.task_manager import TaskManager


class ControlButtonsWidget(ttk.Frame):
    """Widget for task operation control buttons."""
    
    def __init__(self, parent: tk.Widget, task_manager: TaskManager):
        """
        Initialize control buttons widget.
        
        Args:
            parent: Parent widget
            task_manager: Task manager instance
        """
        super().__init__(parent)
        self.task_manager = task_manager
        self.selected_task_ids: List[str] = []
        
        # Callbacks
        self.on_task_created: Optional[Callable[[], None]] = None
        self.on_task_updated: Optional[Callable[[], None]] = None
        self.on_task_deleted: Optional[Callable[[], None]] = None
        self.on_task_executed: Optional[Callable[[], None]] = None
        
        self._setup_ui()
        self._update_button_states()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        
        # Primary action buttons frame
        primary_frame = ttk.LabelFrame(self, text="Task Operations", padding=10)
        primary_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Create task button
        self.new_button = ttk.Button(
            primary_frame,
            text="New Task",
            command=self._create_new_task,
            width=15
        )
        self.new_button.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="ew")
        
        # Edit task button
        self.edit_button = ttk.Button(
            primary_frame,
            text="Edit Task",
            command=self._edit_selected_task,
            state="disabled",
            width=15
        )
        self.edit_button.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Delete task button
        self.delete_button = ttk.Button(
            primary_frame,
            text="Delete",
            command=self._delete_selected_tasks,
            state="disabled",
            width=15
        )
        self.delete_button.grid(row=1, column=0, padx=(0, 5), pady=2, sticky="ew")
        
        # Execute task button
        self.execute_button = ttk.Button(
            primary_frame,
            text="Execute Now",
            command=self._execute_selected_task,
            state="disabled",
            width=15
        )
        self.execute_button.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        # Configure column weights for primary frame
        for i in range(2):
            primary_frame.grid_columnconfigure(i, weight=1)
        
        # Status display
        self.status_frame = ttk.Frame(self)
        self.status_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="No tasks selected",
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        self.status_label.pack(side="left")
    
    def set_selected_tasks(self, task_ids: List[str]) -> None:
        """
        Set the currently selected tasks.
        
        Args:
            task_ids: List of selected task IDs
        """
        self.selected_task_ids = task_ids
        self._update_button_states()
        self._update_status_display()
    
    def _update_button_states(self) -> None:
        """Update button states based on selection."""
        has_selection = len(self.selected_task_ids) > 0
        single_selection = len(self.selected_task_ids) == 1
        
        # Primary operations
        self.edit_button.config(state="normal" if single_selection else "disabled")
        self.delete_button.config(state="normal" if has_selection else "disabled")
        self.execute_button.config(state="normal" if single_selection else "disabled")
    
    def _update_status_display(self) -> None:
        """Update the status display."""
        count = len(self.selected_task_ids)
        if count == 0:
            self.status_label.config(text="No tasks selected")
        elif count == 1:
            task_id = self.selected_task_ids[0]
            task = self.task_manager.get_task(task_id)
            if task:
                self.status_label.config(text=f"Selected: {task.name}")
            else:
                self.status_label.config(text=f"Selected: {task_id}")
        else:
            self.status_label.config(text=f"Selected {count} tasks")
    
    def _on_task_saved(self, task: Task) -> None:
        """Handle task save from dialog."""
        try:
            if task.id in [t.id for t in self.task_manager.get_all_tasks()]:
                # Update existing task - replace the entire task in storage
                existing_task = self.task_manager.get_task(task.id)
                if existing_task:
                    existing_task.name = task.name
                    existing_task.target_app = task.target_app
                    existing_task.action_sequence = task.action_sequence
                    existing_task.schedule = task.schedule
                    existing_task.status = task.status
                    existing_task.execution_options = task.execution_options
                    # Save the updated task
                    if self.task_manager._task_storage:
                        self.task_manager._task_storage.save_task(existing_task)
            else:
                # Create new task
                self.task_manager.create_task_with_sequence(
                    name=task.name,
                    target_app=task.target_app,
                    action_sequence=task.action_sequence,
                    schedule=task.schedule,
                    execution_options=task.execution_options
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save task:\n{str(e)}")
            raise
    
    def _create_new_task(self) -> None:
        """Create a new task."""
        try:
            from src.gui.dialogs.schedule_dialog import ScheduleDialog
            
            # Create and show the schedule dialog
            dialog = ScheduleDialog(self, on_save=self._on_task_saved)
            result = dialog.show()
            
            if result:
                # Task was created successfully
                if self.on_task_created:
                    self.on_task_created()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create new task:\n{str(e)}")
    
    def _edit_selected_task(self) -> None:
        """Edit the selected task."""
        if len(self.selected_task_ids) != 1:
            return
        
        task_id = self.selected_task_ids[0]
        task = self.task_manager.get_task(task_id)
        
        if not task:
            messagebox.showerror("Error", f"Task not found: {task_id}")
            return
        
        try:
            from src.gui.dialogs.schedule_dialog import ScheduleDialog
            
            # Create and show the schedule dialog with existing task
            dialog = ScheduleDialog(self, task=task, on_save=self._on_task_saved)
            result = dialog.show()
            
            if result:
                # Task was updated successfully
                if self.on_task_updated:
                    self.on_task_updated()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit task:\n{str(e)}")
    
    def _delete_selected_tasks(self) -> None:
        """Delete the selected tasks."""
        if not self.selected_task_ids:
            return
        
        count = len(self.selected_task_ids)
        task_names = []
        
        # Get task names for confirmation
        for task_id in self.selected_task_ids:
            task = self.task_manager.get_task(task_id)
            if task:
                task_names.append(task.name)
            else:
                task_names.append(task_id)
        
        # Confirmation dialog
        if count == 1:
            message = f"Are you sure you want to delete this task?\n\n{task_names[0]}"
        else:
            message = f"Are you sure you want to delete {count} tasks?\n\n" + "\n".join(f"• {name}" for name in task_names[:5])
            if count > 5:
                message += f"\n... and {count - 5} more tasks"
        
        if not messagebox.askyesno("Confirm Deletion", message):
            return
        
        try:
            deleted_count = 0
            
            for task_id in self.selected_task_ids:
                if self.task_manager.delete_task(task_id):
                    deleted_count += 1
            
            if deleted_count > 0:
                messagebox.showinfo("Success", f"Successfully deleted {deleted_count} task(s)")
                if self.on_task_deleted:
                    self.on_task_deleted()
            else:
                messagebox.showwarning("Warning", "No tasks were deleted")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete tasks:\n{str(e)}")
    
    def _execute_selected_task(self) -> None:
        """Execute the selected task immediately."""
        if len(self.selected_task_ids) != 1:
            return
        
        task_id = self.selected_task_ids[0]
        task = self.task_manager.get_task(task_id)
        
        if not task:
            messagebox.showerror("Error", f"Task not found: {task_id}")
            return
        
        if task.status == TaskStatus.RUNNING:
            messagebox.showwarning("Warning", f"Task '{task.name}' is already running")
            return
        
        if task.status == TaskStatus.DISABLED:
            if not messagebox.askyesno("Confirm Execution", f"Task '{task.name}' is disabled.\n\nDo you want to execute it anyway?"):
                return
        
        try:
            # Execute the task
            result = self.task_manager.execute_task_immediately(task_id)
            
            if not result:
                # Get more detailed error information
                task_after = self.task_manager.get_task(task_id)
                error_details = f"Task '{task.name}' execution failed"
                if task_after and hasattr(task_after, 'last_error'):
                    error_details += f"\nError: {task_after.last_error}"
                messagebox.showerror("Execution Failed", error_details)
            
            if self.on_task_executed:
                self.on_task_executed()
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            messagebox.showerror("Error", f"Failed to execute task:\n{str(e)}\n\nDetails:\n{error_trace}")
    
    def set_callbacks(self, 
                     on_task_created: Optional[Callable[[], None]] = None,
                     on_task_updated: Optional[Callable[[], None]] = None,
                     on_task_deleted: Optional[Callable[[], None]] = None,
                     on_task_executed: Optional[Callable[[], None]] = None) -> None:
        """
        Set callback functions for task operations.
        
        Args:
            on_task_created: Called when a task is created
            on_task_updated: Called when a task is updated
            on_task_deleted: Called when a task is deleted
            on_task_executed: Called when a task is executed
        """
        self.on_task_created = on_task_created
        self.on_task_updated = on_task_updated
        self.on_task_deleted = on_task_deleted
        self.on_task_executed = on_task_executed