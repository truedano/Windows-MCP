"""
Action step and execution options models for action sequences.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Any, Optional, List
import uuid

from .action import ActionType, validate_action_params


@dataclass
class ActionStep:
    """Single action step in an action sequence."""
    
    id: str
    action_type: ActionType
    action_params: Dict[str, Any]
    delay_after: timedelta = timedelta(seconds=1)  # 執行後延遲時間
    continue_on_error: bool = True  # 失敗時是否繼續執行後續動作
    description: Optional[str] = None  # 動作描述
    
    def validate(self) -> bool:
        """Validate the action step configuration."""
        # Check required fields
        if not all([self.id, self.action_type]):
            return False
        
        # Validate action parameters
        if not validate_action_params(self.action_type, self.action_params):
            return False
        
        # Check delay is non-negative
        if self.delay_after.total_seconds() < 0:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'action_type': self.action_type.value,
            'action_params': self.action_params,
            'delay_after': self.delay_after.total_seconds(),
            'continue_on_error': self.continue_on_error,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionStep':
        """Create action step from dictionary."""
        return cls(
            id=data['id'],
            action_type=ActionType(data['action_type']),
            action_params=data['action_params'],
            delay_after=timedelta(seconds=data.get('delay_after', 1.0)),
            continue_on_error=data.get('continue_on_error', True),
            description=data.get('description')
        )
    
    @classmethod
    def create(cls, action_type: ActionType, action_params: Dict[str, Any], 
               delay_after: timedelta = timedelta(seconds=1), 
               continue_on_error: bool = True,
               description: Optional[str] = None) -> 'ActionStep':
        """Create a new action step with auto-generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            action_type=action_type,
            action_params=action_params,
            delay_after=delay_after,
            continue_on_error=continue_on_error,
            description=description
        )


@dataclass
class ExecutionOptions:
    """Execution options for action sequence."""
    
    stop_on_first_error: bool = False  # 遇到錯誤時是否停止整個序列
    default_delay_between_actions: timedelta = timedelta(seconds=1)  # 預設動作間延遲
    max_execution_time: Optional[timedelta] = None  # 最大執行時間
    retry_failed_actions: bool = False  # 是否重試失敗的動作
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'stop_on_first_error': self.stop_on_first_error,
            'default_delay_between_actions': self.default_delay_between_actions.total_seconds(),
            'max_execution_time': self.max_execution_time.total_seconds() if self.max_execution_time else None,
            'retry_failed_actions': self.retry_failed_actions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionOptions':
        """Create execution options from dictionary."""
        return cls(
            stop_on_first_error=data.get('stop_on_first_error', False),
            default_delay_between_actions=timedelta(seconds=data.get('default_delay_between_actions', 1.0)),
            max_execution_time=timedelta(seconds=data['max_execution_time']) if data.get('max_execution_time') else None,
            retry_failed_actions=data.get('retry_failed_actions', False)
        )
    
    @classmethod
    def get_default(cls) -> 'ExecutionOptions':
        """Get default execution options."""
        return cls()


def create_action_sequence(actions: List[tuple]) -> List[ActionStep]:
    """
    Helper function to create action sequence from list of tuples.
    
    Args:
        actions: List of tuples (action_type, action_params, delay_after, continue_on_error, description)
                 Only action_type and action_params are required.
    
    Returns:
        List[ActionStep]: Created action sequence
    """
    sequence = []
    
    for action_data in actions:
        if len(action_data) < 2:
            raise ValueError("Each action must have at least action_type and action_params")
        
        action_type = action_data[0]
        action_params = action_data[1]
        delay_after = action_data[2] if len(action_data) > 2 else timedelta(seconds=1)
        continue_on_error = action_data[3] if len(action_data) > 3 else True
        description = action_data[4] if len(action_data) > 4 else None
        
        step = ActionStep.create(
            action_type=action_type,
            action_params=action_params,
            delay_after=delay_after,
            continue_on_error=continue_on_error,
            description=description
        )
        sequence.append(step)
    
    return sequence