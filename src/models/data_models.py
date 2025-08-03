"""
Data models for the Windows Scheduler GUI application.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .enums import (
    TaskStatus,
    ScheduleType,
    ActionType,
    ConditionType,
    ExecutionStatus,
)


@dataclass
class ExecutionResult:
    """Result of a task execution."""

    success: bool
    message: str
    timestamp: datetime
    operation: str
    target: str
    status: ExecutionStatus
    details: Optional[Dict[str, Any]] = None
    duration: Optional[timedelta] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "target": self.target,
            "status": self.status.value,
            "details": self.details,
            "duration": self.duration.total_seconds() if self.duration else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        """Create from dictionary."""
        return cls(
            success=data["success"],
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            operation=data["operation"],
            target=data["target"],
            status=ExecutionStatus(data["status"]),
            details=data.get("details"),
            duration=(
                timedelta(seconds=data["duration"]) if data.get("duration") else None
            ),
        )


@dataclass
class ConditionalTrigger:
    """Conditional trigger for task execution."""

    condition_type: ConditionType
    condition_value: str
    enabled: bool = True

    def evaluate(self, current_context: Dict[str, Any]) -> bool:
        """Evaluate the condition against current context."""
        # This will be implemented in the business logic layer
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "condition_type": self.condition_type.value,
            "condition_value": self.condition_value,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionalTrigger":
        """Create from dictionary."""
        return cls(
            condition_type=ConditionType(data["condition_type"]),
            condition_value=data["condition_value"],
            enabled=data.get("enabled", True),
        )


@dataclass
class Schedule:
    """Schedule configuration for task execution."""

    schedule_type: ScheduleType
    start_time: datetime
    end_time: Optional[datetime] = None
    interval: Optional[timedelta] = None
    days_of_week: Optional[List[int]] = None  # 0-6, Monday-Sunday
    repeat_enabled: bool = False
    conditional_trigger: Optional[ConditionalTrigger] = None

    def get_next_execution(self, from_time: datetime) -> Optional[datetime]:
        """Calculate next execution time."""
        # This will be implemented in the business logic layer
        return None

    def should_execute(self, current_context: Dict[str, Any]) -> bool:
        """Check if task should execute based on conditions."""
        if self.conditional_trigger and self.conditional_trigger.enabled:
            return self.conditional_trigger.evaluate(current_context)
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schedule_type": self.schedule_type.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "interval": self.interval.total_seconds() if self.interval else None,
            "days_of_week": self.days_of_week,
            "repeat_enabled": self.repeat_enabled,
            "conditional_trigger": (
                self.conditional_trigger.to_dict() if self.conditional_trigger else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schedule":
        """Create from dictionary."""
        return cls(
            schedule_type=ScheduleType(data["schedule_type"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=(
                datetime.fromisoformat(data["end_time"])
                if data.get("end_time")
                else None
            ),
            interval=(
                timedelta(seconds=data["interval"]) if data.get("interval") else None
            ),
            days_of_week=data.get("days_of_week"),
            repeat_enabled=data.get("repeat_enabled", False),
            conditional_trigger=(
                ConditionalTrigger.from_dict(data["conditional_trigger"])
                if data.get("conditional_trigger")
                else None
            ),
        )


@dataclass
class Task:
    """Task definition for scheduled execution."""

    id: str
    name: str
    target_app: str
    action_type: ActionType
    action_params: Dict[str, Any]
    schedule: Schedule
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

    def is_due(self) -> bool:
        """Check if task is due for execution."""
        if not self.next_execution:
            return False
        return datetime.now() >= self.next_execution

    def update_next_execution(self) -> None:
        """Update next execution time based on schedule."""
        self.next_execution = self.schedule.get_next_execution(datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "target_app": self.target_app,
            "action_type": self.action_type.value,
            "action_params": self.action_params,
            "schedule": self.schedule.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_executed": (
                self.last_executed.isoformat() if self.last_executed else None
            ),
            "next_execution": (
                self.next_execution.isoformat() if self.next_execution else None
            ),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            target_app=data["target_app"],
            action_type=ActionType(data["action_type"]),
            action_params=data["action_params"],
            schedule=Schedule.from_dict(data["schedule"]),
            status=TaskStatus(data.get("status", TaskStatus.PENDING.value)),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_executed=(
                datetime.fromisoformat(data["last_executed"])
                if data.get("last_executed")
                else None
            ),
            next_execution=(
                datetime.fromisoformat(data["next_execution"])
                if data.get("next_execution")
                else None
            ),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )


@dataclass
class ExecutionLog:
    """Log entry for task execution."""

    id: str
    schedule_name: str
    execution_time: datetime
    result: ExecutionResult
    duration: timedelta
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "schedule_name": self.schedule_name,
            "execution_time": self.execution_time.isoformat(),
            "result": self.result.to_dict(),
            "duration": self.duration.total_seconds(),
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionLog":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            schedule_name=data["schedule_name"],
            execution_time=datetime.fromisoformat(data["execution_time"]),
            result=ExecutionResult.from_dict(data["result"]),
            duration=timedelta(seconds=data["duration"]),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class AppConfig:
    """Application configuration."""

    schedule_check_frequency: int = 1  # seconds
    notifications_enabled: bool = True
    log_recording_enabled: bool = True
    log_retention_days: int = 30
    max_retry_attempts: int = 3
    ui_theme: str = "default"
    language: str = "zh-TW"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schedule_check_frequency": self.schedule_check_frequency,
            "notifications_enabled": self.notifications_enabled,
            "log_recording_enabled": self.log_recording_enabled,
            "log_retention_days": self.log_retention_days,
            "max_retry_attempts": self.max_retry_attempts,
            "ui_theme": self.ui_theme,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Create from dictionary."""
        return cls(
            schedule_check_frequency=data.get("schedule_check_frequency", 1),
            notifications_enabled=data.get("notifications_enabled", True),
            log_recording_enabled=data.get("log_recording_enabled", True),
            log_retention_days=data.get("log_retention_days", 30),
            max_retry_attempts=data.get("max_retry_attempts", 3),
            ui_theme=data.get("ui_theme", "default"),
            language=data.get("language", "zh-TW"),
        )

    @classmethod
    def get_default(cls) -> "AppConfig":
        """Get default configuration."""
        return cls()


@dataclass
class App:
    """Represents a Windows application."""

    name: str
    title: str
    process_id: int
    window_handle: Optional[int] = None
    is_visible: bool = True
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "title": self.title,
            "process_id": self.process_id,
            "window_handle": self.window_handle,
            "is_visible": self.is_visible,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
