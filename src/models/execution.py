"""
Execution result and logging models.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid


@dataclass
class ExecutionResult:
    """Result of a task execution operation."""
    success: bool
    message: str
    timestamp: datetime
    operation: str
    target: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'success': self.success,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'target': self.target,
            'details': self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionResult':
        """Create instance from dictionary."""
        return cls(
            success=data['success'],
            message=data['message'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            operation=data['operation'],
            target=data['target'],
            details=data.get('details')
        )
    
    @classmethod
    def success_result(cls, operation: str, target: str, message: str = "Operation completed successfully") -> 'ExecutionResult':
        """Create a successful execution result."""
        return cls(
            success=True,
            message=message,
            timestamp=datetime.now(),
            operation=operation,
            target=target
        )
    
    @classmethod
    def failure_result(cls, operation: str, target: str, message: str, details: Optional[Dict[str, Any]] = None) -> 'ExecutionResult':
        """Create a failed execution result."""
        return cls(
            success=False,
            message=message,
            timestamp=datetime.now(),
            operation=operation,
            target=target,
            details=details
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
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'schedule_name': self.schedule_name,
            'execution_time': self.execution_time.isoformat(),
            'result': self.result.to_dict(),
            'duration': self.duration.total_seconds(),
            'retry_count': self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionLog':
        """Create instance from dictionary."""
        return cls(
            id=data['id'],
            schedule_name=data['schedule_name'],
            execution_time=datetime.fromisoformat(data['execution_time']),
            result=ExecutionResult.from_dict(data['result']),
            duration=timedelta(seconds=data['duration']),
            retry_count=data.get('retry_count', 0)
        )
    
    @classmethod
    def create_log(cls, schedule_name: str, result: ExecutionResult, duration: timedelta, retry_count: int = 0) -> 'ExecutionLog':
        """Create a new execution log entry."""
        return cls(
            id=str(uuid.uuid4()),
            schedule_name=schedule_name,
            execution_time=result.timestamp,
            result=result,
            duration=duration,
            retry_count=retry_count
        )


@dataclass
class ExecutionStatistics:
    """Statistics about task executions."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration: timedelta
    most_frequent_errors: List[str]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.failed_executions / self.total_executions) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'average_duration': self.average_duration.total_seconds(),
            'most_frequent_errors': self.most_frequent_errors,
            'success_rate': self.success_rate,
            'failure_rate': self.failure_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionStatistics':
        """Create instance from dictionary."""
        return cls(
            total_executions=data['total_executions'],
            successful_executions=data['successful_executions'],
            failed_executions=data['failed_executions'],
            average_duration=timedelta(seconds=data['average_duration']),
            most_frequent_errors=data['most_frequent_errors']
        )
    
    @classmethod
    def empty_stats(cls) -> 'ExecutionStatistics':
        """Create empty statistics."""
        return cls(
            total_executions=0,
            successful_executions=0,
            failed_executions=0,
            average_duration=timedelta(),
            most_frequent_errors=[]
        )