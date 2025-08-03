"""
Main window implementation for Windows Scheduler GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from typing import Optional, Callable
from src.models.config import AppConfig
from src.utils.constants import (
    APP_NAME, APP_VERSION,
    MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT,
    MAIN_WINDOW_DEFAULT_WIDTH, MAIN_WINDOW_DEFAULT_HEIGHT
)


class MainWindow:
    """Main application window with unified navigation structure."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the main window.
        
        Args:
            config: Application configuration
        """
        self.config = config or AppConfig.get_default()
        self.root = tk.Tk()
        self.current_page = "Overview"
        self.pages = {}
        self.navigation_buttons = {}
        
        # Initialize window
        self._setup_window()
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()
        
        # Bind events
        self._bind_events()
        
    def _setup_window(self):
        """Setup main window properties."""
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.minsize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.config.window_width // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.config.window_height // 2)
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}+{x}+{y}")
        
        # Set window icon (if available)
        try:
            # You can add an icon file later
            pass
        except Exception:
            pass
    
    def _create_menu_bar(self):
        """Create the main menu bar."""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="新增任務", command=self._on_new_task)
        file_menu.add_command(label="匯入設定", command=self._on_import_config)
        file_menu.add_command(label="匯出設定", command=self._on_export_config)
        file_menu.add_separator()
        file_menu.add_command(label="結束", command=self._on_exit)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="編輯", menu=edit_menu)
        edit_menu.add_command(label="偏好設定", command=self._on_preferences)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="檢視", menu=view_menu)
        view_menu.add_command(label="重新整理", command=self._on_refresh)
        view_menu.add_command(label="全螢幕", command=self._on_toggle_fullscreen)
        
        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="系統資訊", command=self._on_system_info)
        tools_menu.add_command(label="清理日誌", command=self._on_clean_logs)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="使用說明", command=self._on_help)
        help_menu.add_command(label="關於", command=self._on_about)
    
    def _create_main_layout(self):
        """Create the main layout with navigation and content area."""
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create navigation frame
        self._create_navigation_frame()
        
        # Create content area
        self._create_content_area()
        
    def _create_navigation_frame(self):
        """Create the unified navigation structure."""
        # Navigation header with app logo/title
        nav_header = ttk.Frame(self.main_frame)
        nav_header.pack(fill=tk.X, pady=(0, 10))
        
        # App title with diamond symbol
        title_label = ttk.Label(
            nav_header, 
            text="◆ Windows-MCP", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Navigation buttons frame
        nav_buttons_frame = ttk.Frame(nav_header)
        nav_buttons_frame.pack(side=tk.RIGHT)
        
        # Navigation buttons
        nav_items = [
            ("Overview", "系統概覽"),
            ("Schedules", "排程管理"),
            ("Logs", "執行記錄"),
            ("Settings", "系統設定"),
            ("Help", "說明文件")
        ]
        
        for i, (page_id, display_name) in enumerate(nav_items):
            btn = ttk.Button(
                nav_buttons_frame,
                text=display_name,
                command=lambda p=page_id: self._switch_page(p),
                style="Navigation.TButton"
            )
            btn.pack(side=tk.LEFT, padx=(5, 0))
            self.navigation_buttons[page_id] = btn
        
        # Configure navigation button style
        self._configure_navigation_style()
        
        # Separator line
        separator = ttk.Separator(self.main_frame, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, pady=(0, 10))
    
    def _configure_navigation_style(self):
        """Configure the navigation button styles."""
        style = ttk.Style()
        
        # Configure navigation button style
        style.configure(
            "Navigation.TButton",
            padding=(10, 5),
            font=("Arial", 10)
        )
        
        # Configure active navigation button style
        style.configure(
            "NavigationActive.TButton",
            padding=(10, 5),
            font=("Arial", 10, "bold"),
            relief="solid"
        )
    
    def _create_content_area(self):
        """Create the main content area for pages."""
        # Content frame with scrollable area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for page management (hidden tabs)
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Hide notebook tabs
        style = ttk.Style()
        style.layout("Hidden.TNotebook", [])
        style.layout("Hidden.TNotebook.Tab", [])
        self.notebook.configure(style="Hidden.TNotebook")
        
        # Initialize pages
        self._initialize_pages()
        
        # Show default page
        self._switch_page("Overview")
    
    def _initialize_pages(self):
        """Initialize all application pages."""
        # Overview page
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")
        self.pages["Overview"] = overview_frame
        self._create_overview_page(overview_frame)
        
        # Schedules page
        schedules_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedules_frame, text="Schedules")
        self.pages["Schedules"] = schedules_frame
        self._create_schedules_page(schedules_frame)
        
        # Logs page
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        self.pages["Logs"] = logs_frame
        self._create_logs_page(logs_frame)
        
        # Settings page
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        self.pages["Settings"] = settings_frame
        self._create_settings_page(settings_frame)
        
        # Help page
        help_frame = ttk.Frame(self.notebook)
        self.notebook.add(help_frame, text="Help")
        self.pages["Help"] = help_frame
        self._create_help_page(help_frame)
    
    def _create_overview_page(self, parent):
        """Create the system overview page."""
        # Page title
        title_label = ttk.Label(parent, text="System Overview", font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Statistics cards frame
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Statistics cards
        stats = [
            ("Active Tasks", "12"),
            ("Total Executions", "1,247"),
            ("Success Rate", "95.2%")
        ]
        
        for i, (label, value) in enumerate(stats):
            card = ttk.LabelFrame(stats_frame, text=label, padding=10)
            card.grid(row=0, column=i, padx=(0, 10), sticky="ew")
            
            value_label = ttk.Label(card, text=value, font=("Arial", 18, "bold"))
            value_label.pack()
        
        # Configure grid weights
        for i in range(len(stats)):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # Recent Activity section
        activity_label = ttk.Label(parent, text="Recent Activity", font=("Arial", 14, "bold"))
        activity_label.pack(anchor=tk.W, pady=(20, 10))
        
        activity_frame = ttk.LabelFrame(parent, text="", padding=10)
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Activity list (placeholder)
        activities = [
            "[10:30] Daily Backup - Success",
            "[10:15] Close Browser - Success", 
            "[10:00] System Cleanup - Failed",
            "[09:45] Launch Calculator - Success"
        ]
        
        for activity in activities:
            activity_item = ttk.Label(activity_frame, text=activity)
            activity_item.pack(anchor=tk.W, pady=2)
        
        # System Status section
        status_label = ttk.Label(parent, text="System Status", font=("Arial", 14, "bold"))
        status_label.pack(anchor=tk.W, pady=(20, 10))
        
        status_frame = ttk.LabelFrame(parent, text="", padding=10)
        status_frame.pack(fill=tk.X)
        
        # Status items
        status_items = [
            "Scheduler Engine: ● Running",
            "Windows-MCP: ● Connected",
            "Log Recording: ● Enabled",
            "Next Task: Daily Backup in 2h 30m"
        ]
        
        for item in status_items:
            status_item = ttk.Label(status_frame, text=item)
            status_item.pack(anchor=tk.W, pady=2)
    
    def _create_schedules_page(self, parent):
        """Create the schedules management page."""
        title_label = ttk.Label(parent, text="Schedule Management", font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder content
        placeholder = ttk.Label(parent, text="排程管理頁面將在後續任務中實作")
        placeholder.pack(expand=True)
    
    def _create_logs_page(self, parent):
        """Create the execution logs page."""
        title_label = ttk.Label(parent, text="Execution Logs", font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder content
        placeholder = ttk.Label(parent, text="執行記錄頁面將在後續任務中實作")
        placeholder.pack(expand=True)
    
    def _create_settings_page(self, parent):
        """Create the settings page."""
        title_label = ttk.Label(parent, text="System Settings", font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder content
        placeholder = ttk.Label(parent, text="系統設定頁面將在後續任務中實作")
        placeholder.pack(expand=True)
    
    def _create_help_page(self, parent):
        """Create the help page."""
        title_label = ttk.Label(parent, text="Help & Support", font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder content
        placeholder = ttk.Label(parent, text="說明文件頁面將在後續任務中實作")
        placeholder.pack(expand=True)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status text
        self.status_text = tk.StringVar()
        self.status_text.set("就緒")
        
        status_label = ttk.Label(self.status_bar, textvariable=self.status_text)
        status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Separator
        separator = ttk.Separator(self.status_bar, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Connection status
        self.connection_status = tk.StringVar()
        self.connection_status.set("Windows-MCP: 已連接")
        
        connection_label = ttk.Label(self.status_bar, textvariable=self.connection_status)
        connection_label.pack(side=tk.LEFT, padx=5, pady=2)
    
    def _switch_page(self, page_id: str):
        """
        Switch to the specified page.
        
        Args:
            page_id: ID of the page to switch to
        """
        if page_id not in self.pages:
            return
        
        # Update navigation button styles
        for btn_id, btn in self.navigation_buttons.items():
            if btn_id == page_id:
                btn.configure(style="NavigationActive.TButton")
            else:
                btn.configure(style="Navigation.TButton")
        
        # Switch notebook page
        page_index = list(self.pages.keys()).index(page_id)
        self.notebook.select(page_index)
        
        self.current_page = page_id
        self.status_text.set(f"當前頁面: {page_id}")
    
    def _bind_events(self):
        """Bind window events."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self._on_new_task())
        self.root.bind("<Control-q>", lambda e: self._on_exit())
        self.root.bind("<F5>", lambda e: self._on_refresh())
        self.root.bind("<F11>", lambda e: self._on_toggle_fullscreen())
    
    def _on_window_close(self):
        """Handle window close event."""
        if self.config.minimize_to_tray:
            # TODO: Implement system tray functionality
            self.root.withdraw()
        else:
            self._on_exit()
    
    def _on_new_task(self):
        """Handle new task creation."""
        # TODO: Implement task creation dialog
        messagebox.showinfo("新增任務", "任務建立功能將在後續實作")
    
    def _on_import_config(self):
        """Handle configuration import."""
        # TODO: Implement config import
        messagebox.showinfo("匯入設定", "設定匯入功能將在後續實作")
    
    def _on_export_config(self):
        """Handle configuration export."""
        # TODO: Implement config export
        messagebox.showinfo("匯出設定", "設定匯出功能將在後續實作")
    
    def _on_preferences(self):
        """Handle preferences dialog."""
        # TODO: Implement preferences dialog
        messagebox.showinfo("偏好設定", "偏好設定功能將在後續實作")
    
    def _on_refresh(self):
        """Handle refresh action."""
        self.status_text.set("正在重新整理...")
        self.root.after(1000, lambda: self.status_text.set("就緒"))
    
    def _on_toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        current_state = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current_state)
    
    def _on_system_info(self):
        """Show system information."""
        # TODO: Implement system info dialog
        messagebox.showinfo("系統資訊", "系統資訊功能將在後續實作")
    
    def _on_clean_logs(self):
        """Handle log cleanup."""
        # TODO: Implement log cleanup
        messagebox.showinfo("清理日誌", "日誌清理功能將在後續實作")
    
    def _on_help(self):
        """Show help documentation."""
        self._switch_page("Help")
    
    def _on_about(self):
        """Show about dialog."""
        about_text = f"""
{APP_NAME} v{APP_VERSION}

Windows應用程式排程控制GUI

基於Python Tkinter開發的現代化排程管理工具
整合Windows-MCP功能，提供直觀的圖形介面

© 2024 Windows-MCP Project
        """
        messagebox.showinfo("關於", about_text.strip())
    
    def _on_exit(self):
        """Handle application exit."""
        if messagebox.askokcancel("結束應用程式", "確定要結束應用程式嗎？"):
            # Save window size and position
            self.config.window_width = self.root.winfo_width()
            self.config.window_height = self.root.winfo_height()
            
            # TODO: Save configuration
            
            self.root.quit()
            sys.exit(0)
    
    def run(self):
        """Start the main application loop."""
        self.root.mainloop()
    
    def set_status(self, message: str):
        """
        Set status bar message.
        
        Args:
            message: Status message to display
        """
        self.status_text.set(message)
    
    def set_connection_status(self, status: str):
        """
        Set connection status.
        
        Args:
            status: Connection status message
        """
        self.connection_status.set(f"Windows-MCP: {status}")
    
    def get_current_page(self) -> str:
        """
        Get the currently active page.
        
        Returns:
            Current page ID
        """
        return self.current_page