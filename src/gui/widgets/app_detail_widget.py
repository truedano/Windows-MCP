"""
Application Detail Widget for displaying detailed information about selected applications.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import threading

from ...models.data_models import App
from ...core.windows_controller import WindowsController
from ...models.execution import ExecutionResult


class AppDetailWidget(ttk.Frame):
    """Widget for displaying detailed information about a selected application."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the AppDetailWidget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for Frame
        """
        super().__init__(parent, **kwargs)
        
        self.windows_controller = WindowsController()
        self.current_app: Optional[App] = None
        self.on_action_completed: Optional[Callable[[ExecutionResult], None]] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Title
        title_label = ttk.Label(self, text="Application Details", font=("TkDefaultFont", 12, "bold"))
        title_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Main content frame
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Application info section
        info_frame = ttk.LabelFrame(content_frame, text="Application Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create info labels
        self.info_labels = {}
        info_fields = [
            ("Name", "app_name"),
            ("Window Title", "window_title"),
            ("Process ID", "process_id"),
            ("Status", "status"),
            ("Position", "position"),
            ("Size", "size"),
            ("Visibility", "visibility")
        ]
        
        for i, (label_text, key) in enumerate(info_fields):
            ttk.Label(info_frame, text=f"{label_text}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            value_label = ttk.Label(info_frame, text="N/A", foreground="gray")
            value_label.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            self.info_labels[key] = value_label
        
        # Configure grid weights
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Window operations section
        operations_frame = ttk.LabelFrame(content_frame, text="Quick Operations", padding=10)
        operations_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create operation buttons
        button_frame = ttk.Frame(operations_frame)
        button_frame.pack(fill=tk.X)
        
        # Row 1: Window state operations
        state_frame = ttk.Frame(button_frame)
        state_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.focus_button = ttk.Button(
            state_frame, 
            text="Focus", 
            command=lambda: self._execute_action("focus"),
            width=12
        )
        self.focus_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.minimize_button = ttk.Button(
            state_frame, 
            text="Minimize", 
            command=lambda: self._execute_action("minimize"),
            width=12
        )
        self.minimize_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.maximize_button = ttk.Button(
            state_frame, 
            text="Maximize", 
            command=lambda: self._execute_action("maximize"),
            width=12
        )
        self.maximize_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.close_button = ttk.Button(
            state_frame, 
            text="Close", 
            command=lambda: self._execute_action("close"),
            width=12
        )
        self.close_button.pack(side=tk.LEFT)
        
        # Row 2: Position and size operations
        transform_frame = ttk.Frame(button_frame)
        transform_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Move controls
        move_frame = ttk.Frame(transform_frame)
        move_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(move_frame, text="Move to:").pack(side=tk.LEFT)
        self.move_x_var = tk.StringVar(value="100")
        self.move_y_var = tk.StringVar(value="100")
        
        ttk.Entry(move_frame, textvariable=self.move_x_var, width=6).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Label(move_frame, text=",").pack(side=tk.LEFT)
        ttk.Entry(move_frame, textvariable=self.move_y_var, width=6).pack(side=tk.LEFT, padx=(2, 5))
        
        ttk.Button(
            move_frame, 
            text="Move", 
            command=lambda: self._execute_action("move"),
            width=8
        ).pack(side=tk.LEFT)
        
        # Resize controls
        resize_frame = ttk.Frame(transform_frame)
        resize_frame.pack(side=tk.LEFT)
        
        ttk.Label(resize_frame, text="Resize to:").pack(side=tk.LEFT)
        self.resize_width_var = tk.StringVar(value="800")
        self.resize_height_var = tk.StringVar(value="600")
        
        ttk.Entry(resize_frame, textvariable=self.resize_width_var, width=6).pack(side=tk.LEFT, padx=(5, 2))
        ttk.Label(resize_frame, text="×").pack(side=tk.LEFT)
        ttk.Entry(resize_frame, textvariable=self.resize_height_var, width=6).pack(side=tk.LEFT, padx=(2, 5))
        
        ttk.Button(
            resize_frame, 
            text="Resize", 
            command=lambda: self._execute_action("resize"),
            width=8
        ).pack(side=tk.LEFT)
        
        # Status section
        status_frame = ttk.LabelFrame(content_frame, text="Operation Status", padding=10)
        status_frame.pack(fill=tk.X)
        
        self.status_text = tk.Text(status_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initially disable all buttons
        self._set_buttons_enabled(False)
        
        # Show empty state
        self._show_empty_state()
    
    def _show_empty_state(self):
        """Show empty state when no application is selected."""
        for label in self.info_labels.values():
            label.config(text="N/A", foreground="gray")
        
        self._add_status_message("No application selected. Select an application from the list to view details.")
    
    def set_app(self, app: Optional[App]):
        """
        Set the application to display details for.
        
        Args:
            app: Application to display, or None to clear
        """
        self.current_app = app
        
        if app:
            self._update_app_info(app)
            self._set_buttons_enabled(True)
            self._add_status_message(f"Displaying details for {app.name}")
        else:
            self._show_empty_state()
            self._set_buttons_enabled(False)
    
    def _update_app_info(self, app: App):
        """Update the application information display."""
        self.info_labels["app_name"].config(text=app.name, foreground="black")
        self.info_labels["window_title"].config(text=app.title or "No Title", foreground="black")
        self.info_labels["process_id"].config(text=str(app.process_id), foreground="black")
        self.info_labels["status"].config(text="Running", foreground="green")
        
        position_text = f"({app.x}, {app.y})" if app.x or app.y else "Unknown"
        self.info_labels["position"].config(text=position_text, foreground="black")
        
        size_text = f"{app.width} × {app.height}" if app.width and app.height else "Unknown"
        self.info_labels["size"].config(text=size_text, foreground="black")
        
        visibility_text = "Visible" if app.is_visible else "Hidden"
        visibility_color = "green" if app.is_visible else "orange"
        self.info_labels["visibility"].config(text=visibility_text, foreground=visibility_color)
        
        # Update move/resize fields with current values
        if app.x or app.y:
            self.move_x_var.set(str(app.x))
            self.move_y_var.set(str(app.y))
        
        if app.width and app.height:
            self.resize_width_var.set(str(app.width))
            self.resize_height_var.set(str(app.height))
    
    def _set_buttons_enabled(self, enabled: bool):
        """Enable or disable all operation buttons."""
        buttons = [
            self.focus_button, self.minimize_button, self.maximize_button, 
            self.close_button
        ]
        
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in buttons:
            button.config(state=state)
    
    def _execute_action(self, action: str):
        """
        Execute an action on the current application.
        
        Args:
            action: Action to execute ('focus', 'minimize', 'maximize', 'close', 'move', 'resize')
        """
        if not self.current_app:
            self._add_status_message("Error: No application selected", "error")
            return
        
        # Disable buttons during operation
        self._set_buttons_enabled(False)
        self._add_status_message(f"Executing {action} on {self.current_app.name}...")
        
        # Execute action in background thread
        def execute():
            try:
                result = None
                app_name = self.current_app.name
                
                if action == "focus":
                    result = self.windows_controller.focus_window(app_name)
                elif action == "minimize":
                    result = self.windows_controller.minimize_window(app_name)
                elif action == "maximize":
                    result = self.windows_controller.maximize_window(app_name)
                elif action == "close":
                    result = self.windows_controller.close_app(app_name)
                elif action == "move":
                    try:
                        x = int(self.move_x_var.get())
                        y = int(self.move_y_var.get())
                        result = self.windows_controller.move_window(app_name, x, y)
                    except ValueError:
                        result = ExecutionResult.failure_result(
                            operation="move_window",
                            target=app_name,
                            message="Invalid coordinates. Please enter numeric values."
                        )
                elif action == "resize":
                    try:
                        width = int(self.resize_width_var.get())
                        height = int(self.resize_height_var.get())
                        result = self.windows_controller.resize_window(app_name, width, height)
                    except ValueError:
                        result = ExecutionResult.failure_result(
                            operation="resize_window",
                            target=app_name,
                            message="Invalid dimensions. Please enter numeric values."
                        )
                
                # Update UI on main thread
                if result:
                    self.after_idle(lambda: self._handle_action_result(result))
                
            except Exception as e:
                error_result = ExecutionResult.failure_result(
                    operation=action,
                    target=self.current_app.name if self.current_app else "unknown",
                    message=f"Unexpected error: {str(e)}"
                )
                self.after_idle(lambda: self._handle_action_result(error_result))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def _handle_action_result(self, result: ExecutionResult):
        """Handle the result of an action execution."""
        # Re-enable buttons
        self._set_buttons_enabled(True)
        
        # Add status message
        if result.success:
            self._add_status_message(f"✓ {result.message}", "success")
        else:
            self._add_status_message(f"✗ {result.message}", "error")
        
        # Notify callback if set
        if self.on_action_completed:
            self.on_action_completed(result)
    
    def _add_status_message(self, message: str, message_type: str = "info"):
        """
        Add a status message to the status text area.
        
        Args:
            message: Message to add
            message_type: Type of message ('info', 'success', 'error')
        """
        self.status_text.config(state=tk.NORMAL)
        
        # Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Configure tags for different message types
        if not hasattr(self, '_tags_configured'):
            self.status_text.tag_configure("success", foreground="green")
            self.status_text.tag_configure("error", foreground="red")
            self.status_text.tag_configure("info", foreground="black")
            self.status_text.tag_configure("timestamp", foreground="gray")
            self._tags_configured = True
        
        # Insert message
        self.status_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.status_text.insert(tk.END, f"{message}\n", message_type)
        
        # Auto-scroll to bottom
        self.status_text.see(tk.END)
        
        # Limit text length (keep last 100 lines)
        lines = self.status_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.status_text.delete("1.0", f"{len(lines) - 100}.0")
        
        self.status_text.config(state=tk.DISABLED)
    
    def set_action_completed_callback(self, callback: Callable[[ExecutionResult], None]):
        """Set the callback function for action completion."""
        self.on_action_completed = callback
    
    def refresh_app_info(self):
        """Refresh the current application information."""
        if self.current_app:
            # This would typically re-query the application state
            # For now, we'll just update the display with current data
            self._update_app_info(self.current_app)
            self._add_status_message(f"Refreshed information for {self.current_app.name}")