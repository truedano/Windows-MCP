"""
Application List Widget for displaying running applications.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable
import threading
import time

from ...models.data_models import App
from ...core.windows_controller import WindowsController


class AppListWidget(ttk.Frame):
    """Widget for displaying and managing the list of running applications."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the AppListWidget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for Frame
        """
        super().__init__(parent, **kwargs)
        
        self.windows_controller = WindowsController()
        self.apps: List[App] = []
        self.filtered_apps: List[App] = []
        self.selected_app: Optional[App] = None
        self.on_app_selected: Optional[Callable[[App], None]] = None
        self.auto_refresh = True
        self.refresh_interval = 5  # seconds
        self.refresh_thread: Optional[threading.Thread] = None
        self.stop_refresh = threading.Event()
        
        self._setup_ui()
        self._start_auto_refresh()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Search and filter frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search entry
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Filter options
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="All")
        self.filter_combo = ttk.Combobox(
            search_frame, 
            textvariable=self.filter_var,
            values=["All", "Visible Only", "With Windows"],
            state="readonly",
            width=15
        )
        self.filter_combo.pack(side=tk.LEFT, padx=(5, 10))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Refresh button
        self.refresh_button = ttk.Button(
            search_frame, 
            text="Refresh", 
            command=self.refresh_apps
        )
        self.refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.auto_refresh_checkbox = ttk.Checkbutton(
            search_frame,
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            command=self._on_auto_refresh_changed
        )
        self.auto_refresh_checkbox.pack(side=tk.RIGHT, padx=5)
        
        # Applications list frame
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for applications list
        columns = ("Name", "Title", "PID", "Status", "Position", "Size")
        self.app_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.app_tree.heading("Name", text="Application")
        self.app_tree.heading("Title", text="Window Title")
        self.app_tree.heading("PID", text="Process ID")
        self.app_tree.heading("Status", text="Status")
        self.app_tree.heading("Position", text="Position")
        self.app_tree.heading("Size", text="Size")
        
        # Set column widths
        self.app_tree.column("Name", width=120, minwidth=80)
        self.app_tree.column("Title", width=200, minwidth=100)
        self.app_tree.column("PID", width=80, minwidth=60)
        self.app_tree.column("Status", width=80, minwidth=60)
        self.app_tree.column("Position", width=100, minwidth=80)
        self.app_tree.column("Size", width=100, minwidth=80)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.app_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.app_tree.xview)
        self.app_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.app_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.app_tree.bind('<<TreeviewSelect>>', self._on_app_selected)
        
        # Status label
        self.status_label = ttk.Label(self, text="Ready")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        # Load initial data
        self.refresh_apps()
    
    def _start_auto_refresh(self):
        """Start the auto-refresh thread."""
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            self.stop_refresh.clear()
            self.refresh_thread = threading.Thread(target=self._auto_refresh_worker, daemon=True)
            self.refresh_thread.start()
    
    def _stop_auto_refresh(self):
        """Stop the auto-refresh thread."""
        self.stop_refresh.set()
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=1)
    
    def _auto_refresh_worker(self):
        """Worker thread for auto-refreshing the application list."""
        while not self.stop_refresh.is_set():
            if self.auto_refresh:
                try:
                    # Schedule refresh on main thread
                    self.after_idle(self._refresh_apps_background)
                except tk.TclError:
                    # Widget has been destroyed
                    break
            
            # Wait for the specified interval or until stop is requested
            self.stop_refresh.wait(self.refresh_interval)
    
    def _refresh_apps_background(self):
        """Refresh apps in background without blocking UI."""
        try:
            self.status_label.config(text="Refreshing applications...")
            self.refresh_button.config(state="disabled")
            
            # Get applications in a separate thread to avoid blocking UI
            def get_apps():
                try:
                    apps = self.windows_controller.get_running_apps()
                    self.after_idle(lambda: self._update_apps_list(apps))
                except Exception as e:
                    self.after_idle(lambda: self._handle_refresh_error(str(e)))
            
            threading.Thread(target=get_apps, daemon=True).start()
            
        except Exception as e:
            self._handle_refresh_error(str(e))
    
    def _update_apps_list(self, apps: List[App]):
        """Update the applications list with new data."""
        try:
            self.apps = apps
            self._apply_filters()
            self._update_treeview()
            
            self.status_label.config(text=f"Found {len(self.apps)} applications ({len(self.filtered_apps)} shown)")
            self.refresh_button.config(state="normal")
            
        except Exception as e:
            self._handle_refresh_error(str(e))
    
    def _handle_refresh_error(self, error_msg: str):
        """Handle refresh errors."""
        self.status_label.config(text=f"Error: {error_msg}")
        self.refresh_button.config(state="normal")
    
    def refresh_apps(self):
        """Manually refresh the applications list."""
        self._refresh_apps_background()
    
    def _apply_filters(self):
        """Apply search and filter criteria to the applications list."""
        search_text = self.search_var.get().lower()
        filter_option = self.filter_var.get()
        
        self.filtered_apps = []
        
        for app in self.apps:
            # Apply search filter
            if search_text:
                if (search_text not in app.name.lower() and 
                    search_text not in app.title.lower()):
                    continue
            
            # Apply visibility filter
            if filter_option == "Visible Only" and not app.is_visible:
                continue
            elif filter_option == "With Windows" and not app.title:
                continue
            
            self.filtered_apps.append(app)
    
    def _update_treeview(self):
        """Update the treeview with filtered applications."""
        # Clear existing items
        for item in self.app_tree.get_children():
            self.app_tree.delete(item)
        
        # Add filtered applications
        for app in self.filtered_apps:
            status = "Visible" if app.is_visible else "Hidden"
            position = f"({app.x}, {app.y})" if app.x or app.y else "N/A"
            size = f"{app.width}×{app.height}" if app.width and app.height else "N/A"
            
            self.app_tree.insert("", tk.END, values=(
                app.name,
                app.title or "No Title",
                app.process_id,
                status,
                position,
                size
            ))
    
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        self._apply_filters()
        self._update_treeview()
        self.status_label.config(text=f"Found {len(self.apps)} applications ({len(self.filtered_apps)} shown)")
    
    def _on_filter_changed(self, event=None):
        """Handle filter option changes."""
        self._apply_filters()
        self._update_treeview()
        self.status_label.config(text=f"Found {len(self.apps)} applications ({len(self.filtered_apps)} shown)")
    
    def _on_auto_refresh_changed(self):
        """Handle auto-refresh checkbox changes."""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()
    
    def _on_app_selected(self, event=None):
        """Handle application selection in the treeview."""
        selection = self.app_tree.selection()
        if selection:
            item = selection[0]
            values = self.app_tree.item(item, 'values')
            
            # Find the corresponding app
            app_name = values[0]
            pid = int(values[2])
            
            for app in self.filtered_apps:
                if app.name == app_name and app.process_id == pid:
                    self.selected_app = app
                    if self.on_app_selected:
                        self.on_app_selected(app)
                    break
    
    def get_selected_app(self) -> Optional[App]:
        """Get the currently selected application."""
        return self.selected_app
    
    def set_app_selection_callback(self, callback: Callable[[App], None]):
        """Set the callback function for application selection."""
        self.on_app_selected = callback
    
    def set_refresh_interval(self, interval: int):
        """Set the auto-refresh interval in seconds."""
        self.refresh_interval = max(1, interval)  # Minimum 1 second
    
    def destroy(self):
        """Clean up resources when widget is destroyed."""
        self._stop_auto_refresh()
        super().destroy()