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
    """Enhanced search bar widget with advanced filtering capabilities."""
    
    def __init__(self, parent: tk.Widget, on_search: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """Initialize search bar widget."""
        self.parent = parent
        self.on_search = on_search
        self.search_var = tk.StringVar()
        self.filter_vars: Dict[str, tk.Variable] = {}
        
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
            values=["全部", "今天", "昨天", "本週", "本月"], 
            width=12, 
            state="readonly"
        )
        self.date_combo.set("全部")
        self.date_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.filter_vars['date_range'] = date_var
        
        # Bind filter changes
        for var in self.filter_vars.values():
            var.trace('w', lambda *args: self._on_filter_change())
    
    def _on_search_enter(self, event=None):
        """Handle Enter key in search entry."""
        self._perform_search()
    
    def _on_filter_change(self):
        """Handle filter changes."""
        self._perform_search()
    
    def _perform_search(self):
        """Perform search with current criteria."""
        search_query = self.search_var.get().strip()
        filters = self._get_current_filters()
        
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
        
        return filters
    
    def update_filter_options(self, schedules: List[str], operations: List[str]):
        """Update filter dropdown options."""
        # Update schedule options
        schedule_values = ["全部"] + sorted(schedules)
        self.schedule_combo['values'] = schedule_values
    
    def get_search_query(self) -> str:
        """Get current search query."""
        return self.search_var.get().strip()
    
    def get_filters(self) -> Dict[str, Any]:
        """Get current filters."""
        return self._get_current_filters()


class LogsTableWidget:
    """Enhanced logs table widget with sorting and highlighting."""
    
    def __init__(self, parent: tk.Widget, on_log_select: Optional[Callable[[ExecutionLog], None]] = None):
        """Initialize logs table widget."""
        self.parent = parent
        self.on_log_select = on_log_select
        self.logs: List[ExecutionLog] = []
        self.sort_column = "time"
        self.sort_reverse = True
        
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
        
        # Configure row styles
        self._configure_row_styles()
    
    def _configure_row_styles(self):
        """Configure row styles for different log types."""
        self.tree.tag_configure("success", background="#e8f5e8", foreground="#2d5a2d")
        self.tree.tag_configure("failure", background="#ffe8e8", foreground="#5a2d2d")
    
    def _sort_by_column(self, column: str):
        """Sort table by column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
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
            log_id = selection[0]
            log = next((l for l in self.logs if l.id == log_id), None)
            if log:
                self.on_log_select(log)
    
    def update_logs(self, logs: List[ExecutionLog], search_query: str = ""):
        """Update table with new logs."""
        self.logs = logs.copy()
        self._sort_logs()
        self._refresh_display()
    
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
        
        self.tree.insert("", tk.END, iid=log.id, values=values, tags=tags)


class PaginationWidget:
    """Pagination widget for log navigation."""
    
    def __init__(self, parent: tk.Widget, on_page_change: Optional[Callable[[int], None]] = None):
        """Initialize pagination widget."""
        self.parent = parent
        self.on_page_change = on_page_change
        self.current_page = 0
        self.total_pages = 0
        self.page_size = 50
        self.total_items = 0
        
        self._create_pagination_ui()
    
    def _create_pagination_ui(self):
        """Create pagination UI."""
        self.pagination_frame = ttk.Frame(self.parent)
        self.pagination_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Page info
        self.info_label = ttk.Label(self.pagination_frame, text="")
        self.info_label.pack(side=tk.LEFT)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.pagination_frame)
        nav_frame.pack(side=tk.RIGHT)
        
        # Previous page
        self.prev_btn = ttk.Button(
            nav_frame, 
            text="◀️ 上一頁", 
            command=self._go_previous,
            width=8
        )
        self.prev_btn.pack(side=tk.LEFT, padx=1)
        
        # Next page
        self.next_btn = ttk.Button(
            nav_frame, 
            text="下一頁 ▶️", 
            command=self._go_next,
            width=8
        )
        self.next_btn.pack(side=tk.LEFT, padx=1)
        
        # Page size selector
        ttk.Label(nav_frame, text="每頁:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_combo = ttk.Combobox(
            nav_frame,
            textvariable=self.page_size_var,
            values=["25", "50", "100", "200"],
            width=5,
            state="readonly"
        )
        page_size_combo.pack(side=tk.LEFT)
        page_size_combo.bind('<<ComboboxSelected>>', self._on_page_size_change)
        
        self._update_ui()
    
    def _go_previous(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._page_changed()
    
    def _go_next(self):
        """Go to next page."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._page_changed()
    
    def _on_page_size_change(self, event=None):
        """Handle page size change."""
        try:
            new_page_size = int(self.page_size_var.get())
            if new_page_size != self.page_size:
                self.page_size = new_page_size
                self._recalculate_pagination()
                self._page_changed()
        except ValueError:
            pass
    
    def _page_changed(self):
        """Handle page change."""
        self._update_ui()
        if self.on_page_change:
            self.on_page_change(self.current_page)
    
    def _recalculate_pagination(self):
        """Recalculate pagination based on new page size."""
        if self.total_items > 0:
            self.total_pages = (self.total_items + self.page_size - 1) // self.page_size
            if self.current_page >= self.total_pages:
                self.current_page = max(0, self.total_pages - 1)
        else:
            self.total_pages = 0
            self.current_page = 0
    
    def _update_ui(self):
        """Update pagination UI."""
        # Update info label
        if self.total_items > 0:
            start_item = self.current_page * self.page_size + 1
            end_item = min((self.current_page + 1) * self.page_size, self.total_items)
            self.info_label.config(
                text=f"顯示 {start_item}-{end_item} / 共 {self.total_items} 筆記錄"
            )
        else:
            self.info_label.config(text="無記錄")
        
        # Update button states
        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)
    
    def update_pagination(self, total_items: int, current_page: int = None):
        """Update pagination information."""
        self.total_items = total_items
        self._recalculate_pagination()
        
        if current_page is not None:
            self.current_page = max(0, min(current_page, self.total_pages - 1))
        
        self._update_ui()
    
    def get_current_page(self) -> int:
        """Get current page number (0-based)."""
        return self.current_page
    
    def get_page_size(self) -> int:
        """Get current page size."""
        return self.page_size
    
    def reset(self):
        """Reset pagination to first page."""
        self.current_page = 0
        self._update_ui()


