"""
Schedules management page implementation.
"""

import tkinter as tk
from tkinter import ttk
from typing import List

from src.gui.page_manager import BasePage
from src.gui.widgets.task_list_widget import TaskListWidget
from src.core.task_manager import TaskManager


class SchedulesPage(BasePage):
    """Schedules management page."""
    
    def __init__(self, parent: tk.Widget, task_manager: TaskManager):
        """Initialize schedules page."""
        super().__init__(parent, "Schedules", "排程管理")
        self.task_manager = task_manager
        self.task_list_widget = None
    
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
        detail_frame = ttk.LabelFrame(main_frame, text="任務詳細資訊", padding=5)
        detail_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        detail_frame.grid_rowconfigure(1, weight=1)
        detail_frame.grid_columnconfigure(0, weight=1)
        
        # Control buttons
        control_frame = ttk.Frame(detail_frame)
        control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.new_button = ttk.Button(
            control_frame,
            text="新增任務",
            command=self._create_new_task,
            width=12
        )
        self.new_button.pack(side="left", padx=(0, 5))
        
        self.edit_button = ttk.Button(
            control_frame,
            text="編輯任務",
            command=self._edit_selected_task,
            state="disabled",
            width=12
        )
        self.edit_button.pack(side="left", padx=(0, 5))
        
        self.delete_button = ttk.Button(
            control_frame,
            text="刪除任務",
            command=self._delete_selected_tasks,
            state="disabled",
            width=12
        )
        self.delete_button.pack(side="left", padx=(0, 5))
        
        self.execute_button = ttk.Button(
            control_frame,
            text="立即執行",
            command=self._execute_selected_task,
            state="disabled",
            width=12
        )
        self.execute_button.pack(side="left")
        
        # Task detail display
        self.detail_text = tk.Text(
            detail_frame,
            wrap=tk.WORD,
            state="disabled",
            font=("Segoe UI", 10),
            bg="#F8F9FA",
            relief="flat",
            borderwidth=1
        )
        self.detail_text.grid(row=1, column=0, sticky="nsew")
        
        # Detail scrollbar
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)
        detail_scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Initial detail text
        self._update_detail_display([])
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        if self.task_list_widget:
            self.task_list_widget.refresh_tasks()
    
    def _on_task_selection_changed(self, selected_task_ids: List[str]) -> None:
        """Handle task selection changes."""
        # Update button states
        has_selection = len(selected_task_ids) > 0
        single_selection = len(selected_task_ids) == 1
        
        self.edit_button.config(state="normal" if single_selection else "disabled")
        self.delete_button.config(state="normal" if has_selection else "disabled")
        self.execute_button.config(state="normal" if single_selection else "disabled")
        
        # Update detail display
        self._update_detail_display(selected_task_ids)
    
    def _update_detail_display(self, selected_task_ids: List[str]) -> None:
        """Update the task detail display."""
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, tk.END)
        
        if not selected_task_ids:
            self.detail_text.insert(tk.END, "請選擇一個任務以查看詳細資訊")
        elif len(selected_task_ids) == 1:
            task_id = selected_task_ids[0]
            task = self.task_manager.get_task(task_id)
            if task:
                detail_text = self._format_task_details(task)
                self.detail_text.insert(tk.END, detail_text)
            else:
                self.detail_text.insert(tk.END, f"找不到任務: {task_id}")
        else:
            self.detail_text.insert(tk.END, f"已選擇 {len(selected_task_ids)} 個任務\n\n批次操作可用：\n• 刪除選中的任務")
        
        self.detail_text.config(state="disabled")
    
    def _format_task_details(self, task) -> str:
        """Format task details for display."""
        from src.models.task import TaskStatus
        
        status_texts = {
            TaskStatus.PENDING: "等待中",
            TaskStatus.RUNNING: "執行中", 
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失敗",
            TaskStatus.DISABLED: "已停用"
        }
        
        details = []
        details.append(f"任務名稱: {task.name}")
        details.append(f"任務ID: {task.id}")
        details.append(f"目標應用程式: {task.target_app}")
        details.append(f"動作類型: {task.action_type.value if hasattr(task.action_type, 'value') else str(task.action_type)}")
        details.append(f"狀態: {status_texts.get(task.status, '未知')}")
        details.append(f"建立時間: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if task.last_executed:
            details.append(f"上次執行: {task.last_executed.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            details.append("上次執行: 從未執行")
        
        if task.next_execution:
            details.append(f"下次執行: {task.next_execution.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            details.append("下次執行: 未排程")
        
        details.append(f"重試次數: {task.retry_count}/{task.max_retries}")
        
        # Schedule details
        details.append("\n排程設定:")
        details.append(f"  類型: {task.schedule.schedule_type.value if hasattr(task.schedule.schedule_type, 'value') else str(task.schedule.schedule_type)}")
        details.append(f"  開始時間: {task.schedule.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if task.schedule.end_time:
            details.append(f"  結束時間: {task.schedule.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Action parameters
        if task.action_params:
            details.append("\n動作參數:")
            for key, value in task.action_params.items():
                details.append(f"  {key}: {value}")
        
        return "\n".join(details)
    
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