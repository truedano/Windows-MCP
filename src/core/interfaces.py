"""
Core interfaces and abstract base classes for the Windows Scheduler GUI.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ..models.data_models import Task, AppConfig, ExecutionLog, ExecutionResult, App


class IStorage(ABC):
    """Abstract interface for data storage operations."""

    @abstractmethod
    def save(self, data: Any) -> bool:
        """Save data to storage."""
        pass

    @abstractmethod
    def load(self) -> Any:
        """Load data from storage."""
        pass

    @abstractmethod
    def delete(self, identifier: str) -> bool:
        """Delete data by identifier."""
        pass

    @abstractmethod
    def exists(self, identifier: str) -> bool:
        """Check if data exists."""
        pass


class ITaskStorage(IStorage):
    """Interface for task storage operations."""

    @abstractmethod
    def save_task(self, task: "Task") -> bool:
        """Save a task to storage."""
        pass

    @abstractmethod
    def load_task(self, task_id: str) -> Optional["Task"]:
        """Load a task by ID."""
        pass

    @abstractmethod
    def load_all_tasks(self) -> List["Task"]:
        """Load all tasks."""
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        pass


class IConfigStorage(IStorage):
    """Interface for configuration storage operations."""

    @abstractmethod
    def load_config(self) -> "AppConfig":
        """Load application configuration."""
        pass

    @abstractmethod
    def save_config(self, config: "AppConfig") -> bool:
        """Save application configuration."""
        pass

    @abstractmethod
    def get_setting(self, key: str) -> Any:
        """Get a specific setting value."""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value."""
        pass


class ILogStorage(IStorage):
    """Interface for log storage operations."""

    @abstractmethod
    def save_log(self, log: "ExecutionLog") -> bool:
        """Save an execution log."""
        pass

    @abstractmethod
    def load_logs(
        self, page: int, page_size: int, filters: Dict[str, Any]
    ) -> List["ExecutionLog"]:
        """Load logs with pagination and filtering."""
        pass

    @abstractmethod
    def search_logs(self, query: str) -> List["ExecutionLog"]:
        """Search logs by query."""
        pass

    @abstractmethod
    def delete_logs(self, before_date: datetime) -> bool:
        """Delete logs before a specific date."""
        pass


class IWindowsController(ABC):
    """Interface for Windows system operations."""

    @abstractmethod
    def get_running_apps(self) -> List["App"]:
        """Get list of currently running applications."""
        pass

    @abstractmethod
    def launch_app(self, app_name: str) -> "ExecutionResult":
        """Launch an application."""
        pass

    @abstractmethod
    def close_app(self, app_name: str) -> "ExecutionResult":
        """Close an application."""
        pass

    @abstractmethod
    def resize_window(
        self, app_name: str, width: int, height: int
    ) -> "ExecutionResult":
        """Resize application window."""
        pass

    @abstractmethod
    def move_window(self, app_name: str, x: int, y: int) -> "ExecutionResult":
        """Move application window."""
        pass

    @abstractmethod
    def minimize_window(self, app_name: str) -> "ExecutionResult":
        """Minimize application window."""
        pass

    @abstractmethod
    def maximize_window(self, app_name: str) -> "ExecutionResult":
        """Maximize application window."""
        pass

    @abstractmethod
    def focus_window(self, app_name: str) -> "ExecutionResult":
        """Focus application window."""
        pass

    @abstractmethod
    def click_element(self, app_name: str, x: int, y: int) -> "ExecutionResult":
        """Click on element in application window."""
        pass

    @abstractmethod
    def type_text(self, app_name: str, text: str, x: int, y: int) -> "ExecutionResult":
        """Type text at specific location in application window."""
        pass

    @abstractmethod
    def send_keys(self, keys: List[str]) -> "ExecutionResult":
        """Send keyboard shortcuts."""
        pass

    @abstractmethod
    def execute_powershell_command(self, command: str) -> "ExecutionResult":
        """Execute custom PowerShell command."""
        pass

    @abstractmethod
    def get_app_state(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Get current state of application."""
        pass


class ITaskManager(ABC):
    """Interface for task management operations."""

    @abstractmethod
    def create_task(self, task_config: Dict[str, Any]) -> str:
        """Create a new task and return its ID."""
        pass

    @abstractmethod
    def update_task(self, task_id: str, task_config: Dict[str, Any]) -> bool:
        """Update an existing task."""
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional["Task"]:
        """Get a task by ID."""
        pass

    @abstractmethod
    def get_all_tasks(self) -> List["Task"]:
        """Get all tasks."""
        pass


class ISchedulerEngine(ABC):
    """Interface for task scheduling operations."""

    @abstractmethod
    def start(self) -> bool:
        """Start the scheduler engine."""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop the scheduler engine."""
        pass

    @abstractmethod
    def schedule_task(self, task: "Task") -> bool:
        """Schedule a task for execution."""
        pass

    @abstractmethod
    def execute_task(self, task: "Task") -> "ExecutionResult":
        """Execute a task immediately."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        pass


class IConfigObserver(ABC):
    """Interface for configuration change observers."""

    @abstractmethod
    def on_config_changed(
        self, setting_key: str, old_value: Any, new_value: Any
    ) -> None:
        """Handle configuration changes."""
        pass
