"""
Control buttons widget implementation for task operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable, Dict, Any
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
            text="🆕 New Task",
            command=self._create_new_task,
            width=15
        )
        self.new_button.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="ew")
        
        # Edit task button
        self.edit_button = ttk.Button(
            primary_frame,
            text="✏️ Edit Task",
            command=self._edit_selected_task,
            state="disabled",
            width=15
        )
        self.edit_button.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Duplicate task button
        self.duplicate_button = ttk.Button(
            primary_frame,
            text="📋 Duplicate",
            command=self._duplicate_selected_task,
            state="disabled",
            width=15
        )
        self.duplicate_button.grid(row=0, column=2, padx=5, pady=2, sticky="ew")
        
        # Delete task button
        self.delete_button = ttk.Button(
            primary_frame,
            text="🗑️ Delete",
            command=self._delete_selected_tasks,
            state="disabled",
            width=15
        )
        self.delete_button.grid(row=1, column=0, padx=(0, 5), pady=2, sticky="ew")
        
        # Execute task button
        self.execute_button = ttk.Button(
            primary_frame,
            text="▶️ Execute Now",
            command=self._execute_selected_task,
            state="disabled",
            width=15
        )
        self.execute_button.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        # Stop task button
        self.stop_button = ttk.Button(
            primary_frame,
            text="⏹️ Stop",
            command=self._stop_selected_task,
            state="disabled",
            width=15
        )
        self.stop_button.grid(row=1, column=2, padx=5, pady=2, sticky="ew")
        
        # Configure column weights for primary frame
        for i in range(3):
            primary_frame.grid_columnconfigure(i, weight=1)
        
        # Task status control frame
        status_frame = ttk.LabelFrame(self, text="Status Control", padding=10)
        status_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Enable/Disable buttons
        self.enable_button = ttk.Button(
            status_frame,
            text="✅ Enable",
            command=self._enable_selected_tasks,
            state="disabled",
            width=15
        )
        self.enable_button.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="ew")
        
        self.disable_button = ttk.Button(
            status_frame,
            text="⏸️ Disable",
            command=self._disable_selected_tasks,
            state="disabled",
            width=15
        )
        self.disable_button.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Reset retry counter button
        self.reset_retry_button = ttk.Button(
            status_frame,
            text="🔄 Reset Retry",
            command=self._reset_retry_counter,
            state="disabled",
            width=15
        )
        self.reset_retry_button.grid(row=0, column=2, padx=5, pady=2, sticky="ew")
        
        # Configure column weights for status frame
        for i in range(3):
            status_frame.grid_columnconfigure(i, weight=1)
        
        # Batch operations frame
        batch_frame = ttk.LabelFrame(self, text="Batch Operations", padding=10)
        batch_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        # Export tasks button
        self.export_button = ttk.Button(
            batch_frame,
            text="📤 Export Tasks",
            command=self._export_selected_tasks,
            state="disabled",
            width=15
        )
        self.export_button.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="ew")
        
        # Import tasks button
        self.import_button = ttk.Button(
            batch_frame,
            text="📥 Import Tasks",
            command=self._import_tasks,
            width=15
        )
        self.import_button.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Select all button
        self.select_all_button = ttk.Button(
            batch_frame,
            text="☑️ Select All",
            command=self._select_all_tasks,
            width=15
        )
        self.select_all_button.grid(row=0, column=2, padx=5, pady=2, sticky="ew")
        
        # Configure column weights for batch frame
        for i in range(3):
            batch_frame.grid_columnconfigure(i, weight=1)
        
        # Status display
        self.status_frame = ttk.Frame(self)
        self.status_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="No tasks selected",
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        self.status_label.pack(side="left")
        
        # Progress bar for operations
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            mode="determinate"
        )
        # Initially hidden
    
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
        multiple_selection = len(self.selected_task_ids) > 1
        
        # Primary operations
        self.edit_button.config(state="normal" if single_selection else "disabled")
        self.duplicate_button.config(state="normal" if single_selection else "disabled")
        self.delete_button.config(state="normal" if has_selection else "disabled")
        self.execute_button.config(state="normal" if single_selection else "disabled")
        
        # Status control
        self.enable_button.config(state="normal" if has_selection else "disabled")
        self.disable_button.config(state="normal" if has_selection else "disabled")
        self.reset_retry_button.config(state="normal" if has_selection else "disabled")
        
        # Batch operations
        self.export_button.config(state="normal" if has_selection else "disabled")
        
        # Check if any selected task is running
        running_tasks = self._get_running_tasks()
        self.stop_button.config(state="normal" if running_tasks else "disabled")
    
    def _get_running_tasks(self) -> List[str]:
        """Get list of running task IDs from selection."""
        running_tasks = []
        for task_id in self.selected_task_ids:
            task = self.task_manager.get_task(task_id)
            if task and task.status == TaskStatus.RUNNING:
                running_tasks.append(task_id)
        return running_tasks
    
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
    
    def _show_progress(self, show: bool = True) -> None:
        """Show or hide progress bar."""
        if show:
            self.progress_bar.pack(side="right", padx=(10, 0), fill="x", expand=True)
        else:
            self.progress_bar.pack_forget()
    
    def _on_task_saved(self, task: Task) -> None:
        """Handle task save from dialog."""
        try:
            if task.id in [t.id for t in self.task_manager.get_all_tasks()]:
                # Update existing task
                self.task_manager.update_task(task.id, task)
            else:
                # Create new task
                self.task_manager.create_task(task)
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
    
    def _duplicate_selected_task(self) -> None:
        """Duplicate the selected task."""
        if len(self.selected_task_ids) != 1:
            return
        
        task_id = self.selected_task_ids[0]
        task = self.task_manager.get_task(task_id)
        
        if not task:
            messagebox.showerror("Error", f"Task not found: {task_id}")
            return
        
        try:
            # Create a copy of the task
            import uuid
            from copy import deepcopy
            
            new_task = deepcopy(task)
            new_task.id = str(uuid.uuid4())
            new_task.name = f"{task.name} (Copy)"
            new_task.created_at = datetime.now()
            new_task.last_executed = None
            new_task.retry_count = 0
            new_task.status = TaskStatus.PENDING
            
            # Update next execution time
            new_task.update_next_execution()
            
            # Add to task manager
            self.task_manager.add_task(new_task)
            
            messagebox.showinfo("Success", f"Task duplicated successfully!\n\nNew task: {new_task.name}")
            
            if self.on_task_created:
                self.on_task_created()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to duplicate task:\n{str(e)}")
    
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
            self._show_progress(True)
            deleted_count = 0
            
            for i, task_id in enumerate(self.selected_task_ids):
                # Update progress
                progress = (i + 1) / len(self.selected_task_ids) * 100
                self.progress_var.set(progress)
                self.update()
                
                if self.task_manager.remove_task(task_id):
                    deleted_count += 1
            
            self._show_progress(False)
            
            if deleted_count > 0:
                messagebox.showinfo("Success", f"Successfully deleted {deleted_count} task(s)")
                if self.on_task_deleted:
                    self.on_task_deleted()
            else:
                messagebox.showwarning("Warning", "No tasks were deleted")
                
        except Exception as e:
            self._show_progress(False)
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
            
            if result:
                messagebox.showinfo("Success", f"Task '{task.name}' executed successfully")
            else:
                messagebox.showwarning("Warning", f"Task '{task.name}' execution failed")
            
            if self.on_task_executed:
                self.on_task_executed()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute task:\n{str(e)}")
    
    def _stop_selected_task(self) -> None:
        """Stop the selected running task."""
        running_tasks = self._get_running_tasks()
        
        if not running_tasks:
            messagebox.showwarning("Warning", "No running tasks selected")
            return
        
        try:
            stopped_count = 0
            for task_id in running_tasks:
                task = self.task_manager.get_task(task_id)
                if task and self.task_manager.stop_task(task_id):
                    stopped_count += 1
            
            if stopped_count > 0:
                messagebox.showinfo("Success", f"Stopped {stopped_count} task(s)")
                if self.on_task_updated:
                    self.on_task_updated()
            else:
                messagebox.showwarning("Warning", "No tasks were stopped")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop tasks:\n{str(e)}")
    
    def _enable_selected_tasks(self) -> None:
        """Enable the selected tasks."""
        if not self.selected_task_ids:
            return
        
        try:
            enabled_count = 0
            for task_id in self.selected_task_ids:
                task = self.task_manager.get_task(task_id)
                if task and task.status == TaskStatus.DISABLED:
                    task.status = TaskStatus.PENDING
                    task.update_next_execution()
                    enabled_count += 1
            
            if enabled_count > 0:
                messagebox.showinfo("Success", f"Enabled {enabled_count} task(s)")
                if self.on_task_updated:
                    self.on_task_updated()
            else:
                messagebox.showinfo("Info", "No disabled tasks were selected")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable tasks:\n{str(e)}")
    
    def _disable_selected_tasks(self) -> None:
        """Disable the selected tasks."""
        if not self.selected_task_ids:
            return
        
        try:
            disabled_count = 0
            for task_id in self.selected_task_ids:
                task = self.task_manager.get_task(task_id)
                if task and task.status != TaskStatus.DISABLED:
                    task.status = TaskStatus.DISABLED
                    task.next_execution = None
                    disabled_count += 1
            
            if disabled_count > 0:
                messagebox.showinfo("Success", f"Disabled {disabled_count} task(s)")
                if self.on_task_updated:
                    self.on_task_updated()
            else:
                messagebox.showinfo("Info", "No enabled tasks were selected")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disable tasks:\n{str(e)}")
    
    def _reset_retry_counter(self) -> None:
        """Reset retry counter for selected tasks."""
        if not self.selected_task_ids:
            return
        
        try:
            reset_count = 0
            for task_id in self.selected_task_ids:
                task = self.task_manager.get_task(task_id)
                if task and task.retry_count > 0:
                    task.reset_retry()
                    reset_count += 1
            
            if reset_count > 0:
                messagebox.showinfo("Success", f"Reset retry counter for {reset_count} task(s)")
                if self.on_task_updated:
                    self.on_task_updated()
            else:
                messagebox.showinfo("Info", "No tasks with retry count > 0 were selected")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset retry counters:\n{str(e)}")
    
    def _export_selected_tasks(self) -> None:
        """Export selected tasks to file."""
        if not self.selected_task_ids:
            return
        
        try:
            from tkinter import filedialog
            import json
            
            # Get file path
            file_path = filedialog.asksaveasfilename(
                title="Export Tasks",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Export tasks
            tasks_data = []
            for task_id in self.selected_task_ids:
                task = self.task_manager.get_task(task_id)
                if task:
                    tasks_data.append(task.to_dict())
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Exported {len(tasks_data)} task(s) to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export tasks:\n{str(e)}")
    
    def _import_tasks(self) -> None:
        """Import tasks from file."""
        try:
            from tkinter import filedialog
            import json
            
            # Get file path
            file_path = filedialog.askopenfilename(
                title="Import Tasks",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Import tasks
            with open(file_path, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            if not isinstance(tasks_data, list):
                messagebox.showerror("Error", "Invalid file format. Expected a list of tasks.")
                return
            
            imported_count = 0
            for task_data in tasks_data:
                try:
                    task = Task.from_dict(task_data)
                    # Generate new ID to avoid conflicts
                    import uuid
                    task.id = str(uuid.uuid4())
                    task.created_at = datetime.now()
                    task.last_executed = None
                    task.retry_count = 0
                    task.update_next_execution()
                    
                    self.task_manager.add_task(task)
                    imported_count += 1
                except Exception as e:
                    print(f"Failed to import task: {e}")
                    continue
            
            if imported_count > 0:
                messagebox.showinfo("Success", f"Imported {imported_count} task(s) from:\n{file_path}")
                if self.on_task_created:
                    self.on_task_created()
            else:
                messagebox.showwarning("Warning", "No tasks were imported")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import tasks:\n{str(e)}")
    
    def _select_all_tasks(self) -> None:
        """Select all tasks."""
        # This should be handled by the parent component
        # For now, just show a message
        messagebox.showinfo("Select All", "This function should be implemented by the parent component")
    
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