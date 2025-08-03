"""
System statistics and monitoring models.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


@dataclass
class ActivityItem:
    """Individual activity item for recent activity display."""
    timestamp: datetime
    description: str
    status: str  # "success", "failure", "warning", "info"
    details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'status': self.status,
            'details': self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityItem':
        """Create instance from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            description=data['description'],
            status=data['status'],
            details=data.get('details')
        )


@dataclass
class SystemStatus:
    """Current system status information."""
    scheduler_running: bool
    windows_mcp_connected: bool
    logging_enabled: bool
    next_task_name: Optional[str] = None
    next_task_time: Optional[datetime] = None
    active_tasks_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'scheduler_running': self.scheduler_running,
            'windows_mcp_connected': self.windows_mcp_connected,
            'logging_enabled': self.logging_enabled,
            'next_task_name': self.next_task_name,
            'next_task_time': self.next_task_time.isoformat() if self.next_task_time else None,
            'active_tasks_count': self.active_tasks_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemStatus':
        """Create instance from dictionary."""
        return cls(
            scheduler_running=data['scheduler_running'],
            windows_mcp_connected=data['windows_mcp_connected'],
            logging_enabled=data['logging_enabled'],
            next_task_name=data.get('next_task_name'),
            next_task_time=datetime.fromisoformat(data['next_task_time']) if data.get('next_task_time') else None,
            active_tasks_count=data.get('active_tasks_count', 0)
        )
    
    def get_next_task_description(self) -> str:
        """Get formatted description of next task."""
        if not self.next_task_name or not self.next_task_time:
            return "無排程任務"
            
        now = datetime.now()
        time_diff = self.next_task_time - now
        
        if time_diff.total_seconds() < 0:
            return f"{self.next_task_name} - 已逾期"
        elif time_diff.total_seconds() < 60:
            return f"{self.next_task_name} - {int(time_diff.total_seconds())}秒後"
        elif time_diff.total_seconds() < 3600:
            minutes = int(time_diff.total_seconds() / 60)
            return f"{self.next_task_name} - {minutes}分鐘後"
        else:
            hours = int(time_diff.total_seconds() / 3600)
            minutes = int((time_diff.total_seconds() % 3600) / 60)
            return f"{self.next_task_name} - {hours}小時{minutes}分鐘後"


@dataclass
class SystemStatistics:
    """Overall system statistics."""
    active_tasks: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    recent_activities: List[ActivityItem]
    system_status: SystemStatus
    uptime: timedelta
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'active_tasks': self.active_tasks,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': self.success_rate,
            'recent_activities': [activity.to_dict() for activity in self.recent_activities],
            'system_status': self.system_status.to_dict(),
            'uptime': self.uptime.total_seconds(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemStatistics':
        """Create instance from dictionary."""
        return cls(
            active_tasks=data['active_tasks'],
            total_executions=data['total_executions'],
            successful_executions=data['successful_executions'],
            failed_executions=data['failed_executions'],
            success_rate=data['success_rate'],
            recent_activities=[ActivityItem.from_dict(activity) for activity in data['recent_activities']],
            system_status=SystemStatus.from_dict(data['system_status']),
            uptime=timedelta(seconds=data['uptime']),
            last_updated=datetime.fromisoformat(data['last_updated'])
        )
    
    def get_formatted_uptime(self) -> str:
        """Get formatted uptime string."""
        total_seconds = int(self.uptime.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        
        if days > 0:
            return f"{days}天{hours}小時{minutes}分鐘"
        elif hours > 0:
            return f"{hours}小時{minutes}分鐘"
        else:
            return f"{minutes}分鐘"
    
    def add_activity(self, description: str, status: str, details: Optional[str] = None) -> None:
        """
        Add a new activity item.
        
        Args:
            description: Activity description
            status: Activity status ("success", "failure", "warning", "info")
            details: Optional additional details
        """
        activity = ActivityItem(
            timestamp=datetime.now(),
            description=description,
            status=status,
            details=details
        )
        
        self.recent_activities.insert(0, activity)
        
        # Keep only the most recent 20 activities
        if len(self.recent_activities) > 20:
            self.recent_activities = self.recent_activities[:20]
        
        self.last_updated = datetime.now()
    
    def update_execution_stats(self, success: bool) -> None:
        """
        Update execution statistics.
        
        Args:
            success: Whether the execution was successful
        """
        self.total_executions += 1
        
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        # Recalculate success rate
        if self.total_executions > 0:
            self.success_rate = (self.successful_executions / self.total_executions) * 100
        else:
            self.success_rate = 0.0
        
        self.last_updated = datetime.now()
    
    @classmethod
    def create_empty(cls) -> 'SystemStatistics':
        """Create empty system statistics."""
        return cls(
            active_tasks=0,
            total_executions=0,
            successful_executions=0,
            failed_executions=0,
            success_rate=0.0,
            recent_activities=[],
            system_status=SystemStatus(
                scheduler_running=False,
                windows_mcp_connected=False,
                logging_enabled=True
            ),
            uptime=timedelta(),
            last_updated=datetime.now()
        )