"""
Task model and related enumerations.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

from .action import ActionType
from .schedule import Schedule


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"         # 等待執行
    RUNNING = "running"         # 執行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 執行失敗
    DISABLED = "disabled"      # 已停用


@dataclass
class Task:
    """Task model representing a scheduled Windows operation."""
    id: str
    name: str
    target_app: str
    action_type: ActionType
    action_params: Dict[str, Any]
    schedule: Schedule
    status: TaskStatus
    created_at: datetime
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def is_due(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if the task is due for execution.
        
        Args:
            current_time: Current time to check against (defaults to now)
            
        Returns:
            bool: True if task is due for execution
        """
        if self.status == TaskStatus.DISABLED:
            return False
            
        if not self.next_execution:
            return False
            
        check_time = current_time or datetime.now()
        return check_time >= self.next_execution
    
    def update_next_execution(self, from_time: Optional[datetime] = None) -> None:
        """
        Update the next execution time based on the schedule.
        
        Args:
            from_time: Time to calculate from (defaults to now)
        """
        base_time = from_time or datetime.now()
        self.next_execution = self.schedule.get_next_execution(base_time)
    
    def can_retry(self) -> bool:
        """
        Check if the task can be retried after failure.
        
        Returns:
            bool: True if task can be retried
        """
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        """Increment the retry counter."""
        self.retry_count += 1
    
    def reset_retry(self) -> None:
        """Reset the retry counter."""
        self.retry_count = 0
    
    def mark_executed(self, execution_time: Optional[datetime] = None) -> None:
        """
        Mark the task as executed and update timestamps.
        
        Args:
            execution_time: Time of execution (defaults to now)
        """
        self.last_executed = execution_time or datetime.now()
        self.reset_retry()
        self.update_next_execution(self.last_executed)
    
    def validate(self) -> bool:
        """
        Validate the task configuration.
        
        Returns:
            bool: True if task is valid
        """
        # Import here to avoid circular imports
        from .action import validate_action_params
        
        # Check required fields
        if not all([self.id, self.name, self.target_app]):
            return False
            
        # Validate action parameters
        if not validate_action_params(self.action_type, self.action_params):
            return False
            
        # Check schedule validity
        if not self.schedule:
            return False
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'target_app': self.target_app,
            'action_type': self.action_type.value,
            'action_params': self.action_params,
            'schedule': self.schedule.to_dict(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task instance from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            target_app=data['target_app'],
            action_type=ActionType(data['action_type']),
            action_params=data['action_params'],
            schedule=Schedule.from_dict(data['schedule']),
            status=TaskStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_executed=datetime.fromisoformat(data['last_executed']) if data.get('last_executed') else None,
            next_execution=datetime.fromisoformat(data['next_execution']) if data.get('next_execution') else None,
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )