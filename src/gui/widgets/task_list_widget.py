"""
Task list widget implementation.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable, Set
from datetime import datetime

from src.models.task import Task, TaskStatus
from src.core.task_manager import TaskManager


class TaskListWidget(ttk.Frame):
    """Widget for displaying and managing task list."""
    
    def __init__(self, parent: tk.Widget, task_manager: TaskManager):
        """
        Initialize task list widget.
        
        Args:
            parent: Parent widget
            task_manager: Task manager instance
        """
        super().__init__(parent)
        self.task_manager = task_manager
        self.selected_tasks: Set[str] = set()
        self.on_selection_changed: Optional[Callable[[List[str]], None]] = None
        
        self._setup_ui()
        self._setup_bindings()
        self.refresh_tasks()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title and task count
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w")
        
        self.title_label = ttk.Label(
            title_frame,
            text="任務清單",
            font=("Segoe UI", 12, "bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.count_label = ttk.Label(
            title_frame,
            text="(0 個任務)",
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        self.count_label.grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        # Refresh button
        self.refresh_button = ttk.Button(
            header_frame,
            text="重新整理",
            command=self.refresh_tasks,
            width=10
        )
        self.refresh_button.grid(row=0, column=1, sticky="e")
        
        # Treeview frame with scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview
        columns = ("name", "target_app", "action_type", "status", "next_execution", "last_executed", "task_id")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="extended"
        )
        
        # Configure columns
        self.tree.heading("#0", text="", anchor="w")
        self.tree.column("#0", width=30, minwidth=30, stretch=False)
        
        self.tree.heading("name", text="Task Name", anchor="w")
        self.tree.column("name", width=200, minwidth=150)
        
        self.tree.heading("target_app", text="Target App", anchor="w")
        self.tree.column("target_app", width=150, minwidth=100)
        
        self.tree.heading("action_type", text="Action Type", anchor="w")
        self.tree.column("action_type", width=120, minwidth=80)
        
        self.tree.heading("status", text="Status", anchor="center")
        self.tree.column("status", width=80, minwidth=60)
        
        self.tree.heading("next_execution", text="Next Run", anchor="center")
        self.tree.column("next_execution", width=140, minwidth=100)
        
        self.tree.heading("last_executed", text="Last Run", anchor="center")
        self.tree.column("last_executed", width=140, minwidth=100)
        
        # Hidden task_id column
        self.tree.heading("task_id", text="")
        self.tree.column("task_id", width=0, minwidth=0, stretch=False)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Selection info frame
        selection_frame = ttk.Frame(self)
        selection_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        self.selection_label = ttk.Label(
            selection_frame,
            text="未選擇任務",
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        self.selection_label.pack(side="left")
    
    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_selection)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
    
    def _on_tree_selection(self, event) -> None:
        """Handle tree selection change."""
        selected_items = self.tree.selection()
        self.selected_tasks = {self.tree.item(item)["values"][6] for item in selected_items if self.tree.item(item)["values"]}
        
        # Update selection label
        count = len(self.selected_tasks)
        if count == 0:
            self.selection_label.config(text="未選擇任務")
        elif count == 1:
            # Get task name for display
            selected_item = next(iter(selected_items)) if selected_items else None
            if selected_item:
                task_name = self.tree.item(selected_item)["values"][0]  # First value is task name
                self.selection_label.config(text=f"已選擇: {task_name}")
            else:
                self.selection_label.config(text="未選擇任務")
        else:
            self.selection_label.config(text=f"已選擇 {count} 個任務")
        
        # Notify callback
        if self.on_selection_changed:
            self.on_selection_changed(list(self.selected_tasks))
    
    def _on_double_click(self, event) -> None:
        """Handle double-click on task item."""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item and self.tree.item(item)["values"]:
            task_id = self.tree.item(item)["values"][6]
            # TODO: Implement task detail view or edit dialog
            print(f"Double-clicked task: {task_id}")
    
    def _on_right_click(self, event) -> None:
        """Handle right-click context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # TODO: Implement context menu
            print("Right-click context menu")
    
    def _get_status_indicator(self, status: TaskStatus) -> str:
        """Get visual indicator for task status."""
        status_indicators = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "▶️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.DISABLED: "⏸️"
        }
        return status_indicators.get(status, "❓")
    
    def _get_status_text(self, status: TaskStatus) -> str:
        """Get localized status text."""
        status_texts = {
            TaskStatus.PENDING: "等待中",
            TaskStatus.RUNNING: "執行中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失敗",
            TaskStatus.DISABLED: "已停用"
        }
        return status_texts.get(status, "未知")
    
    def _format_datetime(self, dt: Optional[datetime]) -> str:
        """Format datetime for display."""
        if not dt:
            return "-"
        
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        elif dt.year == now.year:
            return dt.strftime("%m/%d %H:%M")
        else:
            return dt.strftime("%Y/%m/%d %H:%M")
    
    def _get_action_type_text(self, action_type) -> str:
        """Get localized action type text."""
        # Import here to avoid circular imports
        from src.models.action import ActionType
        
        action_texts = {
            ActionType.LAUNCH_APP: "啟動應用程式",
            ActionType.CLOSE_APP: "關閉應用程式",
            ActionType.FOCUS_WINDOW: "聚焦視窗",
            ActionType.MINIMIZE_WINDOW: "最小化視窗",
            ActionType.MAXIMIZE_WINDOW: "最大化視窗",
            ActionType.RESTORE_WINDOW: "還原視窗",
            ActionType.RESIZE_WINDOW: "調整視窗大小",
            ActionType.MOVE_WINDOW: "移動視窗",
            ActionType.SEND_KEYS: "發送按鍵",
            ActionType.CLICK_ELEMENT: "點擊元素"
        }
        return action_texts.get(action_type, str(action_type.value) if hasattr(action_type, 'value') else str(action_type))
    
    def _get_action_sequence_text(self, task) -> str:
        """Get action sequence summary text."""
        try:
            if not hasattr(task, 'action_sequence') or not task.action_sequence:
                return "無動作"
            
            from src.models.action import ActionType
            
            action_texts = {
                ActionType.LAUNCH_APP: "啟動應用程式",
                ActionType.CLOSE_APP: "關閉應用程式",
                ActionType.RESIZE_WINDOW: "調整視窗大小",
                ActionType.MOVE_WINDOW: "移動視窗",
                ActionType.MINIMIZE_WINDOW: "最小化視窗",
                ActionType.MAXIMIZE_WINDOW: "最大化視窗",
                ActionType.FOCUS_WINDOW: "聚焦視窗",
                ActionType.CLICK_ELEMENT: "點擊元素",
                ActionType.TYPE_TEXT: "輸入文字",
                ActionType.SEND_KEYS: "發送快捷鍵",
                ActionType.CUSTOM_COMMAND: "自訂命令",
                ActionType.SWITCH_APP: "切換應用程式",
                ActionType.DRAG_ELEMENT: "拖拽操作",
                ActionType.MOVE_MOUSE: "移動滑鼠",
                ActionType.SCROLL: "滾動操作",
                ActionType.PRESS_KEY: "按鍵操作",
                ActionType.CLIPBOARD_COPY: "複製到剪貼簿",
                ActionType.CLIPBOARD_PASTE: "從剪貼簿貼上",
                ActionType.GET_DESKTOP_STATE: "獲取桌面狀態",
                ActionType.WAIT: "等待",
                ActionType.SCRAPE_WEBPAGE: "抓取網頁"
            }
            
            if len(task.action_sequence) == 1:
                # Single action - show action type
                action_type = task.action_sequence[0].action_type
                return action_texts.get(action_type, str(action_type.value) if hasattr(action_type, 'value') else str(action_type))
            else:
                # Multiple actions - show summary
                return f"動作序列 ({len(task.action_sequence)} 步驟)"
                
        except Exception:
            return "未知動作"
    
    def refresh_tasks(self) -> None:
        """Refresh the task list."""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get tasks from task manager
            tasks = self.task_manager.get_all_tasks()
            
            # Add tasks to tree
            for task in tasks:
                status_indicator = self._get_status_indicator(task.status)
                status_text = self._get_status_text(task.status)
                action_text = self._get_action_sequence_text(task)
                next_exec = self._format_datetime(task.next_execution)
                last_exec = self._format_datetime(task.last_executed)
                
                # Insert task item
                item_id = self.tree.insert(
                    "",
                    "end",
                    text=status_indicator,
                    values=(
                        task.name,        # Task Name column
                        task.target_app,  # Target App column
                        action_text,      # Action Type column
                        status_text,      # Status column
                        next_exec,        # Next Run column
                        last_exec,        # Last Run column
                        task.id           # Hidden Task ID column
                    )
                )
                
                # Apply status-based styling
                self._apply_status_styling(item_id, task.status)
            
            # Update count label
            task_count = len(tasks)
            self.count_label.config(text=f"({task_count} 個任務)")
            
            # Clear selection
            self.selected_tasks.clear()
            self.selection_label.config(text="未選擇任務")
            
        except Exception as e:
            print(f"Error refreshing tasks: {e}")
            self.count_label.config(text="(載入失敗)")
    
    def _apply_status_styling(self, item_id: str, status: TaskStatus) -> None:
        """Apply visual styling based on task status."""
        # Configure tags for different statuses
        if not hasattr(self, '_tags_configured'):
            self.tree.tag_configure("running", background="#E3F2FD")
            self.tree.tag_configure("failed", background="#FFEBEE")
            self.tree.tag_configure("disabled", background="#F5F5F5", foreground="#9E9E9E")
            self.tree.tag_configure("completed", background="#E8F5E8")
            self._tags_configured = True
        
        # Apply appropriate tag
        if status == TaskStatus.RUNNING:
            self.tree.item(item_id, tags=("running",))
        elif status == TaskStatus.FAILED:
            self.tree.item(item_id, tags=("failed",))
        elif status == TaskStatus.DISABLED:
            self.tree.item(item_id, tags=("disabled",))
        elif status == TaskStatus.COMPLETED:
            self.tree.item(item_id, tags=("completed",))
    
    def get_selected_task_ids(self) -> List[str]:
        """Get list of selected task IDs."""
        return list(self.selected_tasks)
    
    def select_task(self, task_id: str) -> None:
        """Select a specific task by ID."""
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if values and values[6] == task_id:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                break
    
    def clear_selection(self) -> None:
        """Clear all selections."""
        self.tree.selection_remove(self.tree.selection())
    
    def set_selection_callback(self, callback: Callable[[List[str]], None]) -> None:
        """Set callback for selection changes."""
        self.on_selection_changed = callback
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update the status of a specific task in the list."""
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if values and values[6] == task_id:
                # Update status text and indicator
                status_text = self._get_status_text(status)
                status_indicator = self._get_status_indicator(status)
                
                # Update values
                new_values = list(values)
                new_values[3] = status_text  # Status column (now at index 3)
                self.tree.item(item, text=status_indicator, values=new_values)
                
                # Update styling
                self._apply_status_styling(item, status)
                break