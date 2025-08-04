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
from src.gui.pages import OverviewPage, SchedulesPage, ScheduleDetailPage, LogsPage, SettingsPage, HelpPage, AppsPage
from src.core.task_manager import TaskManager
from src.storage.task_storage import TaskStorage


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
        
        # Core components
        self.task_storage = TaskStorage()
        self.task_manager = TaskManager(self.task_storage)
        
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
        # Register SchedulesPage with task_manager parameter
        self.page_manager.register_page(SchedulesPage, task_manager=self.task_manager)
        # Register ScheduleDetailPage with task_manager parameter
        self.page_manager.register_page(ScheduleDetailPage, task_manager=self.task_manager)
        self.page_manager.register_page(AppsPage)
        self.page_manager.register_page(LogsPage)
        self.page_manager.register_page(SettingsPage)
        self.page_manager.register_page(HelpPage)
    
    def _switch_to_default_page(self):
        """Switch to the default page."""
        if self.navigation_frame:
            self.navigation_frame.switch_to_page("Overview")
            self.set_status("歡迎使用 Windows 排程控制 GUI")
    
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
            window_height = self.root.winfo_height()
            
            # Configure responsive layout
            self.navigation_frame.configure_responsive_layout(window_width)
            
            # Update page manager layout if needed
            if self.page_manager:
                self.page_manager.update_layout(window_width, window_height)
    
    def _on_window_close(self):
        """Handle window close event."""
        if self.config.minimize_to_tray:
            # TODO: Implement system tray functionality
            self.root.withdraw()
        else:
            self._on_exit()
    
    def _on_new_task(self):
        """Handle new task creation."""
        try:
            from src.gui.dialogs.schedule_dialog import ScheduleDialog
            
            # Create and show the schedule dialog
            dialog = ScheduleDialog(self.root, on_save=self._on_task_saved_from_menu)
            result = dialog.show()
            
            if result:
                self.set_status("新任務已建立")
                # Switch to schedules page to show the new task
                self.switch_to_page("Schedules")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"無法建立新任務:\n{str(e)}")
    
    def _on_task_saved_from_menu(self, task):
        """Handle task save from menu dialog."""
        try:
            self.task_manager.create_task(task)
            self.set_status(f"任務 '{task.name}' 已建立")
        except Exception as e:
            messagebox.showerror("錯誤", f"無法儲存任務:\n{str(e)}")
            raise
    
    def _on_import_config(self):
        """Handle configuration import."""
        try:
            from tkinter import filedialog
            from src.core.config_manager import get_config_manager
            import json
            
            # Ask user to select config file
            file_path = filedialog.askopenfilename(
                title="選擇設定檔案",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                config_manager = get_config_manager()
                
                # Load and validate config file
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Import configuration
                config_manager.import_config(config_data)
                
                messagebox.showinfo("匯入成功", "設定已成功匯入")
                self.set_status("設定匯入完成")
                
        except Exception as e:
            messagebox.showerror("匯入失敗", f"無法匯入設定:\n{str(e)}")
    
    def _on_export_config(self):
        """Handle configuration export."""
        try:
            from tkinter import filedialog
            from src.core.config_manager import get_config_manager
            import json
            from datetime import datetime
            
            # Ask user where to save config file
            file_path = filedialog.asksaveasfilename(
                title="儲存設定檔案",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialname=f"scheduler_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if file_path:
                config_manager = get_config_manager()
                
                # Export configuration
                config_data = config_manager.export_config()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("匯出成功", f"設定已匯出至:\n{file_path}")
                self.set_status("設定匯出完成")
                
        except Exception as e:
            messagebox.showerror("匯出失敗", f"無法匯出設定:\n{str(e)}")
    
    def _on_preferences(self):
        """Handle preferences dialog."""
        # Switch to settings page
        self.switch_to_page("Settings")
        self.set_status("已開啟設定頁面")
    
    def _on_refresh(self):
        """Handle refresh action."""
        self.set_status("正在重新整理...")
        
        # Refresh current page content
        self.refresh_current_page()
        
        # Update status after refresh
        self.root.after(500, lambda: self.set_status("重新整理完成"))
    
    def _on_toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        current_state = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current_state)
    
    def _on_system_info(self):
        """Show system information."""
        try:
            import platform
            import psutil
            from src.utils.constants import APP_NAME, APP_VERSION
            
            # Gather system information
            system_info = f"""
{APP_NAME} v{APP_VERSION}

系統資訊:
作業系統: {platform.system()} {platform.release()}
處理器: {platform.processor()}
Python版本: {platform.python_version()}
記憶體使用: {psutil.virtual_memory().percent:.1f}%
磁碟使用: {psutil.disk_usage('/').percent:.1f}%

應用程式狀態:
任務數量: {len(self.task_manager.get_all_tasks())}
當前頁面: {self.get_current_page()}
            """.strip()
            
            messagebox.showinfo("系統資訊", system_info)
            
        except Exception as e:
            # Fallback system info without psutil
            basic_info = f"""
{APP_NAME} v{APP_VERSION}

基本資訊:
作業系統: {platform.system()} {platform.release()}
Python版本: {platform.python_version()}
任務數量: {len(self.task_manager.get_all_tasks())}
當前頁面: {self.get_current_page()}
            """.strip()
            
            messagebox.showinfo("系統資訊", basic_info)
    
    def _on_clean_logs(self):
        """Handle log cleanup."""
        try:
            from src.storage.log_storage import get_log_storage
            from datetime import datetime, timedelta
            
            # Ask for confirmation
            result = messagebox.askyesno(
                "清理日誌", 
                "確定要清理30天前的舊日誌嗎？\n此操作無法復原。"
            )
            
            if result:
                log_storage = get_log_storage()
                cutoff_date = datetime.now() - timedelta(days=30)
                
                # Clean old logs
                deleted_count = log_storage.delete_logs(cutoff_date)
                
                messagebox.showinfo(
                    "清理完成", 
                    f"已清理 {deleted_count} 筆舊日誌記錄"
                )
                self.set_status(f"已清理 {deleted_count} 筆日誌")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"清理日誌時發生錯誤:\n{str(e)}")
    
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