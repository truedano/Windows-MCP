"""
Unified navigation system for Windows Scheduler GUI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional, List, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class NavigationState(Enum):
    """Navigation state enumeration."""
    NORMAL = "normal"
    ACTIVE = "active"
    DISABLED = "disabled"
    HOVER = "hover"


@dataclass
class NavigationItem:
    """Navigation item configuration."""
    page_id: str
    display_name: str
    description: str
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    shortcut: Optional[str] = None


class PageInterface(ABC):
    """Interface for navigation pages."""
    
    @abstractmethod
    def get_page_id(self) -> str:
        """Get the unique page identifier."""
        pass
    
    @abstractmethod
    def get_display_name(self) -> str:
        """Get the display name for navigation."""
        pass
    
    @abstractmethod
    def on_page_enter(self) -> None:
        """Called when page becomes active."""
        pass
    
    @abstractmethod
    def on_page_leave(self) -> None:
        """Called when page becomes inactive."""
        pass
    
    @abstractmethod
    def refresh_content(self) -> None:
        """Refresh page content."""
        pass


class NavigationFrame:
    """
    Unified navigation frame managing page switching and state.
    """
    
    def __init__(self, parent: tk.Widget, on_page_change: Optional[Callable[[str], None]] = None):
        """
        Initialize navigation frame.
        
        Args:
            parent: Parent widget
            on_page_change: Callback for page changes
        """
        self.parent = parent
        self.on_page_change = on_page_change
        
        # Navigation state
        self.current_page: Optional[str] = None
        self.navigation_items: Dict[str, NavigationItem] = {}
        self.navigation_buttons: Dict[str, ttk.Button] = {}
        self.page_history: List[str] = []
        self.max_history_size = 10
        
        # UI components
        self.nav_frame: Optional[ttk.Frame] = None
        self.header_frame: Optional[ttk.Frame] = None
        self.buttons_frame: Optional[ttk.Frame] = None
        
        # Style configuration
        self.style = ttk.Style()
        self._configure_styles()
        
        # Create navigation UI
        self._create_navigation_ui()
        
        # Initialize default navigation items
        self._initialize_default_items()
    
    def _configure_styles(self):
        """Configure navigation button styles."""
        # Normal navigation button
        self.style.configure(
            "Navigation.TButton",
            padding=(12, 8),
            font=("Segoe UI", 10),
            relief="flat",
            borderwidth=0
        )
        
        # Active navigation button
        self.style.configure(
            "NavigationActive.TButton",
            padding=(12, 8),
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            borderwidth=2,
            background="#0078d4",
            foreground="white"
        )
        
        # Hover state
        self.style.map(
            "Navigation.TButton",
            background=[("active", "#f0f0f0")],
            relief=[("active", "solid")],
            borderwidth=[("active", 1)]
        )
        
        # Disabled state
        self.style.configure(
            "NavigationDisabled.TButton",
            padding=(12, 8),
            font=("Segoe UI", 10),
            relief="flat",
            borderwidth=0,
            foreground="#999999"
        )
    
    def _create_navigation_ui(self):
        """Create the navigation user interface."""
        # Main navigation frame
        self.nav_frame = ttk.Frame(self.parent)
        self.nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Header frame with app title
        self.header_frame = ttk.Frame(self.nav_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # App title with diamond symbol
        title_label = ttk.Label(
            self.header_frame,
            text="◆ Windows-MCP",
            font=("Segoe UI", 16, "bold"),
            foreground="#0078d4"
        )
        title_label.pack(side=tk.LEFT)
        
        # Navigation buttons frame
        self.buttons_frame = ttk.Frame(self.header_frame)
        self.buttons_frame.pack(side=tk.RIGHT)
        
        # Separator line
        separator = ttk.Separator(self.nav_frame, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, pady=(5, 0))
    
    def _initialize_default_items(self):
        """Initialize default navigation items."""
        default_items = [
            NavigationItem(
                page_id="Overview",
                display_name="系統概覽",
                description="顯示系統狀態、任務統計和最近活動",
                shortcut="Ctrl+1"
            ),
            NavigationItem(
                page_id="Schedules",
                display_name="排程管理",
                description="管理排程任務、建立和編輯排程",
                shortcut="Ctrl+2"
            ),
            NavigationItem(
                page_id="Logs",
                display_name="執行記錄",
                description="查看任務執行歷史和日誌",
                shortcut="Ctrl+3"
            ),
            NavigationItem(
                page_id="Settings",
                display_name="系統設定",
                description="配置應用程式設定和偏好",
                shortcut="Ctrl+4"
            ),
            NavigationItem(
                page_id="Help",
                display_name="說明文件",
                description="使用指南、FAQ和支援資訊",
                shortcut="F1"
            )
        ]
        
        for item in default_items:
            self.add_navigation_item(item)
    
    def add_navigation_item(self, item: NavigationItem):
        """
        Add a navigation item.
        
        Args:
            item: Navigation item to add
        """
        self.navigation_items[item.page_id] = item
        
        if item.visible:
            self._create_navigation_button(item)
    
    def remove_navigation_item(self, page_id: str):
        """
        Remove a navigation item.
        
        Args:
            page_id: Page ID to remove
        """
        if page_id in self.navigation_items:
            # Remove button if exists
            if page_id in self.navigation_buttons:
                self.navigation_buttons[page_id].destroy()
                del self.navigation_buttons[page_id]
            
            # Remove from items
            del self.navigation_items[page_id]
            
            # Switch to another page if current page is removed
            if self.current_page == page_id:
                available_pages = [pid for pid in self.navigation_items.keys() 
                                 if self.navigation_items[pid].enabled]
                if available_pages:
                    self.switch_to_page(available_pages[0])
    
    def _create_navigation_button(self, item: NavigationItem):
        """
        Create a navigation button for the item.
        
        Args:
            item: Navigation item
        """
        if not self.buttons_frame:
            return
        
        # Create button
        button = ttk.Button(
            self.buttons_frame,
            text=item.display_name,
            command=lambda: self.switch_to_page(item.page_id),
            style="Navigation.TButton"
        )
        
        # Pack button
        button.pack(side=tk.LEFT, padx=(8, 0))
        
        # Store button reference
        self.navigation_buttons[item.page_id] = button
        
        # Add tooltip if description exists
        if item.description:
            self._add_tooltip(button, item.description)
        
        # Bind keyboard shortcut
        if item.shortcut:
            self._bind_shortcut(item.shortcut, item.page_id)
    
    def _add_tooltip(self, widget: tk.Widget, text: str):
        """
        Add tooltip to widget.
        
        Args:
            widget: Widget to add tooltip to
            text: Tooltip text
        """
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip,
                text=text,
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 9)
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _bind_shortcut(self, shortcut: str, page_id: str):
        """
        Bind keyboard shortcut for navigation.
        
        Args:
            shortcut: Keyboard shortcut (e.g., "Ctrl+1")
            page_id: Target page ID
        """
        # Convert shortcut to Tkinter format
        tk_shortcut = shortcut.replace("Ctrl", "Control")
        
        def shortcut_handler(event):
            self.switch_to_page(page_id)
        
        # Bind to parent widget
        self.parent.bind_all(f"<{tk_shortcut}>", shortcut_handler)
    
    def switch_to_page(self, page_id: str, add_to_history: bool = True) -> bool:
        """
        Switch to the specified page.
        
        Args:
            page_id: Page ID to switch to
            add_to_history: Whether to add to navigation history
            
        Returns:
            True if switch was successful
        """
        # Validate page exists and is enabled
        if page_id not in self.navigation_items:
            return False
        
        item = self.navigation_items[page_id]
        if not item.enabled:
            return False
        
        # Store previous page
        previous_page = self.current_page
        
        # Add to history
        if add_to_history and previous_page and previous_page != page_id:
            self._add_to_history(previous_page)
        
        # Update current page
        self.current_page = page_id
        
        # Update button styles
        self._update_button_styles()
        
        # Call page change callback
        if self.on_page_change:
            self.on_page_change(page_id)
        
        return True
    
    def _add_to_history(self, page_id: str):
        """
        Add page to navigation history.
        
        Args:
            page_id: Page ID to add
        """
        if page_id in self.page_history:
            self.page_history.remove(page_id)
        
        self.page_history.append(page_id)
        
        # Limit history size
        if len(self.page_history) > self.max_history_size:
            self.page_history.pop(0)
    
    def go_back(self) -> bool:
        """
        Navigate to previous page in history.
        
        Returns:
            True if navigation was successful
        """
        if not self.page_history:
            return False
        
        previous_page = self.page_history.pop()
        return self.switch_to_page(previous_page, add_to_history=False)
    
    def _update_button_styles(self):
        """Update navigation button styles based on current state."""
        for page_id, button in self.navigation_buttons.items():
            item = self.navigation_items[page_id]
            
            if not item.enabled:
                button.configure(style="NavigationDisabled.TButton")
                button.configure(state="disabled")
            elif page_id == self.current_page:
                button.configure(style="NavigationActive.TButton")
                button.configure(state="normal")
            else:
                button.configure(style="Navigation.TButton")
                button.configure(state="normal")
    
    def set_page_enabled(self, page_id: str, enabled: bool):
        """
        Enable or disable a navigation page.
        
        Args:
            page_id: Page ID
            enabled: Whether page should be enabled
        """
        if page_id in self.navigation_items:
            self.navigation_items[page_id].enabled = enabled
            self._update_button_styles()
            
            # Switch away from disabled page
            if not enabled and self.current_page == page_id:
                available_pages = [pid for pid in self.navigation_items.keys() 
                                 if self.navigation_items[pid].enabled]
                if available_pages:
                    self.switch_to_page(available_pages[0])
    
    def set_page_visible(self, page_id: str, visible: bool):
        """
        Show or hide a navigation page.
        
        Args:
            page_id: Page ID
            visible: Whether page should be visible
        """
        if page_id in self.navigation_items:
            item = self.navigation_items[page_id]
            item.visible = visible
            
            if visible and page_id not in self.navigation_buttons:
                # Create button if it doesn't exist
                self._create_navigation_button(item)
            elif not visible and page_id in self.navigation_buttons:
                # Remove button if it exists
                self.navigation_buttons[page_id].destroy()
                del self.navigation_buttons[page_id]
                
                # Switch away from hidden page
                if self.current_page == page_id:
                    available_pages = [pid for pid in self.navigation_items.keys() 
                                     if self.navigation_items[pid].visible and 
                                        self.navigation_items[pid].enabled]
                    if available_pages:
                        self.switch_to_page(available_pages[0])
    
    def get_current_page(self) -> Optional[str]:
        """
        Get the current active page.
        
        Returns:
            Current page ID or None
        """
        return self.current_page
    
    def get_navigation_history(self) -> List[str]:
        """
        Get navigation history.
        
        Returns:
            List of page IDs in history
        """
        return self.page_history.copy()
    
    def get_available_pages(self) -> List[str]:
        """
        Get list of available (enabled and visible) pages.
        
        Returns:
            List of available page IDs
        """
        return [
            page_id for page_id, item in self.navigation_items.items()
            if item.enabled and item.visible
        ]
    
    def refresh_current_page(self):
        """Refresh the current page content."""
        if self.on_page_change and self.current_page:
            self.on_page_change(self.current_page)
    
    def update_page_title(self, page_id: str, new_title: str):
        """
        Update the display title of a page.
        
        Args:
            page_id: Page ID
            new_title: New display title
        """
        if page_id in self.navigation_items:
            self.navigation_items[page_id].display_name = new_title
            
            if page_id in self.navigation_buttons:
                self.navigation_buttons[page_id].configure(text=new_title)
    
    def get_page_info(self, page_id: str) -> Optional[NavigationItem]:
        """
        Get information about a navigation page.
        
        Args:
            page_id: Page ID
            
        Returns:
            NavigationItem or None if not found
        """
        return self.navigation_items.get(page_id)
    
    def configure_responsive_layout(self, window_width: int):
        """
        Configure responsive layout based on window width.
        
        Args:
            window_width: Current window width
        """
        # Adjust button padding and font size based on window width
        if window_width < 800:
            # Compact layout for small windows
            self.style.configure(
                "Navigation.TButton",
                padding=(8, 6),
                font=("Segoe UI", 9)
            )
            self.style.configure(
                "NavigationActive.TButton",
                padding=(8, 6),
                font=("Segoe UI", 9, "bold")
            )
        elif window_width < 1200:
            # Medium layout
            self.style.configure(
                "Navigation.TButton",
                padding=(10, 7),
                font=("Segoe UI", 10)
            )
            self.style.configure(
                "NavigationActive.TButton",
                padding=(10, 7),
                font=("Segoe UI", 10, "bold")
            )
        else:
            # Full layout for large windows
            self.style.configure(
                "Navigation.TButton",
                padding=(12, 8),
                font=("Segoe UI", 10)
            )
            self.style.configure(
                "NavigationActive.TButton",
                padding=(12, 8),
                font=("Segoe UI", 10, "bold")
            )