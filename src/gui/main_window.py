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
from src.gui.navigation import NavigationFrame
from src.gui.page_manager import PageManager
from src.gui.pages import OverviewPage, SchedulesPage, LogsPage, SettingsPage, HelpPage


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
        
        # Navigation and page management
        self.navigation_frame: Optional[NavigationFrame] = None
        self.page_manager: Optional[PageManager] = None
        
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
        
        # Create unified navigation system
        self.navigation_frame = NavigationFrame(
            self.main_frame, 
            on_page_change=self._on_page_change
        )
        
        # Create page manager
        self.page_manager = PageManager(self.main_frame)
        
        # Initialize pages
        self._initialize_pages()
        
        # Set default page
        self._switch_to_default_page()
    
    def _initialize_pages(self):
        """Initialize all application pages."""
        if not self.page_manager:
            return
        
        # Register all pages
        self.page_manager.register_page(OverviewPage)
        self.page_manager.register_page(SchedulesPage)
        self.page_manager.register_page(LogsPage)
        self.page_manager.register_page(SettingsPage)
        self.page_manager.register_page(HelpPage)
    
    def _switch_to_default_page(self):
        """Switch to the default page."""
        if self.navigation_frame:
            self.navigation_frame.switch_to_page("Overview")
    
    def _on_page_change(self, page_id: str):
        """
        Handle page change from navigation.
        
        Args:
            page_id: ID of the page to switch to
        """
        if self.page_manager:
            success = self.page_manager.switch_to_page(page_id)
            if success:
                self.set_status(f"當前頁面: {page_id}")
            else:
                self.set_status(f"無法切換到頁面: {page_id}")
    
    
    
    
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
    
    
    def _bind_events(self):
        """Bind window events."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self._on_new_task())
        self.root.bind("<Control-q>", lambda e: self._on_exit())
        self.root.bind("<F5>", lambda e: self._on_refresh())
        self.root.bind("<F11>", lambda e: self._on_toggle_fullscreen())
        
        # Window resize event for responsive layout
        self.root.bind("<Configure>", self._on_window_configure)
    
    def _on_window_configure(self, event):
        """Handle window resize for responsive layout."""
        if event.widget == self.root and self.navigation_frame:
            # Update navigation layout based on window width
            window_width = self.root.winfo_width()
            self.navigation_frame.configure_responsive_layout(window_width)
    
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
        if self.navigation_frame:
            return self.navigation_frame.get_current_page() or "Overview"
        return "Overview"
    
    def refresh_current_page(self):
        """Refresh the current page content."""
        if self.page_manager:
            self.page_manager.refresh_current_page()
    
    def switch_to_page(self, page_id: str) -> bool:
        """
        Switch to a specific page.
        
        Args:
            page_id: Page ID to switch to
            
        Returns:
            True if switch was successful
        """
        if self.navigation_frame:
            return self.navigation_frame.switch_to_page(page_id)
        return False
    
    def get_page_manager(self) -> Optional[PageManager]:
        """
        Get the page manager instance.
        
        Returns:
            PageManager instance or None
        """
        return self.page_manager
    
    def get_navigation_frame(self) -> Optional[NavigationFrame]:
        """
        Get the navigation frame instance.
        
        Returns:
            NavigationFrame instance or None
        """
        return self.navigation_frame