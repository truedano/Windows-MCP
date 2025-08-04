"""
Execution logs page implementation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from src.gui.page_manager import BasePage
from src.storage.log_storage import get_log_storage
from src.models.execution import ExecutionLog


class LogsPage(BasePage):
    """Execution logs page with full log management functionality."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize logs page."""
        super().__init__(parent, "Logs", "執行記錄")
        self.log_storage = get_log_storage()
        self.current_page = 0
        self.page_size = 50
        self.current_filters: Dict[str, Any] = {}
        self.logs_tree: Optional[ttk.Treeview] = None
        self.search_var = tk.StringVar()
        self.filter_vars: Dict[str, tk.Variable] = {}
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="Execution Logs",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="查看任務執行歷史和日誌",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Create main container
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create search and filter panel
        self._create_search_panel(main_container)
        
        # Create logs display
        self._create_logs_display(main_container)
        
        # Create action buttons
        self._create_action_buttons(main_container)
        
        # Load initial logs
        self._load_logs()
    
    def _create_search_panel(self, parent: tk.Widget) -> None:
        """Create search and filter panel."""
        search_frame = ttk.LabelFrame(parent, text="搜尋和篩選", padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Search row
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_row, text="搜尋:").pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind('<Return>', lambda e: self._apply_filters())
        
        search_btn = ttk.Button(search_row, text="搜尋", command=self._apply_filters)
        search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(search_row, text="清除", command=self._clear_filters)
        clear_btn.pack(side=tk.LEFT)
        
        # Filter row
        filter_row = ttk.Frame(search_frame)
        filter_row.pack(fill=tk.X)
        
        # Schedule filter
        ttk.Label(filter_row, text="排程:").pack(side=tk.LEFT, padx=(0, 5))
        schedule_var = tk.StringVar()
        schedule_combo = ttk.Combobox(filter_row, textvariable=schedule_var, width=15, state="readonly")
        schedule_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.filter_vars['schedule'] = schedule_var
        
        # Status filter
        ttk.Label(filter_row, text="狀態:").pack(side=tk.LEFT, padx=(0, 5))
        status_var = tk.StringVar()
        status_combo = ttk.Combobox(
            filter_row, textvariable=status_var, 
            values=["全部", "成功", "失敗"], width=10, state="readonly"
        )
        status_combo.set("全部")
        status_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.filter_vars['status'] = status_var
        
        # Date range filter
        ttk.Label(filter_row, text="日期範圍:").pack(side=tk.LEFT, padx=(0, 5))
        date_var = tk.StringVar()
        date_combo = ttk.Combobox(
            filter_row, textvariable=date_var,
            values=["全部", "今天", "昨天", "本週", "本月"], width=10, state="readonly"
        )
        date_combo.set("全部")
        date_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.filter_vars['date_range'] = date_var
        
        # Bind filter changes
        for var in self.filter_vars.values():
            var.trace('w', lambda *args: self._apply_filters())
        
        # Update schedule combo with available schedules
        self._update_schedule_filter()
    
    def _create_logs_display(self, parent: tk.Widget) -> None:
        """Create logs display with treeview."""
        display_frame = ttk.LabelFrame(parent, text="執行日誌", padding=5)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(display_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Define columns
        columns = ("time", "schedule", "operation", "target", "status", "duration", "message")
        self.logs_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure column headings and widths
        self.logs_tree.heading("time", text="執行時間")
        self.logs_tree.heading("schedule", text="排程名稱")
        self.logs_tree.heading("operation", text="操作")
        self.logs_tree.heading("target", text="目標")
        self.logs_tree.heading("status", text="狀態")
        self.logs_tree.heading("duration", text="持續時間")
        self.logs_tree.heading("message", text="訊息")
        
        self.logs_tree.column("time", width=150, minwidth=120)
        self.logs_tree.column("schedule", width=120, minwidth=100)
        self.logs_tree.column("operation", width=100, minwidth=80)
        self.logs_tree.column("target", width=100, minwidth=80)
        self.logs_tree.column("status", width=60, minwidth=50)
        self.logs_tree.column("duration", width=80, minwidth=70)
        self.logs_tree.column("message", width=200, minwidth=150)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.logs_tree.xview)
        self.logs_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to show details
        self.logs_tree.bind("<Double-1>", self._show_log_details)
        
        # Create pagination controls
        self._create_pagination_controls(display_frame)
    
    def _create_pagination_controls(self, parent: tk.Widget) -> None:
        """Create pagination controls."""
        pagination_frame = ttk.Frame(parent)
        pagination_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Previous button
        self.prev_btn = ttk.Button(
            pagination_frame, text="上一頁", command=self._previous_page
        )
        self.prev_btn.pack(side=tk.LEFT)
        
        # Page info
        self.page_info_label = ttk.Label(pagination_frame, text="")
        self.page_info_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Next button
        self.next_btn = ttk.Button(
            pagination_frame, text="下一頁", command=self._next_page
        )
        self.next_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Page size selector
        ttk.Label(pagination_frame, text="每頁顯示:").pack(side=tk.RIGHT, padx=(0, 5))
        page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_combo = ttk.Combobox(
            pagination_frame, textvariable=page_size_var,
            values=["25", "50", "100", "200"], width=8, state="readonly"
        )
        page_size_combo.pack(side=tk.RIGHT)
        page_size_combo.bind('<<ComboboxSelected>>', self._change_page_size)
        self.page_size_var = page_size_var
    
    def _create_action_buttons(self, parent: tk.Widget) -> None:
        """Create action buttons."""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=5)
        
        # Refresh button
        refresh_btn = ttk.Button(
            action_frame, text="重新整理", command=self._load_logs
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Export button
        export_btn = ttk.Button(
            action_frame, text="匯出日誌", command=self._export_logs
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear old logs button
        clear_btn = ttk.Button(
            action_frame, text="清除舊日誌", command=self._clear_old_logs
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Statistics button
        stats_btn = ttk.Button(
            action_frame, text="統計資訊", command=self._show_statistics
        )
        stats_btn.pack(side=tk.LEFT, padx=5)
    
    def _load_logs(self) -> None:
        """Load logs from storage and display them."""
        try:
            # Clear existing items
            if self.logs_tree:
                for item in self.logs_tree.get_children():
                    self.logs_tree.delete(item)
            
            # Load logs with current filters and pagination
            logs = self.log_storage.load_logs(self.current_page, self.page_size, self.current_filters)
            
            # Populate treeview
            for log in logs:
                self._add_log_to_tree(log)
            
            # Update pagination info
            self._update_pagination_info(len(logs))
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入日誌時發生錯誤: {e}")
    
    def _add_log_to_tree(self, log: ExecutionLog) -> None:
        """Add a log entry to the treeview."""
        if not self.logs_tree:
            return
        
        # Format values for display
        time_str = log.execution_time.strftime("%Y-%m-%d %H:%M:%S")
        status_str = "成功" if log.result.success else "失敗"
        duration_str = f"{log.duration.total_seconds():.2f}s"
        
        # Determine row color based on status
        tags = ("success",) if log.result.success else ("failure",)
        
        # Insert row
        item = self.logs_tree.insert("", tk.END, values=(
            time_str,
            log.schedule_name,
            log.result.operation,
            log.result.target,
            status_str,
            duration_str,
            log.result.message
        ), tags=tags)
        
        # Store log ID for reference
        self.logs_tree.set(item, "#0", log.id)
        
        # Configure row colors
        self.logs_tree.tag_configure("success", background="#e8f5e8")
        self.logs_tree.tag_configure("failure", background="#ffe8e8")
    
    def _apply_filters(self) -> None:
        """Apply current filters and reload logs."""
        self.current_filters = {}
        
        # Text search
        search_text = self.search_var.get().strip()
        if search_text:
            self.current_filters['query'] = search_text
        
        # Schedule filter
        schedule = self.filter_vars['schedule'].get()
        if schedule and schedule != "全部":
            self.current_filters['schedule_name'] = schedule
        
        # Status filter
        status = self.filter_vars['status'].get()
        if status == "成功":
            self.current_filters['success'] = True
        elif status == "失敗":
            self.current_filters['success'] = False
        
        # Date range filter
        date_range = self.filter_vars['date_range'].get()
        if date_range != "全部":
            today = datetime.now().date()
            if date_range == "今天":
                self.current_filters['start_date'] = today
                self.current_filters['end_date'] = today
            elif date_range == "昨天":
                yesterday = today - timedelta(days=1)
                self.current_filters['start_date'] = yesterday
                self.current_filters['end_date'] = yesterday
            elif date_range == "本週":
                week_start = today - timedelta(days=today.weekday())
                self.current_filters['start_date'] = week_start
                self.current_filters['end_date'] = today
            elif date_range == "本月":
                month_start = today.replace(day=1)
                self.current_filters['start_date'] = month_start
                self.current_filters['end_date'] = today
        
        # Reset to first page and reload
        self.current_page = 0
        self._load_logs()
    
    def _clear_filters(self) -> None:
        """Clear all filters and reload logs."""
        self.search_var.set("")
        self.filter_vars['schedule'].set("")
        self.filter_vars['status'].set("全部")
        self.filter_vars['date_range'].set("全部")
        self.current_filters = {}
        self.current_page = 0
        self._load_logs()
    
    def _update_schedule_filter(self) -> None:
        """Update schedule filter combo with available schedules."""
        try:
            # Get all logs to extract unique schedule names
            all_logs = self.log_storage.load_logs(0, 1000, {})
            schedules = set(log.schedule_name for log in all_logs)
            
            # Update combo values
            if 'schedule' in self.filter_vars:
                combo_widget = None
                for widget in self.frame.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.LabelFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ttk.Frame):
                                        for ggchild in grandchild.winfo_children():
                                            if isinstance(ggchild, ttk.Combobox):
                                                if ggchild['textvariable'] == str(self.filter_vars['schedule']):
                                                    combo_widget = ggchild
                                                    break
                
                if combo_widget:
                    combo_widget['values'] = ["全部"] + sorted(schedules)
                    
        except Exception as e:
            print(f"Error updating schedule filter: {e}")
    
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
    
    def _update_pagination_info(self, logs_count: int) -> None:
        """Update pagination information."""
        start_idx = self.current_page * self.page_size + 1
        end_idx = start_idx + logs_count - 1
        
        if logs_count == 0:
            info_text = "沒有日誌記錄"
        else:
            info_text = f"顯示 {start_idx}-{end_idx} 項"
        
        if hasattr(self, 'page_info_label'):
            self.page_info_label.config(text=info_text)
        
        # Update button states
        if hasattr(self, 'prev_btn'):
            self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        
        if hasattr(self, 'next_btn'):
            self.next_btn.config(state=tk.NORMAL if logs_count == self.page_size else tk.DISABLED)
    
    def _show_log_details(self, event=None) -> None:
        """Show detailed information for selected log."""
        if not self.logs_tree:
            return
        
        selection = self.logs_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        log_id = self.logs_tree.set(item, "#0")
        
        # Find the log in storage
        logs = self.log_storage.load_logs(0, 1000, {})
        log = next((l for l in logs if l.id == log_id), None)
        
        if not log:
            messagebox.showerror("錯誤", "找不到日誌記錄")
            return
        
        # Create details window
        self._create_log_details_window(log)
    
    def _create_log_details_window(self, log: ExecutionLog) -> None:
        """Create a window showing detailed log information."""
        details_window = tk.Toplevel(self.frame)
        details_window.title("日誌詳細資訊")
        details_window.geometry("600x400")
        details_window.transient(self.frame.winfo_toplevel())
        details_window.grab_set()
        
        # Create scrollable text widget
        text_frame = ttk.Frame(details_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format log details
        details = f"""日誌 ID: {log.id}
排程名稱: {log.schedule_name}
執行時間: {log.execution_time.strftime('%Y-%m-%d %H:%M:%S')}
持續時間: {log.duration.total_seconds():.2f} 秒
重試次數: {log.retry_count}

執行結果:
  狀態: {'成功' if log.result.success else '失敗'}
  操作: {log.result.operation}
  目標: {log.result.target}
  訊息: {log.result.message}
  時間戳記: {log.result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if log.result.details:
            details += f"\n詳細資訊:\n{log.result.details}"
        
        # Insert text
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, details)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        close_btn = ttk.Button(details_window, text="關閉", command=details_window.destroy)
        close_btn.pack(pady=10)
    
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
        self._load_logs()
        self._update_schedule_filter()