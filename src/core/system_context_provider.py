"""
System context provider for conditional trigger evaluation.

This module provides system information needed for evaluating conditional triggers,
including window titles, running applications, processes, and system state.
"""

import time
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .interfaces import IWindowsController
from ..models.data_models import App


@dataclass
class SystemContext:
    """System context information for conditional trigger evaluation."""
    window_titles: List[str]
    running_apps: List[str]
    running_processes: List[str]
    current_time: datetime
    idle_time_minutes: int
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for trigger evaluation."""
        return {
            'window_titles': self.window_titles,
            'running_apps': self.running_apps,
            'running_processes': self.running_processes,
            'current_time': self.current_time,
            'idle_time_minutes': self.idle_time_minutes
        }


class SystemContextProvider:
    """
    Provides system context information for conditional trigger evaluation.
    
    This class gathers information about running applications, window titles,
    processes, and system state to support conditional trigger evaluation.
    """
    
    def __init__(self, windows_controller: Optional[IWindowsController] = None):
        """
        Initialize the system context provider.
        
        Args:
            windows_controller: Windows controller for application information
        """
        self.windows_controller = windows_controller
        if not self.windows_controller:
            from .windows_controller import get_windows_controller
            self.windows_controller = get_windows_controller()
        
        # Cache settings
        self._cache_duration = 2.0  # seconds
        self._last_update: Optional[datetime] = None
        self._cached_context: Optional[SystemContext] = None
        
        # System idle tracking
        self._last_input_time = time.time()
        self._idle_threshold = 60  # seconds to consider system idle
    
    def get_current_context(self, force_refresh: bool = False) -> SystemContext:
        """
        Get current system context information.
        
        Args:
            force_refresh: Force refresh of cached data
            
        Returns:
            SystemContext: Current system context
        """
        current_time = datetime.now()
        
        # Use cache if recent and not forcing refresh
        if (not force_refresh and 
            self._cached_context and 
            self._last_update and
            (current_time - self._last_update).total_seconds() < self._cache_duration):
            return self._cached_context
        
        # Gather fresh context information
        context = self._gather_context(current_time)
        
        # Update cache
        self._cached_context = context
        self._last_update = current_time
        
        return context
    
    def _gather_context(self, current_time: datetime) -> SystemContext:
        """
        Gather fresh system context information.
        
        Args:
            current_time: Current timestamp
            
        Returns:
            SystemContext: Fresh system context
        """
        # Get running applications
        running_apps = []
        window_titles = []
        
        try:
            apps = self.windows_controller.get_running_apps()
            for app in apps:
                if app.name:
                    running_apps.append(app.name)
                if app.title:
                    window_titles.append(app.title)
        except Exception:
            # Fallback to basic process enumeration
            running_apps, window_titles = self._get_basic_app_info()
        
        # Get running processes
        running_processes = self._get_running_processes()
        
        # Calculate idle time
        idle_time_minutes = self._get_idle_time_minutes()
        
        return SystemContext(
            window_titles=window_titles,
            running_apps=running_apps,
            running_processes=running_processes,
            current_time=current_time,
            idle_time_minutes=idle_time_minutes,
            last_updated=current_time
        )
    
    def _get_basic_app_info(self) -> tuple[List[str], List[str]]:
        """
        Get basic application information using psutil as fallback.
        
        Returns:
            Tuple of (running_apps, window_titles)
        """
        running_apps = []
        window_titles = []
        
        try:
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] and proc_info['exe']:
                        running_apps.append(proc_info['name'])
                        
                        # Try to get window title (simplified)
                        if hasattr(proc, 'name'):
                            window_titles.append(proc_info['name'])
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception:
            pass
        
        return running_apps, window_titles
    
    def _get_running_processes(self) -> List[str]:
        """
        Get list of running process names.
        
        Returns:
            List of process names
        """
        processes = []
        
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name']:
                        processes.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            pass
        
        return processes
    
    def _get_idle_time_minutes(self) -> int:
        """
        Get system idle time in minutes.
        
        This is a simplified implementation. In a real system, you would
        use Windows API to get actual idle time.
        
        Returns:
            Idle time in minutes
        """
        try:
            # Simplified idle detection based on CPU usage
            # In a real implementation, you would use GetLastInputInfo() from Windows API
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            if cpu_percent < 5.0:  # Low CPU usage indicates potential idle
                current_time = time.time()
                idle_seconds = current_time - self._last_input_time
                return int(idle_seconds / 60)
            else:
                # Reset idle timer on activity
                self._last_input_time = time.time()
                return 0
                
        except Exception:
            return 0
    
    def get_window_titles(self) -> List[str]:
        """
        Get current window titles.
        
        Returns:
            List of window titles
        """
        context = self.get_current_context()
        return context.window_titles
    
    def get_running_apps(self) -> List[str]:
        """
        Get current running application names.
        
        Returns:
            List of application names
        """
        context = self.get_current_context()
        return context.running_apps
    
    def get_running_processes(self) -> List[str]:
        """
        Get current running process names.
        
        Returns:
            List of process names
        """
        context = self.get_current_context()
        return context.running_processes
    
    def is_process_running(self, process_name: str) -> bool:
        """
        Check if a specific process is running.
        
        Args:
            process_name: Name of the process to check
            
        Returns:
            True if process is running
        """
        processes = self.get_running_processes()
        return process_name.lower() in [p.lower() for p in processes]
    
    def is_window_open(self, window_title_pattern: str) -> bool:
        """
        Check if a window with matching title is open.
        
        Args:
            window_title_pattern: Pattern to match in window titles
            
        Returns:
            True if matching window is found
        """
        titles = self.get_window_titles()
        return any(window_title_pattern.lower() in title.lower() for title in titles)
    
    def is_app_running(self, app_name: str) -> bool:
        """
        Check if a specific application is running.
        
        Args:
            app_name: Name of the application to check
            
        Returns:
            True if application is running
        """
        apps = self.get_running_apps()
        return app_name.lower() in [app.lower() for app in apps]
    
    def get_system_idle_time(self) -> int:
        """
        Get current system idle time in minutes.
        
        Returns:
            Idle time in minutes
        """
        context = self.get_current_context()
        return context.idle_time_minutes
    
    def clear_cache(self) -> None:
        """Clear cached context information."""
        self._cached_context = None
        self._last_update = None
    
    def set_cache_duration(self, seconds: float) -> None:
        """
        Set cache duration.
        
        Args:
            seconds: Cache duration in seconds
        """
        self._cache_duration = max(0.1, seconds)  # Minimum 0.1 seconds


# Global system context provider instance
_system_context_provider: Optional[SystemContextProvider] = None


def get_system_context_provider() -> SystemContextProvider:
    """
    Get the global system context provider instance.
    
    Returns:
        SystemContextProvider instance
    """
    global _system_context_provider
    if _system_context_provider is None:
        _system_context_provider = SystemContextProvider()
    return _system_context_provider


def initialize_system_context_provider(windows_controller: Optional[IWindowsController] = None) -> SystemContextProvider:
    """
    Initialize the global system context provider.
    
    Args:
        windows_controller: Optional custom windows controller
        
    Returns:
        SystemContextProvider instance
    """
    global _system_context_provider
    _system_context_provider = SystemContextProvider(windows_controller)
    return _system_context_provider