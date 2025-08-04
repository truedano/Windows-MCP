"""
Schedule logs page implementation with modern table design.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import re

from src.gui.page_manager import BasePage
from src.storage.log_storage import get_log_storage
from src.models.execution import ExecutionLog


class SearchBarWidget:
    """Search bar widget with advanced filtering capabilities."""
    
    def __init__(self, parent: tk.Widget, on_search: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """
        Initialize search bar widget.
        
        Args:
            parent: Parent widget
            on_search: Callback for search events
        """
        self.parent = parent
        self.on_search = on_search
        self.search_var = tk.StringVar()
        self.filter_vars: Dict[str, tk.Variable] = {}
        self.search_history: List[str] = []
        self.max_history = 10
        
        self._create_search_ui()
    
    def _create_search_ui(self):
        """Create search user interface."""
        # Main search frame
        self.search_frame = ttk.LabelFrame(self.parent, text="搜尋和篩選", padding=10)
        self.search_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Search input row
        search_row = ttk.Frame(self.search_frame)
        search_row.pack(fill=tk.X, pady=(0, 10))
        
        # Search icon and input
        search_icon = ttk.Label(search_row, text="🔍", font=("Segoe UI", 12))
        search_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_entry = ttk.Entry(
            search_row, 
            textvariable=self.search_var, 
            width=40,
            font=("Segoe UI", 10)
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind('<Return>', self._on_search_enter)
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Search button
        self.search_btn = ttk.Button(
            search_row, 
            text="搜尋", 
            command=self._perform_search,
            style="Accent.TButton"
        )
        self.search_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear button
        self.clear_btn = ttk.Button(
            search_row, 
            text="清除", 
            command=self._clear_search
        )
        self.clear_btn.pack(side=tk.LEFT)
        
        # Advanced filters row
        self._create_filter_row()
        
        # Search suggestions (initially hidden)
        self._create_suggestions_dropdown()
    
    def _create_filter_row(self):
        """Create advanced filter controls."""
        filter_row = ttk.Frame(self.search_frame)
        filter_row.pack(fill=tk.X, pady=(5, 0))
        
        # Schedule name filter
        ttk.Label(filter_row, text="排程:").pack(side=tk.LEFT, padx=(0, 5))
        schedule_var = tk.StringVar()
        self.schedule_combo = ttk.Combobox(
            filter_row, 
            textvariable=schedule_var, 
            width=15, 
            state="readonly"
        )
        self.schedule_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.filter_vars['schedule'] = schedule_var
        
        # Status filter
        ttk.Label(filter_row, text="狀態:").pack(side=tk.LEFT, padx=(0, 5))
        status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(
            filter_row, 
            textvariable=status_var,
            values=["全部", "成功", "失敗"], 
            width=10, 
            state="readonly"
        )
        self.status_combo.set("全部")
        self.status_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.filter_vars['status'] = status_var
        
        # Date range filter
        ttk.Label(filter_row, text="時間範圍:").pack(side=tk.LEFT, padx=(0, 5))
        date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(
            filter_row, 
            textvariable=date_var,
            values=["全部", "今天", "昨天", "本週", "本月", "自訂範圍"], 
            width=12, 
            state="readonly"
        )
        self.date_combo.set("全部")
        self.date_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.filter_vars['date_range'] = date_var
        
        # Operation filter
        ttk.Label(filter_row, text="操作:").pack(side=tk.LEFT, padx=(0, 5))
        operation_var = tk.StringVar()
        self.operation_combo = ttk.Combobox(
            filter_row, 
            textvariable=operation_var, 
            width=12, 
            state="readonly"
        )
        self.operation_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.filter_vars['operation'] = operation_var
        
        # Bind filter changes
        for var in self.filter_vars.values():
            var.trace('w', lambda *args: self._on_filter_change())
    
    def _create_suggestions_dropdown(self):
        """Create search suggestions dropdown."""
        self.suggestions_frame = ttk.Frame(self.search_frame)
        # Initially hidden - will be shown when needed
        
        self.suggestions_listbox = tk.Listbox(
            self.suggestions_frame,
            height=5,
            font=("Segoe UI", 9)
        )
        self.suggestions_listbox.pack(fill=tk.BOTH, expand=True)
        self.suggestions_listbox.bind('<Double-Button-1>', self._on_suggestion_select)
        self.suggestions_listbox.bind('<Return>', self._on_suggestion_select)
    
    def _on_search_enter(self, event=None):
        """Handle Enter key in search entry."""
        self._perform_search()
    
    def _on_search_change(self, event=None):
        """Handle search text changes for live suggestions."""
        search_text = self.search_var.get().strip()
        if len(search_text) >= 2:
            self._show_suggestions(search_text)
        else:
            self._hide_suggestions()
    
    def _on_filter_change(self):
        """Handle filter changes."""
        # Perform search when filters change
        self._perform_search()
    
    def _perform_search(self):
        """Perform search with current criteria."""
        search_query = self.search_var.get().strip()
        filters = self._get_current_filters()
        
        # Add to search history
        if search_query and search_query not in self.search_history:
            self.search_history.insert(0, search_query)
            if len(self.search_history) > self.max_history:
                self.search_history.pop()
        
        # Hide suggestions
        self._hide_suggestions()
        
        # Call search callback
        if self.on_search:
            self.on_search(search_query, filters)
    
    def _clear_search(self):
        """Clear search and filters."""
        self.search_var.set("")
        for var in self.filter_vars.values():
            if hasattr(var, 'set'):
                if var == self.filter_vars['status'] or var == self.filter_vars['date_range']:
                    var.set("全部")
                else:
                    var.set("")
        
        self._hide_suggestions()
        
        # Perform empty search
        if self.on_search:
            self.on_search("", {})
    
    def _get_current_filters(self) -> Dict[str, Any]:
        """Get current filter values."""
        filters = {}
        
        # Schedule filter
        schedule = self.filter_vars['schedule'].get()
        if schedule and schedule != "全部":
            filters['schedule_name'] = schedule
        
        # Status filter
        status = self.filter_vars['status'].get()
        if status == "成功":
            filters['success'] = True
        elif status == "失敗":
            filters['success'] = False
        
        # Date range filter
        date_range = self.filter_vars['date_range'].get()
        if date_range != "全部":
            today = datetime.now().date()
            if date_range == "今天":
                filters['start_date'] = today
                filters['end_date'] = today
            elif date_range == "昨天":
                yesterday = today - timedelta(days=1)
                filters['start_date'] = yesterday
                filters['end_date'] = yesterday
            elif date_range == "本週":
                week_start = today - timedelta(days=today.weekday())
                filters['start_date'] = week_start
                filters['end_date'] = today
            elif date_range == "本月":
                month_start = today.replace(day=1)
                filters['start_date'] = month_start
                filters['end_date'] = today
        
        # Operation filter
        operation = self.filter_vars['operation'].get()
        if operation and operation != "全部":
            filters['operation'] = operation
        
        return filters
    
    def _show_suggestions(self, search_text: str):
        """Show search suggestions based on input."""
        suggestions = []
        
        # Add from search history
        for item in self.search_history:
            if search_text.lower() in item.lower():
                suggestions.append(f"歷史: {item}")
        
        # Add common search patterns
        common_patterns = [
            f"排程名稱包含: {search_text}",
            f"錯誤訊息包含: {search_text}",
            f"目標應用程式: {search_text}"
        ]
        suggestions.extend(common_patterns)
        
        if suggestions:
            self.suggestions_listbox.delete(0, tk.END)
            for suggestion in suggestions[:5]:  # Show max 5 suggestions
                self.suggestions_listbox.insert(tk.END, suggestion)
            
            self.suggestions_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self._hide_suggestions()
    
    def _hide_suggestions(self):
        """Hide search suggestions."""
        self.suggestions_frame.pack_forget()
    
    def _on_suggestion_select(self, event=None):
        """Handle suggestion selection."""
        selection = self.suggestions_listbox.curselection()
        if selection:
            suggestion = self.suggestions_listbox.get(selection[0])
            
            # Extract search text from suggestion
            if suggestion.startswith("歷史: "):
                search_text = suggestion[4:]
            elif ": " in suggestion:
                search_text = suggestion.split(": ", 1)[1]
            else:
                search_text = suggestion
            
            self.search_var.set(search_text)
            self._perform_search()
    
    def update_filter_options(self, schedules: List[str], operations: List[str]):
        """Update filter dropdown options."""
        # Update schedule options
        schedule_values = ["全部"] + sorted(schedules)
        self.schedule_combo['values'] = schedule_values
        
        # Update operation options
        operation_values = ["全部"] + sorted(operations)
        self.operation_combo['values'] = operation_values
    
    def get_search_query(self) -> str:
        """Get current search query."""
        return self.search_var.get().strip()
    
    def get_filters(self) -> Dict[str, Any]:
        """Get current filters."""
        return self._get_current_filters()
    
    def set_search_query(self, query: str):
        """Set search query."""
        self.search_var.set(query)
    
    def reset_filters(self):
        """Reset all filters to default values."""
        self._clear_search()


class LogsTableWidget:
    """Enhanced logs table widget with sorting and highlighting."""
    
    def __init__(self, parent: tk.Widget, on_log_select: Optional[Callable[[ExecutionLog], None]] = None):
        """
        Initialize logs table widget.
        
        Args:
            parent: Parent widget
            on_log_select: Callback for log selection
        """
        self.parent = parent
        self.on_log_select = on_log_select
        self.logs: List[ExecutionLog] = []
        self.sort_column = "time"
        self.sort_reverse = True
        self.search_highlights: List[str] = []
        
        self._create_table_ui()
    
    def _create_table_ui(self):
        """Create table user interface."""
        # Table frame
        self.table_frame = ttk.LabelFrame(self.parent, text="執行記錄", padding=5)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        
        # Create treeview container
        tree_container = ttk.Frame(self.table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Define columns
        columns = ("time", "schedule", "operation", "target", "status", "duration", "message")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=15)
        
        # Configure column headings and widths
        column_config = {
            "time": ("執行時間", 150, 120),
            "schedule": ("排程名稱", 120, 100),
            "operation": ("操作", 100, 80),
            "target": ("目標", 100, 80),
            "status": ("狀態", 60, 50),
            "duration": ("持續時間", 80, 70),
            "message": ("訊息", 250, 150)
        }
        
        for col, (heading, width, minwidth) in column_config.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=width, minwidth=minwidth)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)
        
        # Configure row styles
        self._configure_row_styles()
    
    def _configure_row_styles(self):
        """Configure row styles for different log types."""
        self.tree.tag_configure("success", background="#e8f5e8", foreground="#2d5a2d")
        self.tree.tag_configure("failure", background="#ffe8e8", foreground="#5a2d2d")
        self.tree.tag_configure("highlight", background="#fff3cd", foreground="#856404")
        self.tree.tag_configure("selected", background="#0078d4", foreground="white")
    
    def _sort_by_column(self, column: str):
        """Sort table by column."""
        # Toggle sort direction if same column
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Update column heading to show sort direction
        for col in self.tree["columns"]:
            heading_text = self.tree.heading(col, "text")
            if col == column:
                direction = " ↓" if self.sort_reverse else " ↑"
                if not heading_text.endswith((" ↓", " ↑")):
                    heading_text += direction
                else:
                    heading_text = heading_text[:-2] + direction
            else:
                if heading_text.endswith((" ↓", " ↑")):
                    heading_text = heading_text[:-2]
            
            self.tree.heading(col, text=heading_text)
        
        # Sort logs and refresh display
        self._sort_logs()
        self._refresh_display()
    
    def _sort_logs(self):
        """Sort logs based on current sort criteria."""
        if not self.logs:
            return
        
        sort_key_map = {
            "time": lambda log: log.execution_time,
            "schedule": lambda log: log.schedule_name.lower(),
            "operation": lambda log: log.result.operation.lower(),
            "target": lambda log: log.result.target.lower(),
            "status": lambda log: log.result.success,
            "duration": lambda log: log.duration.total_seconds(),
            "message": lambda log: log.result.message.lower()
        }
        
        sort_key = sort_key_map.get(self.sort_column, sort_key_map["time"])
        self.logs.sort(key=sort_key, reverse=self.sort_reverse)
    
    def _on_double_click(self, event):
        """Handle double-click on log entry."""
        selection = self.tree.selection()
        if selection and self.on_log_select:
            item = selection[0]
            log_id = self.tree.set(item, "#0")
            log = next((l for l in self.logs if l.id == log_id), None)
            if log:
                self.on_log_select(log)
    
    def _on_selection_change(self, event):
        """Handle selection change."""
        # Could be used for showing preview or updating status
        pass
    
    def update_logs(self, logs: List[ExecutionLog], search_query: str = ""):
        """Update table with new logs."""
        self.logs = logs.copy()
        self.search_highlights = self._extract_search_terms(search_query)
        self._sort_logs()
        self._refresh_display()
    
    def _extract_search_terms(self, search_query: str) -> List[str]:
        """Extract search terms for highlighting."""
        if not search_query:
            return []
        
        # Split query into terms, handling quoted phrases
        terms = []
        in_quotes = False
        current_term = ""
        
        for char in search_query:
            if char == '"':
                in_quotes = not in_quotes
                if not in_quotes and current_term:
                    terms.append(current_term)
                    current_term = ""
            elif char == ' ' and not in_quotes:
                if current_term:
                    terms.append(current_term)
                    current_term = ""
            else:
                current_term += char
        
        if current_term:
            terms.append(current_term)
        
        return [term.lower() for term in terms if len(term) > 1]
    
    def _refresh_display(self):
        """Refresh table display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add logs to table
        for log in self.logs:
            self._add_log_to_table(log)
    
    def _add_log_to_table(self, log: ExecutionLog):
        """Add a log entry to the table."""
        # Format values for display
        time_str = log.execution_time.strftime("%Y-%m-%d %H:%M:%S")
        status_str = "成功" if log.result.success else "失敗"
        duration_str = f"{log.duration.total_seconds():.2f}s"
        
        # Determine row tags
        tags = []
        if log.result.success:
            tags.append("success")
        else:
            tags.append("failure")
        
        # Check for search highlights
        if self._should_highlight_log(log):
            tags.append("highlight")
        
        # Insert row
        values = (
            time_str,
            log.schedule_name,
            log.result.operation,
            log.result.target,
            status_str,
            duration_str,
            log.result.message
        )
        
        item = self.tree.insert("", tk.END, values=values, tags=tags)
        
        # Store log ID for reference
        self.tree.set(item, "#0", log.id)
    
    def _should_highlight_log(self, log: ExecutionLog) -> bool:
        """Check if log should be highlighted based on search terms."""
        if not self.search_highlights:
            return False
        
        # Create searchable text from log
        searchable_text = f"{log.schedule_name} {log.result.operation} {log.result.target} {log.result.message}".lower()
        
        # Check if any search term matches
        for term in self.search_highlights:
            if term in searchable_text:
                return True
        
        return False
    
    def get_selected_log(self) -> Optional[ExecutionLog]:
        """Get currently selected log."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            log_id = self.tree.set(item, "#0")
            return next((l for l in self.logs if l.id == log_id), None)
        return None
    
    def clear_logs(self):
        """Clear all logs from table."""
        self.logs.clear()
        self._refresh_display()


class ScheduleLogsPage(BasePage):
    """Modern schedule logs page with enhanced table design and functionality."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize schedule logs page."""
        super().__init__(parent, "Logs", "排程記錄")
        self.log_storage = get_log_storage()
        self.current_page = 0
        self.page_size = 50
        self.current_search_query = ""
        self.current_filters: Dict[str, Any] = {}
        
        # UI components
        self.search_bar: Optional[SearchBarWidget] = None
        self.logs_table: Optional[LogsTableWidget] = None
        self.pagination_frame: Optional[ttk.Frame] = None
        self.page_info_label: Optional[ttk.Label] = None
        self.prev_btn: Optional[ttk.Button] = None
        self.next_btn: Optional[ttk.Button] = None
        self.page_size_var = tk.StringVar(value=str(self.page_size))
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page header
        self._create_page_header()
        
        # Create main container
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create search bar
        self.search_bar = SearchBarWidget(
            main_container, 
            on_search=self._on_search_performed
        )
        
        # Create logs table
        self.logs_table = LogsTableWidget(
            main_container,
            on_log_select=self._show_log_details
        )
        
        # Create pagination controls
        self._create_pagination_controls(main_container)
        
        # Create action buttons
        self._create_action_buttons(main_container)
        
        # Load initial data
        self._load_initial_data()
    
    def _create_page_header(self):
        """Create page header with title and description."""
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Page title
        title_label = ttk.Label(
            header_frame,
            text="Schedule Logs",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Page description
        desc_label = ttk.Label(
            header_frame,
            text="查看和管理排程任務的執行記錄和日誌",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        desc_label.pack(anchor=tk.W)
    
    def _on_search_performed(self, search_query: str, filters: Dict[str, Any]):
        """Handle search performed by search bar."""
        self.current_search_query = search_query
        self.current_filters = filters
        self.current_page = 0  # Reset to first page
        self._load_logs()
    
    def _load_initial_data(self):
        """Load initial data and update filter options."""
        self._load_logs()
        self._update_filter_options()
    
    def _update_filter_options(self):
        """Update filter dropdown options."""
        try:
            # Get all logs to extract unique values
            all_logs = self.log_storage.load_logs(0, 1000, {})
            
            # Extract unique schedule names and operations
            schedules = set(log.schedule_name for log in all_logs)
            operations = set(log.result.operation for log in all_logs)
            
            # Update search bar filter options
            if self.search_bar:
                self.search_bar.update_filter_options(
                    list(schedules), 
                    list(operations)
                )
                
        except Exception as e:
            print(f"Error updating filter options: {e}")
    
    def _create_pagination_controls(self, parent: tk.Widget) -> None:
        """Create modern pagination controls."""
        self.pagination_frame = ttk.Frame(parent)
        self.pagination_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Left side - navigation buttons
        nav_frame = ttk.Frame(self.pagination_frame)
        nav_frame.pack(side=tk.LEFT)
        
        # Previous button
        self.prev_btn = ttk.Button(
            nav_frame, 
            text="◀ 上一頁", 
            command=self._previous_page,
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Page info
        self.page_info_label = ttk.Label(
            nav_frame, 
            text="",
            font=("Segoe UI", 9)
        )
        self.page_info_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Next button
        self.next_btn = ttk.Button(
            nav_frame, 
            text="下一頁 ▶", 
            command=self._next_page,
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.LEFT)
        
        # Right side - page size and actions
        options_frame = ttk.Frame(self.pagination_frame)
        options_frame.pack(side=tk.RIGHT)
        
        # Page size selector
        ttk.Label(options_frame, text="每頁顯示:").pack(side=tk.LEFT, padx=(0, 5))
        page_size_combo = ttk.Combobox(
            options_frame, 
            textvariable=self.page_size_var,
            values=["25", "50", "100", "200"], 
            width=8, 
            state="readonly"
        )
        page_size_combo.pack(side=tk.LEFT, padx=(0, 10))
        page_size_combo.bind('<<ComboboxSelected>>', self._change_page_size)
        
        # Jump to page
        ttk.Label(options_frame, text="跳至頁面:").pack(side=tk.LEFT, padx=(10, 5))
        self.jump_page_var = tk.StringVar()
        jump_entry = ttk.Entry(options_frame, textvariable=self.jump_page_var, width=6)
        jump_entry.pack(side=tk.LEFT, padx=(0, 5))
        jump_entry.bind('<Return>', self._jump_to_page)
        
        jump_btn = ttk.Button(options_frame, text="跳轉", command=self._jump_to_page)
        jump_btn.pack(side=tk.LEFT)
    
    def _create_action_buttons(self, parent: tk.Widget) -> None:
        """Create action buttons with modern styling."""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=5)
        
        # Left side - primary actions
        primary_frame = ttk.Frame(action_frame)
        primary_frame.pack(side=tk.LEFT)
        
        # Refresh button
        refresh_btn = ttk.Button(
            primary_frame, 
            text="🔄 重新整理", 
            command=self._refresh_logs,
            style="Accent.TButton"
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Export button
        export_btn = ttk.Button(
            primary_frame, 
            text="📤 匯出日誌", 
            command=self._export_logs
        )
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side - management actions
        mgmt_frame = ttk.Frame(action_frame)
        mgmt_frame.pack(side=tk.RIGHT)
        
        # Statistics button
        stats_btn = ttk.Button(
            mgmt_frame, 
            text="📊 統計資訊", 
            command=self._show_statistics
        )
        stats_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear old logs button
        clear_btn = ttk.Button(
            mgmt_frame, 
            text="🗑️ 清除舊日誌", 
            command=self._clear_old_logs
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Archive logs button
        archive_btn = ttk.Button(
            mgmt_frame, 
            text="📦 封存日誌", 
            command=self._archive_logs
        )
        archive_btn.pack(side=tk.LEFT)
    
    def _load_logs(self) -> None:
        """Load logs from storage and display them."""
        try:
            # Combine search query with filters
            filters = self.current_filters.copy()
            if self.current_search_query:
                filters['query'] = self.current_search_query
            
            # Load logs with current filters and pagination
            logs = self.log_storage.load_logs(self.current_page, self.page_size, filters)
            
            # Update table
            if self.logs_table:
                self.logs_table.update_logs(logs, self.current_search_query)
            
            # Update pagination info
            self._update_pagination_info(len(logs))
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入日誌時發生錯誤: {e}")
    
    def _refresh_logs(self) -> None:
        """Refresh logs and update filter options."""
        self._load_logs()
        self._update_filter_options()
    
    def _update_pagination_info(self, logs_count: int) -> None:
        """Update pagination information."""
        start_idx = self.current_page * self.page_size + 1
        end_idx = start_idx + logs_count - 1
        
        if logs_count == 0:
            info_text = "沒有符合條件的日誌記錄"
        else:
            info_text = f"第 {start_idx}-{end_idx} 項"
            
            # Add total count if available
            try:
                filters = self.current_filters.copy()
                if self.current_search_query:
                    filters['query'] = self.current_search_query
                
                # Get total count (this is an approximation)
                total_logs = self.log_storage.load_logs(0, 10000, filters)
                if len(total_logs) >= 10000:
                    info_text += f" (共 10000+ 項)"
                else:
                    info_text += f" (共 {len(total_logs)} 項)"
            except:
                pass
        
        if self.page_info_label:
            self.page_info_label.config(text=info_text)
        
        # Update button states
        if self.prev_btn:
            self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        
        if self.next_btn:
            self.next_btn.config(state=tk.NORMAL if logs_count == self.page_size else tk.DISABLED)
    
    def _previous_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_logs()
    
    def _next_page(self) -> None:
        """Go to next page."""
        self.current_page += 1
        self._load_logs()
    
    def _change_page_size(self, event=None) -> None:
        """Change page size and reload."""
        try:
            self.page_size = int(self.page_size_var.get())
            self.current_page = 0
            self._load_logs()
        except ValueError:
            pass
    
    def _jump_to_page(self, event=None) -> None:
        """Jump to specific page."""
        try:
            page_num = int(self.jump_page_var.get())
            if page_num > 0:
                self.current_page = page_num - 1  # Convert to 0-based
                self.jump_page_var.set("")  # Clear input
                self._load_logs()
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的頁面號碼")
    
    def _archive_logs(self) -> None:
        """Archive old logs to compressed files."""
        try:
            # Ask for confirmation and archive period
            archive_window = tk.Toplevel(self.frame)
            archive_window.title("封存日誌")
            archive_window.geometry("350x200")
            archive_window.transient(self.frame.winfo_toplevel())
            archive_window.grab_set()
            
            ttk.Label(archive_window, text="封存多少天前的日誌:").pack(pady=10)
            
            days_var = tk.IntVar(value=90)
            days_spinbox = ttk.Spinbox(archive_window, from_=30, to=365, textvariable=days_var, width=10)
            days_spinbox.pack(pady=5)
            
            info_label = ttk.Label(
                archive_window, 
                text="封存的日誌將被壓縮保存，但仍可查看",
                font=("Segoe UI", 9),
                foreground="#666666"
            )
            info_label.pack(pady=5)
            
            def do_archive():
                days = days_var.get()
                if messagebox.askyesno("確認", f"確定要封存 {days} 天前的日誌嗎？"):
                    success = self.log_storage.rotate_log_files()
                    
                    archive_window.destroy()
                    
                    if success:
                        messagebox.showinfo("成功", f"日誌封存完成")
                        self._refresh_logs()
                    else:
                        messagebox.showerror("錯誤", "日誌封存失敗")
            
            button_frame = ttk.Frame(archive_window)
            button_frame.pack(pady=20)
            
            ttk.Button(button_frame, text="封存", command=do_archive).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=archive_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"封存日誌時發生錯誤: {e}")
    
    def _show_log_details(self, log: ExecutionLog) -> None:
        """Show detailed information for selected log."""
        if not log:
            messagebox.showerror("錯誤", "找不到日誌記錄")
            return
        
        # Create details window
        self._create_log_details_window(log)
    
    def _create_log_details_window(self, log: ExecutionLog) -> None:
        """Create a modern window showing detailed log information."""
        details_window = tk.Toplevel(self.frame)
        details_window.title(f"日誌詳細資訊 - {log.schedule_name}")
        details_window.geometry("700x500")
        details_window.transient(self.frame.winfo_toplevel())
        details_window.grab_set()
        
        # Center the window
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (details_window.winfo_screenheight() // 2) - (500 // 2)
        details_window.geometry(f"700x500+{x}+{y}")
        
        # Main container
        main_frame = ttk.Frame(details_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status icon and title
        status_icon = "✅" if log.result.success else "❌"
        title_label = ttk.Label(
            header_frame,
            text=f"{status_icon} {log.schedule_name}",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Execution time
        time_label = ttk.Label(
            header_frame,
            text=log.execution_time.strftime("%Y-%m-%d %H:%M:%S"),
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        time_label.pack(side=tk.RIGHT)
        
        # Create notebook for organized information
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Basic Information Tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本資訊")
        
        self._create_basic_info_tab(basic_frame, log)
        
        # Execution Details Tab
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="執行詳情")
        
        self._create_execution_details_tab(details_frame, log)
        
        # Raw Data Tab
        raw_frame = ttk.Frame(notebook)
        notebook.add(raw_frame, text="原始資料")
        
        self._create_raw_data_tab(raw_frame, log)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Copy to clipboard button
        copy_btn = ttk.Button(
            button_frame, 
            text="📋 複製到剪貼簿", 
            command=lambda: self._copy_log_to_clipboard(log)
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Close button
        close_btn = ttk.Button(
            button_frame, 
            text="關閉", 
            command=details_window.destroy,
            style="Accent.TButton"
        )
        close_btn.pack(side=tk.RIGHT)
    
    def _create_basic_info_tab(self, parent: tk.Widget, log: ExecutionLog):
        """Create basic information tab."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Basic information fields
        info_fields = [
            ("日誌 ID", log.id),
            ("排程名稱", log.schedule_name),
            ("執行時間", log.execution_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("執行狀態", "成功" if log.result.success else "失敗"),
            ("持續時間", f"{log.duration.total_seconds():.3f} 秒"),
            ("重試次數", str(log.retry_count)),
            ("操作類型", log.result.operation),
            ("目標對象", log.result.target),
            ("結果訊息", log.result.message)
        ]
        
        for i, (label, value) in enumerate(info_fields):
            row_frame = ttk.Frame(scrollable_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Label
            label_widget = ttk.Label(
                row_frame, 
                text=f"{label}:", 
                font=("Segoe UI", 10, "bold"),
                width=12,
                anchor="w"
            )
            label_widget.pack(side=tk.LEFT, padx=(0, 10))
            
            # Value
            value_widget = ttk.Label(
                row_frame, 
                text=str(value),
                font=("Segoe UI", 10),
                anchor="w",
                wraplength=400
            )
            value_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_execution_details_tab(self, parent: tk.Widget, log: ExecutionLog):
        """Create execution details tab."""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbar
        text_widget = tk.Text(
            text_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 10),
            state=tk.DISABLED
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Format execution details
        details_text = f"""執行結果詳情:

時間戳記: {log.result.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
操作類型: {log.result.operation}
目標對象: {log.result.target}
執行狀態: {'成功' if log.result.success else '失敗'}
結果訊息: {log.result.message}

執行統計:
開始時間: {log.execution_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
結束時間: {log.result.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
執行時長: {log.duration.total_seconds():.3f} 秒
重試次數: {log.retry_count}
"""
        
        if log.result.details:
            details_text += f"\n詳細資訊:\n{self._format_details(log.result.details)}"
        
        # Insert text
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, details_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_raw_data_tab(self, parent: tk.Widget, log: ExecutionLog):
        """Create raw data tab showing JSON representation."""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbar
        text_widget = tk.Text(
            text_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Format as JSON
        import json
        raw_data = json.dumps(log.to_dict(), indent=2, ensure_ascii=False)
        
        # Insert text
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, raw_data)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dictionary for display."""
        import json
        return json.dumps(details, indent=2, ensure_ascii=False)
    
    def _copy_log_to_clipboard(self, log: ExecutionLog):
        """Copy log information to clipboard."""
        try:
            import json
            log_text = json.dumps(log.to_dict(), indent=2, ensure_ascii=False)
            
            # Copy to clipboard
            self.frame.clipboard_clear()
            self.frame.clipboard_append(log_text)
            
            messagebox.showinfo("成功", "日誌資訊已複製到剪貼簿")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"複製到剪貼簿失敗: {e}")
    
    def _export_logs(self) -> None:
        """Export logs to file."""
        try:
            # Ask for export format
            format_window = tk.Toplevel(self.frame)
            format_window.title("選擇匯出格式")
            format_window.geometry("300x150")
            format_window.transient(self.frame.winfo_toplevel())
            format_window.grab_set()
            
            selected_format = tk.StringVar(value="json")
            
            ttk.Label(format_window, text="選擇匯出格式:").pack(pady=10)
            
            ttk.Radiobutton(format_window, text="JSON", variable=selected_format, value="json").pack()
            ttk.Radiobutton(format_window, text="CSV", variable=selected_format, value="csv").pack()
            ttk.Radiobutton(format_window, text="文字檔", variable=selected_format, value="txt").pack()
            
            def do_export():
                format_window.destroy()
                
                # Get file path
                format_ext = selected_format.get()
                file_types = {
                    'json': [("JSON files", "*.json")],
                    'csv': [("CSV files", "*.csv")],
                    'txt': [("Text files", "*.txt")]
                }
                
                file_path = filedialog.asksaveasfilename(
                    title="匯出日誌",
                    defaultextension=f".{format_ext}",
                    filetypes=file_types[format_ext] + [("All files", "*.*")]
                )
                
                if file_path:
                    # Get logs to export (current filtered results)
                    logs = self.log_storage.load_logs(0, 10000, self.current_filters)
                    
                    success = self.log_storage.export_logs(logs, format_ext, file_path)
                    if success:
                        messagebox.showinfo("成功", f"日誌已匯出到 {file_path}")
                    else:
                        messagebox.showerror("錯誤", "匯出日誌失敗")
            
            ttk.Button(format_window, text="匯出", command=do_export).pack(pady=10)
            ttk.Button(format_window, text="取消", command=format_window.destroy).pack()
            
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出日誌時發生錯誤: {e}")
    
    def _clear_old_logs(self) -> None:
        """Clear old logs based on retention policy."""
        try:
            # Ask for confirmation and retention period
            retention_window = tk.Toplevel(self.frame)
            retention_window.title("清除舊日誌")
            retention_window.geometry("300x200")
            retention_window.transient(self.frame.winfo_toplevel())
            retention_window.grab_set()
            
            ttk.Label(retention_window, text="清除多少天前的日誌:").pack(pady=10)
            
            days_var = tk.IntVar(value=30)
            days_spinbox = ttk.Spinbox(retention_window, from_=1, to=365, textvariable=days_var, width=10)
            days_spinbox.pack(pady=5)
            
            def do_clear():
                days = days_var.get()
                if messagebox.askyesno("確認", f"確定要清除 {days} 天前的所有日誌嗎？此操作無法復原。"):
                    cutoff_date = datetime.now() - timedelta(days=days)
                    success = self.log_storage.delete_logs(cutoff_date)
                    
                    retention_window.destroy()
                    
                    if success:
                        messagebox.showinfo("成功", f"已清除 {days} 天前的日誌")
                        self._load_logs()  # Refresh display
                    else:
                        messagebox.showerror("錯誤", "清除日誌失敗")
            
            ttk.Button(retention_window, text="清除", command=do_clear).pack(pady=10)
            ttk.Button(retention_window, text="取消", command=retention_window.destroy).pack()
            
        except Exception as e:
            messagebox.showerror("錯誤", f"清除日誌時發生錯誤: {e}")
    
    def _show_statistics(self) -> None:
        """Show log storage statistics."""
        try:
            stats = self.log_storage.get_statistics()
            
            stats_window = tk.Toplevel(self.frame)
            stats_window.title("日誌統計資訊")
            stats_window.geometry("400x300")
            stats_window.transient(self.frame.winfo_toplevel())
            stats_window.grab_set()
            
            # Create text widget for statistics
            text_widget = tk.Text(stats_window, wrap=tk.WORD, state=tk.DISABLED)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Format statistics
            stats_text = f"""日誌存儲統計資訊

總日誌數量: {stats.get('total_logs', 0):,}
成功執行: {stats.get('successful_logs', 0):,}
失敗執行: {stats.get('failed_logs', 0):,}
成功率: {stats.get('success_rate', 0):.1f}%

存儲資訊:
當前檔案大小: {stats.get('current_file_size', 0) / 1024:.1f} KB
封存檔案數量: {stats.get('archive_count', 0)}
封存檔案大小: {stats.get('archive_size', 0) / 1024:.1f} KB
總存儲大小: {stats.get('total_size', 0) / 1024:.1f} KB

記憶體快取: {stats.get('cache_size', 0):,} 條記錄
"""
            
            text_widget.config(state=tk.NORMAL)
            text_widget.insert(tk.END, stats_text)
            text_widget.config(state=tk.DISABLED)
            
            # Close button
            ttk.Button(stats_window, text="關閉", command=stats_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"獲取統計資訊時發生錯誤: {e}")
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        self._refresh_logs()


# Backward compatibility alias
LogsPage = ScheduleLogsPage