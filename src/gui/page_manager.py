"""
Page management system for the Windows Scheduler GUI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Type, Any
from abc import ABC, abstractmethod

from src.gui.navigation import PageInterface


class BasePage(PageInterface):
    """Base class for all application pages."""
    
    def __init__(self, parent: tk.Widget, page_id: str, display_name: str):
        """
        Initialize base page.
        
        Args:
            parent: Parent widget
            page_id: Unique page identifier
            display_name: Display name for navigation
        """
        self.parent = parent
        self.page_id = page_id
        self.display_name = display_name
        self.frame: Optional[ttk.Frame] = None
        self.is_initialized = False
        self.is_active = False
        
        # Create page frame
        self._create_frame()
    
    def _create_frame(self):
        """Create the main page frame."""
        self.frame = ttk.Frame(self.parent)
        # Don't pack yet - will be managed by PageManager
    
    def get_page_id(self) -> str:
        """Get the unique page identifier."""
        return self.page_id
    
    def get_display_name(self) -> str:
        """Get the display name for navigation."""
        return self.display_name
    
    def get_frame(self) -> ttk.Frame:
        """Get the page frame widget."""
        if not self.frame:
            self._create_frame()
        return self.frame
    
    def on_page_enter(self) -> None:
        """Called when page becomes active."""
        self.is_active = True
        if not self.is_initialized:
            self.initialize_content()
            self.is_initialized = True
        self.refresh_content()
    
    def on_page_leave(self) -> None:
        """Called when page becomes inactive."""
        self.is_active = False
    
    @abstractmethod
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        pass
    
    @abstractmethod
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        pass
    
    def show(self):
        """Show the page frame."""
        if self.frame:
            self.frame.pack(fill=tk.BOTH, expand=True)
    
    def hide(self):
        """Hide the page frame."""
        if self.frame:
            self.frame.pack_forget()


class PageManager:
    """
    Manages application pages and their lifecycle.
    """
    
    def __init__(self, parent: tk.Widget):
        """
        Initialize page manager.
        
        Args:
            parent: Parent widget for pages
        """
        self.parent = parent
        self.pages: Dict[str, BasePage] = {}
        self.current_page: Optional[str] = None
        
        # Create container frame
        self.container = ttk.Frame(parent)
        self.container.pack(fill=tk.BOTH, expand=True)
    
    def register_page(self, page_class: Type[BasePage], *args, **kwargs) -> str:
        """
        Register a new page.
        
        Args:
            page_class: Page class to instantiate
            *args: Arguments for page constructor
            **kwargs: Keyword arguments for page constructor
            
        Returns:
            Page ID of the registered page
        """
        # Create page instance
        page = page_class(self.container, *args, **kwargs)
        page_id = page.get_page_id()
        
        # Store page
        self.pages[page_id] = page
        
        return page_id
    
    def add_page(self, page: BasePage) -> str:
        """
        Add an existing page instance.
        
        Args:
            page: Page instance to add
            
        Returns:
            Page ID of the added page
        """
        page_id = page.get_page_id()
        self.pages[page_id] = page
        return page_id
    
    def remove_page(self, page_id: str) -> bool:
        """
        Remove a page.
        
        Args:
            page_id: Page ID to remove
            
        Returns:
            True if page was removed
        """
        if page_id not in self.pages:
            return False
        
        page = self.pages[page_id]
        
        # Hide page if it's current
        if self.current_page == page_id:
            page.on_page_leave()
            page.hide()
            self.current_page = None
        
        # Destroy page frame
        if page.frame:
            page.frame.destroy()
        
        # Remove from registry
        del self.pages[page_id]
        
        return True
    
    def switch_to_page(self, page_id: str) -> bool:
        """
        Switch to the specified page.
        
        Args:
            page_id: Page ID to switch to
            
        Returns:
            True if switch was successful
        """
        if page_id not in self.pages:
            return False
        
        # Hide current page
        if self.current_page:
            current_page = self.pages[self.current_page]
            current_page.on_page_leave()
            current_page.hide()
        
        # Show new page
        new_page = self.pages[page_id]
        new_page.show()
        new_page.on_page_enter()
        
        self.current_page = page_id
        return True
    
    def get_current_page(self) -> Optional[str]:
        """
        Get the current active page ID.
        
        Returns:
            Current page ID or None
        """
        return self.current_page
    
    def get_page(self, page_id: str) -> Optional[BasePage]:
        """
        Get a page instance.
        
        Args:
            page_id: Page ID
            
        Returns:
            Page instance or None
        """
        return self.pages.get(page_id)
    
    def get_all_pages(self) -> Dict[str, BasePage]:
        """
        Get all registered pages.
        
        Returns:
            Dictionary of page ID to page instance
        """
        return self.pages.copy()
    
    def refresh_current_page(self):
        """Refresh the current page content."""
        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].refresh_content()
    
    def refresh_page(self, page_id: str):
        """
        Refresh a specific page.
        
        Args:
            page_id: Page ID to refresh
        """
        if page_id in self.pages:
            self.pages[page_id].refresh_content()
    
    def is_page_active(self, page_id: str) -> bool:
        """
        Check if a page is currently active.
        
        Args:
            page_id: Page ID to check
            
        Returns:
            True if page is active
        """
        return self.current_page == page_id
    
    def get_page_count(self) -> int:
        """
        Get the number of registered pages.
        
        Returns:
            Number of pages
        """
        return len(self.pages)