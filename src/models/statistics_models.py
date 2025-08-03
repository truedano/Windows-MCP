"""
Data models for statistics and system monitoring.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any


@dataclass
class ExecutionStatistics:
    """Statistics for task execution."""

    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration: timedelta
    most_frequent_errors: List[str]

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "average_duration": self.average_duration.total_seconds(),
            "most_frequent_errors": self.most_frequent_errors,
            "success_rate": self.success_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionStatistics":
        """Create from dictionary."""
        return cls(
            total_executions=data["total_executions"],
            successful_executions=data["successful_executions"],
            failed_executions=data["failed_executions"],
            average_duration=timedelta(seconds=data["average_duration"]),
            most_frequent_errors=data["most_frequent_errors"],
        )


@dataclass
class SystemStatistics:
    """Overall system statistics."""

    active_tasks: int
    total_tasks: int
    scheduler_uptime: timedelta
    last_execution_time: datetime
    next_execution_time: datetime
    execution_stats: ExecutionStatistics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "active_tasks": self.active_tasks,
            "total_tasks": self.total_tasks,
            "scheduler_uptime": self.scheduler_uptime.total_seconds(),
            "last_execution_time": self.last_execution_time.isoformat(),
            "next_execution_time": self.next_execution_time.isoformat(),
            "execution_stats": self.execution_stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemStatistics":
        """Create from dictionary."""
        return cls(
            active_tasks=data["active_tasks"],
            total_tasks=data["total_tasks"],
            scheduler_uptime=timedelta(seconds=data["scheduler_uptime"]),
            last_execution_time=datetime.fromisoformat(data["last_execution_time"]),
            next_execution_time=datetime.fromisoformat(data["next_execution_time"]),
            execution_stats=ExecutionStatistics.from_dict(data["execution_stats"]),
        )


@dataclass
class ActivityItem:
    """Activity item for recent activity display."""

    timestamp: datetime
    task_name: str
    action: str
    result: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "task_name": self.task_name,
            "action": self.action,
            "result": self.result,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivityItem":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            task_name=data["task_name"],
            action=data["action"],
            result=data["result"],
            message=data["message"],
        )


@dataclass
class SystemStatus:
    """Current system status."""

    scheduler_running: bool
    windows_mcp_connected: bool
    logging_enabled: bool
    next_task_info: str
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scheduler_running": self.scheduler_running,
            "windows_mcp_connected": self.windows_mcp_connected,
            "logging_enabled": self.logging_enabled,
            "next_task_info": self.next_task_info,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemStatus":
        """Create from dictionary."""
        return cls(
            scheduler_running=data["scheduler_running"],
            windows_mcp_connected=data["windows_mcp_connected"],
            logging_enabled=data["logging_enabled"],
            next_task_info=data["next_task_info"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )
