"""
Schedule and conditional trigger models.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class ScheduleType(Enum):
    """Types of schedule patterns."""
    ONCE = "once"           # 一次性執行
    DAILY = "daily"         # 每日重複
    WEEKLY = "weekly"       # 每週重複
    CUSTOM = "custom"       # 自訂間隔


class ConditionType(Enum):
    """Types of conditional triggers."""
    WINDOW_TITLE_CONTAINS = "window_title_contains"
    WINDOW_TITLE_EQUALS = "window_title_equals"
    WINDOW_EXISTS = "window_exists"
    PROCESS_RUNNING = "process_running"
    TIME_RANGE = "time_range"
    SYSTEM_IDLE = "system_idle"


@dataclass
class ConditionalTrigger:
    """Conditional trigger for task execution."""
    condition_type: ConditionType
    condition_value: str
    enabled: bool = True
    
    def evaluate(self, current_context: Dict[str, Any]) -> bool:
        """
        Evaluate the condition against the current system context.
        
        Args:
            current_context: Dictionary containing current system state
            
        Returns:
            bool: True if condition is met, False otherwise
        """
        if not self.enabled:
            return True
            
        if self.condition_type == ConditionType.WINDOW_TITLE_CONTAINS:
            return self._check_window_title_contains(current_context)
        elif self.condition_type == ConditionType.WINDOW_TITLE_EQUALS:
            return self._check_window_title_equals(current_context)
        elif self.condition_type == ConditionType.WINDOW_EXISTS:
            return self._check_window_exists(current_context)
        elif self.condition_type == ConditionType.PROCESS_RUNNING:
            return self._check_process_running(current_context)
        elif self.condition_type == ConditionType.TIME_RANGE:
            return self._check_time_range(current_context)
        elif self.condition_type == ConditionType.SYSTEM_IDLE:
            return self._check_system_idle(current_context)
        else:
            return False
    
    def _check_window_title_contains(self, context: Dict[str, Any]) -> bool:
        """Check if any window title contains the specified text."""
        window_titles = context.get('window_titles', [])
        return any(self.condition_value.lower() in title.lower() for title in window_titles)
    
    def _check_window_title_equals(self, context: Dict[str, Any]) -> bool:
        """Check if any window title exactly matches the specified text."""
        window_titles = context.get('window_titles', [])
        return self.condition_value.lower() in [title.lower() for title in window_titles]
    
    def _check_window_exists(self, context: Dict[str, Any]) -> bool:
        """Check if a window with the specified name exists."""
        running_apps = context.get('running_apps', [])
        return self.condition_value.lower() in [app.lower() for app in running_apps]
    
    def _check_process_running(self, context: Dict[str, Any]) -> bool:
        """Check if a process with the specified name is running."""
        running_processes = context.get('running_processes', [])
        return self.condition_value.lower() in [proc.lower() for proc in running_processes]
    
    def _check_time_range(self, context: Dict[str, Any]) -> bool:
        """Check if current time is within the specified range."""
        current_time = context.get('current_time', datetime.now())
        # Parse time range format: "HH:MM-HH:MM"
        try:
            start_str, end_str = self.condition_value.split('-')
            start_hour, start_min = map(int, start_str.split(':'))
            end_hour, end_min = map(int, end_str.split(':'))
            
            current_minutes = current_time.hour * 60 + current_time.minute
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            
            if start_minutes <= end_minutes:
                return start_minutes <= current_minutes <= end_minutes
            else:  # Range crosses midnight
                return current_minutes >= start_minutes or current_minutes <= end_minutes
        except (ValueError, IndexError):
            return False
    
    def _check_system_idle(self, context: Dict[str, Any]) -> bool:
        """Check if system has been idle for the specified duration."""
        idle_time = context.get('idle_time_minutes', 0)
        try:
            required_idle = int(self.condition_value)
            return idle_time >= required_idle
        except ValueError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'condition_type': self.condition_type.value,
            'condition_value': self.condition_value,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionalTrigger':
        """Create instance from dictionary."""
        return cls(
            condition_type=ConditionType(data['condition_type']),
            condition_value=data['condition_value'],
            enabled=data.get('enabled', True)
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
        """
        Calculate the next execution time based on the schedule.
        
        Args:
            from_time: The time to calculate from
            
        Returns:
            Optional[datetime]: Next execution time, or None if no more executions
        """
        if self.end_time and from_time >= self.end_time:
            return None
            
        if self.schedule_type == ScheduleType.ONCE:
            return self.start_time if from_time < self.start_time else None
        elif self.schedule_type == ScheduleType.DAILY:
            return self._get_next_daily_execution(from_time)
        elif self.schedule_type == ScheduleType.WEEKLY:
            return self._get_next_weekly_execution(from_time)
        elif self.schedule_type == ScheduleType.CUSTOM:
            return self._get_next_custom_execution(from_time)
        else:
            return None
    
    def _get_next_daily_execution(self, from_time: datetime) -> Optional[datetime]:
        """Calculate next daily execution."""
        if from_time < self.start_time:
            return self.start_time
            
        # Calculate next day at the same time
        next_execution = datetime.combine(
            from_time.date(),
            self.start_time.time()
        )
        
        if next_execution <= from_time:
            next_execution += timedelta(days=1)
            
        if self.end_time and next_execution > self.end_time:
            return None
            
        return next_execution
    
    def _get_next_weekly_execution(self, from_time: datetime) -> Optional[datetime]:
        """Calculate next weekly execution."""
        if not self.days_of_week:
            return None
            
        if from_time < self.start_time:
            return self.start_time
            
        current_weekday = from_time.weekday()
        target_time = self.start_time.time()
        
        # Find next occurrence
        for days_ahead in range(8):  # Check up to next week
            check_date = from_time.date() + timedelta(days=days_ahead)
            check_weekday = check_date.weekday()
            
            if check_weekday in self.days_of_week:
                next_execution = datetime.combine(check_date, target_time)
                
                if next_execution > from_time:
                    if self.end_time and next_execution > self.end_time:
                        return None
                    return next_execution
                    
        return None
    
    def _get_next_custom_execution(self, from_time: datetime) -> Optional[datetime]:
        """Calculate next custom interval execution."""
        if not self.interval:
            return None
            
        if from_time < self.start_time:
            return self.start_time
            
        # Calculate how many intervals have passed since start
        elapsed = from_time - self.start_time
        intervals_passed = int(elapsed.total_seconds() / self.interval.total_seconds())
        
        # Next execution is start_time + (intervals_passed + 1) * interval
        next_execution = self.start_time + (intervals_passed + 1) * self.interval
        
        if self.end_time and next_execution > self.end_time:
            return None
            
        return next_execution
    
    def should_execute(self, current_context: Dict[str, Any]) -> bool:
        """
        Check if the task should execute based on conditions.
        
        Args:
            current_context: Current system context
            
        Returns:
            bool: True if task should execute, False otherwise
        """
        if self.conditional_trigger:
            return self.conditional_trigger.evaluate(current_context)
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'schedule_type': self.schedule_type.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'interval': self.interval.total_seconds() if self.interval else None,
            'days_of_week': self.days_of_week,
            'repeat_enabled': self.repeat_enabled,
            'conditional_trigger': self.conditional_trigger.to_dict() if self.conditional_trigger else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """Create instance from dictionary."""
        return cls(
            schedule_type=ScheduleType(data['schedule_type']),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            interval=timedelta(seconds=data['interval']) if data.get('interval') else None,
            days_of_week=data.get('days_of_week'),
            repeat_enabled=data.get('repeat_enabled', False),
            conditional_trigger=ConditionalTrigger.from_dict(data['conditional_trigger']) if data.get('conditional_trigger') else None
        )