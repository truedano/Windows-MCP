"""
Execution history dialog for displaying task execution logs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.models.execution import ExecutionLog
from src.storage.log_storage import get_log_storage


class ExecutionHistoryDialog:
    """Dialog for viewing task execution history."""
    
    def __init__(self, parent: tk.Widget, task_id: str, task_name: str):
        """
        Initialize execution history dialog.
        
        Args:
            parent: Parent widget
            task_id: ID of the task to show history for
            task_name: Name of the task for display
        """
        self.parent = parent
        self.task_id = task_id
        self.task_name = task_name
        self.log_storage = get_log_storage()
        self.logs: List[ExecutionLog] = []
        self.filtered_logs: List[ExecutionLog] = []
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Execution History - {task_name}")
        self.dialog.geometry("1200x800")
        self.dialog.minsize(800, 600)  # Set minimum size
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self._center_dialog()
        
        # Setup UI
        self._setup_ui()
        
        # Load execution logs
        self._load_logs()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_dialog(self) -> None:
        """Center dialog on parent window."""
        self.dialog.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # Get dialog size
        dialog_width = 1200
        dialog_height = 800
        
        # Calculate center position on screen
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        
        # Ensure dialog doesn't go off screen
        x = max(0, x)
        y = max(0, y)
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Configure grid weights
        self.dialog.grid_rowconfigure(1, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        
        # Header frame
        self._create_header_frame()
        
        # Filter frame
        self._create_filter_frame()
        
        # Logs frame
        self._create_logs_frame()
        
        # Button frame
        self._create_button_frame()
    
    def _create_header_frame(self) -> None:
        """Create header with task information."""
        header_frame = ttk.Frame(self.dialog)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Icon and title
        icon_label = ttk.Label(header_frame, text="📊", font=("Segoe UI", 16))
        icon_label.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ttk.Label(
            header_frame,
            text=f"Execution History for '{self.task_name}'",
            font=("Segoe UI", 12, "bold")
        )
        title_label.grid(row=0, column=1, sticky="w")
        
        # Task ID
        id_label = ttk.Label(
            header_frame,
            text=f"Task ID: {self.task_id}",
            font=("Consolas", 9),
            foreground="#666666"
        )
        id_label.grid(row=1, column=1, sticky="w")
    
    def _create_filter_frame(self) -> None:
        """Create filter controls."""
        filter_frame = ttk.LabelFrame(self.dialog, text="Filters", padding=10)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1)
        
        # Status filter
        ttk.Label(filter_frame, text="Status:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=["All", "Success", "Failed"],
            state="readonly",
            width=10
        )
        status_combo.grid(row=0, column=1, sticky="w", padx=(0, 20))
        status_combo.bind("<<ComboboxSelected>>", self._apply_filters)
        
        # Date range filter
        ttk.Label(filter_frame, text="Date Range:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.date_var = tk.StringVar(value="All Time")
        date_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.date_var,
            values=["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
            state="readonly",
            width=15
        )
        date_combo.grid(row=0, column=3, sticky="w", padx=(0, 20))
        date_combo.bind("<<ComboboxSelected>>", self._apply_filters)
        
        # Refresh button
        refresh_button = ttk.Button(
            filter_frame,
            text="🔄 Refresh",
            command=self._refresh_logs
        )
        refresh_button.grid(row=0, column=4, padx=(10, 0))
    
    def _create_logs_frame(self) -> None:
        """Create logs display frame."""
        logs_frame = ttk.Frame(self.dialog)
        logs_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        logs_frame.grid_rowconfigure(0, weight=1)
        logs_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview for logs
        columns = ("time", "status", "operation", "duration", "message")
        self.tree = ttk.Treeview(logs_frame, columns=columns, show="headings", height=20)
        
        # Configure columns
        self.tree.heading("time", text="Execution Time")
        self.tree.heading("status", text="Status")
        self.tree.heading("operation", text="Operation")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("message", text="Message")
        
        self.tree.column("time", width=180, anchor="w")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("operation", width=150, anchor="w")
        self.tree.column("duration", width=100, anchor="center")
        self.tree.column("message", width=500, anchor="w")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(logs_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(logs_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind double-click to show details
        self.tree.bind("<Double-1>", self._show_log_details)
        
        # Context menu
        self._create_context_menu()
    
    def _create_context_menu(self) -> None:
        """Create context menu for log entries."""
        self.context_menu = tk.Menu(self.dialog, tearoff=0)
        self.context_menu.add_command(label="View Details", command=self._show_selected_log_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Message", command=self._copy_log_message)
        self.context_menu.add_command(label="Copy All Info", command=self._copy_log_info)
        
        # Bind right-click
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _create_button_frame(self) -> None:
        """Create button frame."""
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # Statistics label
        self.stats_label = ttk.Label(
            button_frame,
            text="No logs found",
            font=("Segoe UI", 9),
            foreground="#666666"
        )
        self.stats_label.pack(side=tk.LEFT)
        
        # Export button
        export_button = ttk.Button(
            button_frame,
            text="📤 Export",
            command=self._export_logs
        )
        export_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Close button
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self._on_close
        )
        close_button.pack(side=tk.RIGHT)
    
    def _load_logs(self) -> None:
        """Load execution logs for the task."""
        try:
            # Get logs filtered by task name (schedule_name)
            filters = {"schedule_name": self.task_name}
            self.logs = self.log_storage.load_logs(0, 1000, filters)
            self.filtered_logs = self.logs.copy()
            self._update_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load execution logs: {str(e)}")
    
    def _apply_filters(self, event=None) -> None:
        """Apply filters to the logs."""
        try:
            self.filtered_logs = self.logs.copy()
            
            # Apply status filter
            status_filter = self.status_var.get()
            if status_filter == "Success":
                self.filtered_logs = [log for log in self.filtered_logs if log.result.success]
            elif status_filter == "Failed":
                self.filtered_logs = [log for log in self.filtered_logs if not log.result.success]
            
            # Apply date filter
            date_filter = self.date_var.get()
            if date_filter != "All Time":
                now = datetime.now()
                if date_filter == "Last 24 Hours":
                    cutoff = now - timedelta(hours=24)
                elif date_filter == "Last 7 Days":
                    cutoff = now - timedelta(days=7)
                elif date_filter == "Last 30 Days":
                    cutoff = now - timedelta(days=30)
                else:
                    cutoff = None
                
                if cutoff:
                    self.filtered_logs = [log for log in self.filtered_logs if log.execution_time >= cutoff]
            
            self._update_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters: {str(e)}")
    
    def _update_display(self) -> None:
        """Update the logs display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered logs
        for log in self.filtered_logs:
            # Format values
            time_str = self._format_datetime(log.execution_time)
            status_str = "✅ Success" if log.result.success else "❌ Failed"
            operation_str = log.result.operation
            duration_str = f"{log.duration.total_seconds():.2f}s"
            message_str = log.result.message[:100] + "..." if len(log.result.message) > 100 else log.result.message
            
            # Set row color based on status
            tags = ("success",) if log.result.success else ("failed",)
            
            self.tree.insert("", "end", values=(
                time_str, status_str, operation_str, duration_str, message_str
            ), tags=tags)
        
        # Configure row colors
        self.tree.tag_configure("success", foreground="#28A745")
        self.tree.tag_configure("failed", foreground="#DC3545")
        
        # Update statistics
        self._update_statistics()
    
    def _update_statistics(self) -> None:
        """Update statistics display."""
        total = len(self.filtered_logs)
        if total == 0:
            self.stats_label.config(text="No logs found")
            return
        
        success_count = sum(1 for log in self.filtered_logs if log.result.success)
        failed_count = total - success_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        stats_text = f"Total: {total} | Success: {success_count} | Failed: {failed_count} | Success Rate: {success_rate:.1f}%"
        self.stats_label.config(text=stats_text)
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        if dt.date() == now.date():
            return f"Today {dt.strftime('%H:%M:%S')}"
        elif dt.year == now.year:
            return dt.strftime("%m/%d %H:%M:%S")
        else:
            return dt.strftime("%Y/%m/%d %H:%M:%S")
    
    def _show_context_menu(self, event) -> None:
        """Show context menu."""
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _show_log_details(self, event) -> None:
        """Show detailed information for selected log."""
        self._show_selected_log_details()
    
    def _show_selected_log_details(self) -> None:
        """Show details for the selected log entry."""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get selected log
        item_index = self.tree.index(selection[0])
        if item_index < len(self.filtered_logs):
            log = self.filtered_logs[item_index]
            self._show_log_detail_dialog(log)
    
    def _show_log_detail_dialog(self, log: ExecutionLog) -> None:
        """Show detailed dialog for a specific log entry."""
        detail_dialog = tk.Toplevel(self.dialog)
        detail_dialog.title("Execution Log Details")
        # Use a larger, adaptive default size and center on screen
        screen_w = detail_dialog.winfo_screenwidth()
        screen_h = detail_dialog.winfo_screenheight()
        width = max(900, int(screen_w * 0.7))
        height = max(600, int(screen_h * 0.7))
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        detail_dialog.geometry(f"{width}x{height}+{x}+{y}")
        detail_dialog.minsize(800, 500)
        detail_dialog.resizable(True, True)
        detail_dialog.transient(self.dialog)
        detail_dialog.grab_set()
        
        # Create scrollable text widget
        text_frame = ttk.Frame(detail_dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format log details
        details = f"""Execution Log Details
{'=' * 50}

Log ID: {log.id}
Task Name: {log.schedule_name}
Execution Time: {log.execution_time.isoformat()}
Duration: {log.duration.total_seconds():.3f} seconds
Retry Count: {log.retry_count}

Result Information:
{'=' * 20}
Success: {'Yes' if log.result.success else 'No'}
Operation: {log.result.operation}
Target: {log.result.target}
Message: {log.result.message}
Timestamp: {log.result.timestamp.isoformat()}

"""
        
        if log.result.details:
            details += f"""Additional Details:
{'=' * 20}
{self._format_details(log.result.details)}
"""
        
        text_widget.insert(tk.END, details)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        button_frame = ttk.Frame(detail_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Close",
            command=detail_dialog.destroy
        ).pack(side=tk.RIGHT)
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dictionary for display."""
        import json
        try:
            return json.dumps(details, indent=2, ensure_ascii=False)
        except:
            return str(details)
    
    def _copy_log_message(self) -> None:
        """Copy selected log message to clipboard."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_index = self.tree.index(selection[0])
        if item_index < len(self.filtered_logs):
            log = self.filtered_logs[item_index]
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(log.result.message)
            messagebox.showinfo("Copied", "Log message copied to clipboard")
    
    def _copy_log_info(self) -> None:
        """Copy selected log information to clipboard."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_index = self.tree.index(selection[0])
        if item_index < len(self.filtered_logs):
            log = self.filtered_logs[item_index]
            info = f"""Log ID: {log.id}
Task: {log.schedule_name}
Time: {log.execution_time.isoformat()}
Status: {'Success' if log.result.success else 'Failed'}
Operation: {log.result.operation}
Target: {log.result.target}
Message: {log.result.message}
Duration: {log.duration.total_seconds():.3f}s
Retries: {log.retry_count}"""
            
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(info)
            messagebox.showinfo("Copied", "Log information copied to clipboard")
    
    def _export_logs(self) -> None:
        """Export filtered logs to file."""
        if not self.filtered_logs:
            messagebox.showwarning("No Data", "No logs to export")
            return
        
        from tkinter import filedialog
        
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            title="Export Execution Logs",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Determine format from extension
            if file_path.lower().endswith('.csv'):
                format_type = 'csv'
            elif file_path.lower().endswith('.txt'):
                format_type = 'txt'
            else:
                format_type = 'json'
            
            # Export logs
            success = self.log_storage.export_logs(self.filtered_logs, format_type, file_path)
            
            if success:
                messagebox.showinfo("Export Complete", f"Logs exported successfully to:\n{file_path}")
            else:
                messagebox.showerror("Export Failed", "Failed to export logs")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting logs: {str(e)}")
    
    def _refresh_logs(self) -> None:
        """Refresh the logs from storage."""
        self._load_logs()
    
    def _on_close(self) -> None:
        """Handle dialog close."""
        self.dialog.destroy()
    
    def show(self) -> None:
        """Show the dialog."""
        self.dialog.wait_window()


def show_execution_history(parent: tk.Widget, task_id: str, task_name: str) -> None:
    """
    Show execution history dialog for a task.
    
    Args:
        parent: Parent widget
        task_id: ID of the task
        task_name: Name of the task
    """
    dialog = ExecutionHistoryDialog(parent, task_id, task_name)
    dialog.show()