class LogExportWidget:
    """Widget for log export and management functions."""
    
    def __init__(self, parent: tk.Widget, on_export: Optional[Callable[[str, str], None]] = None,
                 on_clear_logs: Optional[Callable[[datetime], None]] = None,
                 on_backup: Optional[Callable[[], None]] = None):
        """Initialize log export widget."""
        self.parent = parent
        self.on_export = on_export
        self.on_clear_logs = on_clear_logs
        self.on_backup = on_backup
        
        self._create_export_ui()
    
    def _create_export_ui(self):
        """Create export and management UI."""
        # Export and management frame
        self.export_frame = ttk.LabelFrame(self.parent, text="日誌管理", padding=10)
        self.export_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Export section
        export_section = ttk.Frame(self.export_frame)
        export_section.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(export_section, text="匯出格式:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        # Export format selection
        self.export_format = tk.StringVar(value="csv")
        formats = [("CSV", "csv"), ("JSON", "json"), ("TXT", "txt")]
        
        for text, value in formats:
            ttk.Radiobutton(
                export_section, 
                text=text, 
                variable=self.export_format, 
                value=value
            ).pack(side=tk.LEFT, padx=(0, 15))
        
        # Export button
        self.export_btn = ttk.Button(
            export_section,
            text="📤 匯出日誌",
            command=self._export_logs,
            style="Accent.TButton"
        )
        self.export_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Management section
        management_section = ttk.Frame(self.export_frame)
        management_section.pack(fill=tk.X)
        
        # Clear logs section
        clear_frame = ttk.Frame(management_section)
        clear_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(clear_frame, text="清理日誌:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear options
        self.clear_option = tk.StringVar(value="30_days")
        clear_options = [
            ("30天前", "30_days"),
            ("90天前", "90_days"),
            ("1年前", "1_year")
        ]
        
        self.clear_combo = ttk.Combobox(
            clear_frame,
            textvariable=self.clear_option,
            values=[opt[0] for opt in clear_options],
            state="readonly",
            width=12
        )
        self.clear_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        self.clear_btn = ttk.Button(
            clear_frame,
            text="🗑️ 清理日誌",
            command=self._clear_logs
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Backup button
        self.backup_btn = ttk.Button(
            management_section,
            text="💾 備份日誌",
            command=self._backup_logs
        )
        self.backup_btn.pack(side=tk.RIGHT)
    
    def _export_logs(self):
        """Handle log export."""
        format_type = self.export_format.get()
        
        # Open file dialog
        file_types = {
            'csv': [('CSV files', '*.csv'), ('All files', '*.*')],
            'json': [('JSON files', '*.json'), ('All files', '*.*')],
            'txt': [('Text files', '*.txt'), ('All files', '*.*')]
        }
        
        default_extension = {
            'csv': '.csv',
            'json': '.json',
            'txt': '.txt'
        }
        
        file_path = filedialog.asksaveasfilename(
            title=f"匯出日誌為 {format_type.upper()}",
            filetypes=file_types[format_type],
            defaultextension=default_extension[format_type]
        )
        
        if file_path and self.on_export:
            self.on_export(format_type, file_path)
    
    def _clear_logs(self):
        """Handle log clearing."""
        option = self.clear_option.get()
        
        # Calculate cutoff date
        now = datetime.now()
        if option == "30天前":
            cutoff_date = now - timedelta(days=30)
            message = "這將刪除30天前的所有日誌記錄。"
        elif option == "90天前":
            cutoff_date = now - timedelta(days=90)
            message = "這將刪除90天前的所有日誌記錄。"
        elif option == "1年前":
            cutoff_date = now - timedelta(days=365)
            message = "這將刪除1年前的所有日誌記錄。"
        else:
            return
        
        # Confirm deletion
        result = messagebox.askyesno(
            "確認清理日誌",
            f"{message}\n\n此操作無法復原，確定要繼續嗎？",
            icon="warning"
        )
        
        if result and self.on_clear_logs:
            self.on_clear_logs(cutoff_date)
    
    def _backup_logs(self):
        """Handle log backup."""
        if self.on_backup:
            self.on_backup()


class ScheduleLogsPage(BasePage):
    """Enhanced schedule logs page with comprehensive log management."""
    
    def __init__(self, parent: tk.Widget, page_manager):
        """Initialize schedule logs page."""
        super().__init__(parent, "Logs", "執行記錄")
        self.page_manager = page_manager
        self.log_storage = get_log_storage()
        self.current_logs: List[ExecutionLog] = []
        self.current_filters: Dict[str, Any] = {}
        self.current_search_query: str = ""
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        self._create_page_ui()
        self._load_initial_data()
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        self._refresh_logs()
    
    def _create_page_ui(self):
        """Create page user interface."""
        if not self.frame:
            return
            
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        title_label = ttk.Label(
            header_frame,
            text="執行記錄",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Refresh button
        refresh_btn = ttk.Button(
            header_frame,
            text="🔄 重新整理",
            command=self._refresh_logs
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Search bar
        self.search_bar = SearchBarWidget(
            self.frame,
            on_search=self._on_search
        )
        
        # Export and management widget
        self.export_widget = LogExportWidget(
            self.frame,
            on_export=self._export_logs,
            on_clear_logs=self._clear_logs,
            on_backup=self._backup_logs
        )
        
        # Logs table
        self.logs_table = LogsTableWidget(
            self.frame,
            on_log_select=self._on_log_select
        )
        
        # Pagination
        self.pagination = PaginationWidget(
            self.frame,
            on_page_change=self._on_page_change
        )
    
    def _load_initial_data(self):
        """Load initial log data."""
        try:
            # Load filter options
            self._update_filter_options()
            
            # Load first page of logs
            self._load_logs_page(0)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入日誌資料失敗：{str(e)}")
    
    def _update_filter_options(self):
        """Update filter dropdown options."""
        try:
            # Get unique schedule names and operations
            all_logs = self.log_storage.load_logs(0, 1000, {})
            
            schedules = list(set(log.schedule_name for log in all_logs))
            operations = list(set(log.result.operation for log in all_logs))
            
            self.search_bar.update_filter_options(schedules, operations)
            
        except Exception as e:
            print(f"Error updating filter options: {e}")
    
    def _on_search(self, query: str, filters: Dict[str, Any]):
        """Handle search request."""
        self.current_search_query = query
        self.current_filters = filters.copy()
        
        # Add query to filters if provided
        if query:
            self.current_filters['query'] = query
        
        # Reset to first page and load
        self.pagination.reset()
        self._load_logs_page(0)
    
    def _on_page_change(self, page: int):
        """Handle page change."""
        self._load_logs_page(page)
    
    def _load_logs_page(self, page: int):
        """Load logs for specific page."""
        try:
            page_size = self.pagination.get_page_size()
            
            # Load logs with current filters
            logs = self.log_storage.load_logs(page, page_size, self.current_filters)
            
            # Get total count for pagination
            total_logs = self._get_total_log_count()
            
            # Update UI
            self.current_logs = logs
            self.logs_table.update_logs(logs, self.current_search_query)
            self.pagination.update_pagination(total_logs, page)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入日誌頁面失敗：{str(e)}")
    
    def _get_total_log_count(self) -> int:
        """Get total count of logs matching current filters."""
        try:
            all_matching_logs = self.log_storage.load_logs(0, 10000, self.current_filters)
            return len(all_matching_logs)
        except Exception:
            return 0
    
    def _refresh_logs(self):
        """Refresh log data."""
        try:
            self._update_filter_options()
            current_page = self.pagination.get_current_page()
            self._load_logs_page(current_page)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"重新整理失敗：{str(e)}")
    
    def _export_logs(self, format_type: str, file_path: str):
        """Export current logs."""
        try:
            # Get all logs matching current filters
            all_logs = self.log_storage.load_logs(0, 10000, self.current_filters)
            
            success = self.log_storage.export_logs(all_logs, format_type, file_path)
            
            if success:
                messagebox.showinfo("成功", f"日誌已匯出至：{file_path}")
            else:
                messagebox.showerror("錯誤", "匯出日誌失敗")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出日誌失敗：{str(e)}")
    
    def _clear_logs(self, cutoff_date: datetime):
        """Clear logs before cutoff date."""
        try:
            success = self.log_storage.delete_logs(cutoff_date)
            
            if success:
                # Refresh current view
                self._refresh_logs()
                messagebox.showinfo("成功", f"已清理{cutoff_date.strftime('%Y-%m-%d')}之前的日誌")
            else:
                messagebox.showerror("錯誤", "清理日誌失敗")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"清理日誌失敗：{str(e)}")
    
    def _backup_logs(self):
        """Backup all logs."""
        try:
            # Choose backup location
            backup_path = filedialog.asksaveasfilename(
                title="備份日誌",
                filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
                defaultextension='.json'
            )
            
            if backup_path:
                # Get all logs
                all_logs = self.log_storage.load_logs(0, 10000, {})
                
                # Export as JSON backup
                success = self.log_storage.export_logs(all_logs, 'json', backup_path)
                
                if success:
                    messagebox.showinfo("成功", f"日誌已備份至：{backup_path}")
                else:
                    messagebox.showerror("錯誤", "備份日誌失敗")
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"備份日誌失敗：{str(e)}")
    
    def _on_log_select(self, log: ExecutionLog):
        """Handle log selection."""
        # Show log details dialog
        dialog = LogDetailDialog(self.frame, log)
        dialog.show()


class LogDetailDialog:
    """Dialog for displaying detailed log information."""
    
    def __init__(self, parent: tk.Widget, log: ExecutionLog):
        """Initialize log detail dialog."""
        self.parent = parent
        self.log = log
        self.dialog = None
    
    def show(self):
        """Show log detail dialog."""
        self._create_dialog()
        self.dialog.mainloop()
    
    def _create_dialog(self):
        """Create log detail dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"日誌詳細資訊 - {self.log.schedule_name}")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log information
        info_frame = ttk.LabelFrame(main_frame, text="基本資訊", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_data = [
            ("日誌ID", self.log.id),
            ("排程名稱", self.log.schedule_name),
            ("執行時間", self.log.execution_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("執行狀態", "成功" if self.log.result.success else "失敗"),
            ("操作類型", self.log.result.operation),
            ("目標", self.log.result.target),
            ("持續時間", f"{self.log.duration.total_seconds():.2f}秒"),
            ("重試次數", str(self.log.retry_count))
        ]
        
        for i, (label, value) in enumerate(info_data):
            row_frame = ttk.Frame(info_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(row_frame, text=f"{label}:", width=12, anchor="w").pack(side=tk.LEFT)
            ttk.Label(row_frame, text=str(value), font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        # Message
        message_frame = ttk.LabelFrame(main_frame, text="執行訊息", padding=10)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        message_text = tk.Text(
            message_frame,
            wrap=tk.WORD,
            height=8,
            font=("Consolas", 9)
        )
        message_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar to message text
        message_scrollbar = ttk.Scrollbar(message_frame, orient="vertical", command=message_text.yview)
        message_text.configure(yscrollcommand=message_scrollbar.set)
        message_scrollbar.pack(side="right", fill="y")
        
        # Insert message
        message_text.insert(tk.END, self.log.result.message)
        message_text.config(state=tk.DISABLED)
        
        # Details (if available)
        if self.log.result.details:
            details_frame = ttk.LabelFrame(main_frame, text="詳細資訊", padding=10)
            details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            details_text = tk.Text(
                details_frame,
                wrap=tk.WORD,
                height=6,
                font=("Consolas", 9)
            )
            details_text.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbar to details text
            details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=details_text.yview)
            details_text.configure(yscrollcommand=details_scrollbar.set)
            details_scrollbar.pack(side="right", fill="y")
            
            # Insert details
            import json
            details_json = json.dumps(self.log.result.details, indent=2, ensure_ascii=False)
            details_text.insert(tk.END, details_json)
            details_text.config(state=tk.DISABLED)
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="關閉",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)