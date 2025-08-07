"""
Task model and related enumerations.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List

from .action import ActionType
from .action_step import ActionStep, ExecutionOptions
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
    """Task model representing a scheduled Windows operation with action sequence."""
    id: str
    name: str
    target_app: str
    action_sequence: List[ActionStep]  # 動作序列，取代單一動作
    schedule: Schedule
    status: TaskStatus
    execution_options: ExecutionOptions  # 執行選項
    created_at: datetime
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    
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
        # Check required fields
        if not all([self.id, self.name, self.target_app]):
            return False
        
        # Validate action sequence
        if not self.action_sequence or len(self.action_sequence) == 0:
            return False
        
        # Validate each action step
        for step in self.action_sequence:
            if not step.validate():
                return False
        
        # Check schedule validity
        if not self.schedule:
            return False
        
        # Check execution options
        if not self.execution_options:
            return False
            
        return True
    
    def validate_action_sequence(self) -> bool:
        """
        Validate the action sequence specifically.
        
        Returns:
            bool: True if action sequence is valid
        """
        if not self.action_sequence or len(self.action_sequence) == 0:
            return False
        
        for step in self.action_sequence:
            if not step.validate():
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'target_app': self.target_app,
            'action_sequence': [step.to_dict() for step in self.action_sequence],
            'schedule': self.schedule.to_dict(),
            'status': self.status.value,
            'execution_options': self.execution_options.to_dict(),
            'created_at': self.created_at.isoformat(),
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'last_error': self.last_error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task instance from dictionary."""
        # Import ActionStep at the beginning to avoid scope issues
        from .action_step import ActionStep
        
        # Backward compatibility for renamed ActionType
        if data.get('action_type') == 'click_element':
            data['action_type'] = 'click_abs'
        
        # Handle backward compatibility for old single-action format
        if 'action_type' in data and 'action_params' in data:
            # Convert old format to new action sequence format
            action_sequence = [ActionStep.create(
                action_type=ActionType(data['action_type']),
                action_params=data['action_params']
            )]
            execution_options = ExecutionOptions.get_default()
        else:
            # New format with action sequence
            # Backward compatibility for action steps
            for step_data in data.get('action_sequence', []):
                if step_data.get('action_type') == 'click_element':
                    step_data['action_type'] = 'click_abs'
            
            action_sequence = [ActionStep.from_dict(step_data) for step_data in data['action_sequence']]
            execution_options = ExecutionOptions.from_dict(data.get('execution_options', {}))
        
        return cls(
            id=data['id'],
            name=data['name'],
            target_app=data['target_app'],
            action_sequence=action_sequence,
            schedule=Schedule.from_dict(data['schedule']),
            status=TaskStatus(data['status']),
            execution_options=execution_options,
            created_at=datetime.fromisoformat(data['created_at']),
            last_executed=datetime.fromisoformat(data['last_executed']) if data.get('last_executed') else None,
            next_execution=datetime.fromisoformat(data['next_execution']) if data.get('next_execution') else None,
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            last_error=data.get('last_error')
        )