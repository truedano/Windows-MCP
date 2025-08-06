"""
Enumerations for the Windows Scheduler GUI application.
"""

from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class ScheduleType(Enum):
    """Schedule type for task execution."""

    MANUAL = "manual"
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ActionType(Enum):
    """Types of actions that can be performed on Windows applications."""

    LAUNCH_APP = "launch_app"
    CLOSE_APP = "close_app"
    RESIZE_WINDOW = "resize_window"
    MOVE_WINDOW = "move_window"
    MINIMIZE_WINDOW = "minimize_window"
    MAXIMIZE_WINDOW = "maximize_window"
    RESTORE_WINDOW = "restore_window"
    FOCUS_WINDOW = "focus_window"
    CLICK_ELEMENT = "click_element"
    TYPE_TEXT = "type_text"
    SEND_KEYS = "send_keys"
    CUSTOM_COMMAND = "custom_command"


class ConditionType(Enum):
    """Types of conditional triggers."""

    WINDOW_TITLE_CONTAINS = "window_title_contains"
    WINDOW_TITLE_EQUALS = "window_title_equals"
    WINDOW_EXISTS = "window_exists"
    PROCESS_RUNNING = "process_running"
    TIME_RANGE = "time_range"
    SYSTEM_IDLE = "system_idle"


class ExecutionStatus(Enum):
    """Execution result status."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class LogLevel(Enum):
    """Logging levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
