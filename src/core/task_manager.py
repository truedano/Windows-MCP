"""
Task Manager implementation for managing task lifecycle and operations.
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime

from .interfaces import ITaskManager
from ..models.task import Task, TaskStatus
from ..models.action import ActionType, validate_action_params
from ..models.execution import ExecutionResult
from ..models.schedule import Schedule


class TaskManager(ITaskManager):
    """
    Task manager that provides task lifecycle management.
    
    This class handles task creation, updating, deletion, and validation
    according to the design specifications.
    """
    
    def __init__(self):
        """Initialize the task manager."""
        self._tasks: Dict[str, Task] = {}
        self._task_storage = None  # Will be injected when storage layer is implemented
    
    def create_task(self, name: str, target_app: str, action_type: ActionType, 
                   action_params: Dict[str, any], schedule: "Schedule") -> str:
        """
        Create a new task.
        
        Args:
            name: Task name
            target_app: Target application name
            action_type: Type of action to perform
            action_params: Parameters for the action
            schedule: Schedule configuration
            
        Returns:
            str: Task ID of the created task
            
        Raises:
            ValueError: If task configuration is invalid
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Validate action parameters
        if not validate_action_params(action_type, action_params):
            raise ValueError(f"Invalid action parameters for {action_type.value}")
        
        # Create task instance
        task = Task(
            id=task_id,
            name=name,
            target_app=target_app,
            action_type=action_type,
            action_params=action_params,
            schedule=schedule,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Validate the complete task
        if not self.validate_task(task):
            raise ValueError("Task validation failed")
        
        # Calculate initial next execution time
        task.update_next_execution()
        
        # Store the task
        self._tasks[task_id] = task
        
        # Persist to storage if available
        if self._task_storage:
            self._task_storage.save_task(task)
        
        return task_id
    
    def update_task(self, task_id: str, name: Optional[str] = None, 
                   target_app: Optional[str] = None, action_type: Optional[ActionType] = None,
                   action_params: Optional[Dict[str, any]] = None, 
                   schedule: Optional["Schedule"] = None, status: Optional[TaskStatus] = None,
                   last_executed: Optional[datetime] = None, next_execution: Optional[datetime] = None,
                   retry_count: Optional[int] = None) -> bool:
        """
        Update an existing task.
        
        Args:
            task_id: ID of the task to update
            name: New task name (optional)
            target_app: New target application (optional)
            action_type: New action type (optional)
            action_params: New action parameters (optional)
            schedule: New schedule (optional)
            
        Returns:
            bool: True if task was updated successfully
            
        Raises:
            ValueError: If task ID not found or update parameters are invalid
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task with ID {task_id} not found")
        
        task = self._tasks[task_id]
        
        # Update fields if provided
        if name is not None:
            task.name = name
        
        if target_app is not None:
            task.target_app = target_app
        
        if action_type is not None:
            task.action_type = action_type
        
        if action_params is not None:
            # Validate new action parameters
            current_action_type = action_type if action_type is not None else task.action_type
            if not validate_action_params(current_action_type, action_params):
                raise ValueError(f"Invalid action parameters for {current_action_type.value}")
            task.action_params = action_params
        
        if schedule is not None:
            task.schedule = schedule
            # Recalculate next execution time if schedule changed
            task.update_next_execution()
        
        if status is not None:
            task.status = status
        
        if last_executed is not None:
            task.last_executed = last_executed
        
        if next_execution is not None:
            task.next_execution = next_execution
        
        if retry_count is not None:
            task.retry_count = retry_count
        
        # Validate the updated task
        if not self.validate_task(task):
            raise ValueError("Updated task validation failed")
        
        # Persist changes to storage if available
        if self._task_storage:
            self._task_storage.save_task(task)
        
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            bool: True if task was deleted successfully
            
        Raises:
            ValueError: If task ID not found
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Remove from memory
        del self._tasks[task_id]
        
        # Remove from storage if available
        if self._task_storage:
            self._task_storage.delete_task(task_id)
        
        return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Optional[Task]: Task instance or None if not found
        """
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """
        Get all tasks.
        
        Returns:
            List[Task]: List of all tasks
        """
        return list(self._tasks.values())
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        Get tasks filtered by status.
        
        Args:
            status: Task status to filter by
            
        Returns:
            List[Task]: List of tasks with the specified status
        """
        return [task for task in self._tasks.values() if task.status == status]
    
    def get_due_tasks(self, current_time: Optional[datetime] = None) -> List[Task]:
        """
        Get tasks that are due for execution.
        
        Args:
            current_time: Current time to check against (defaults to now)
            
        Returns:
            List[Task]: List of tasks due for execution
        """
        check_time = current_time or datetime.now()
        return [task for task in self._tasks.values() if task.is_due(check_time)]
    
    def validate_task(self, task: Task) -> bool:
        """
        Validate a task configuration.
        
        Args:
            task: Task to validate
            
        Returns:
            bool: True if task is valid
        """
        try:
            # Use the task's built-in validation
            return task.validate()
        except Exception:
            return False
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            status: New status
            
        Returns:
            bool: True if status was updated successfully
            
        Raises:
            ValueError: If task ID not found
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task with ID {task_id} not found")
        
        task = self._tasks[task_id]
        task.status = status
        
        # Persist changes to storage if available
        if self._task_storage:
            self._task_storage.save_task(task)
        
        return True
    
    def mark_task_executed(self, task_id: str, execution_time: Optional[datetime] = None) -> bool:
        """
        Mark a task as executed and update its next execution time.
        
        Args:
            task_id: ID of the task to mark as executed
            execution_time: Time of execution (defaults to now)
            
        Returns:
            bool: True if task was marked as executed successfully
            
        Raises:
            ValueError: If task ID not found
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task with ID {task_id} not found")
        
        task = self._tasks[task_id]
        task.mark_executed(execution_time)
        task.status = TaskStatus.COMPLETED
        
        # Persist changes to storage if available
        if self._task_storage:
            self._task_storage.save_task(task)
        
        return True
    
    def increment_task_retry(self, task_id: str) -> bool:
        """
        Increment the retry counter for a task.
        
        Args:
            task_id: ID of the task to increment retry count
            
        Returns:
            bool: True if retry count was incremented successfully
            
        Raises:
            ValueError: If task ID not found
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task with ID {task_id} not found")
        
        task = self._tasks[task_id]
        task.increment_retry()
        
        # Persist changes to storage if available
        if self._task_storage:
            self._task_storage.save_task(task)
        
        return True
    
    def can_task_retry(self, task_id: str) -> bool:
        """
        Check if a task can be retried after failure.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            bool: True if task can be retried
            
        Raises:
            ValueError: If task ID not found
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task with ID {task_id} not found")
        
        task = self._tasks[task_id]
        return task.can_retry()
    
    def get_task_count(self) -> int:
        """
        Get the total number of tasks.
        
        Returns:
            int: Total number of tasks
        """
        return len(self._tasks)
    
    def get_task_count_by_status(self, status: TaskStatus) -> int:
        """
        Get the number of tasks with a specific status.
        
        Args:
            status: Task status to count
            
        Returns:
            int: Number of tasks with the specified status
        """
        return len(self.get_tasks_by_status(status))
    
    def clear_all_tasks(self) -> bool:
        """
        Clear all tasks (for testing purposes).
        
        Returns:
            bool: True if all tasks were cleared successfully
        """
        self._tasks.clear()
        
        # Clear storage if available
        if self._task_storage:
            # This would need to be implemented in the storage layer
            pass
        
        return True
    
    def set_task_storage(self, storage):
        """
        Set the task storage instance for persistence.
        
        Args:
            storage: Task storage instance
        """
        self._task_storage = storage
        
        # Load existing tasks from storage
        if storage:
            try:
                existing_tasks = storage.load_all_tasks()
                for task in existing_tasks:
                    self._tasks[task.id] = task
            except Exception:
                # Storage might be empty or not yet initialized
                pass
    
    def export_tasks(self) -> List[Dict[str, any]]:
        """
        Export all tasks to a list of dictionaries.
        
        Returns:
            List[Dict[str, any]]: List of task dictionaries
        """
        return [task.to_dict() for task in self._tasks.values()]
    
    def import_tasks(self, task_data: List[Dict[str, any]]) -> int:
        """
        Import tasks from a list of dictionaries.
        
        Args:
            task_data: List of task dictionaries
            
        Returns:
            int: Number of tasks imported successfully
        """
        imported_count = 0
        
        for data in task_data:
            try:
                task = Task.from_dict(data)
                if self.validate_task(task):
                    self._tasks[task.id] = task
                    
                    # Persist to storage if available
                    if self._task_storage:
                        self._task_storage.save_task(task)
                    
                    imported_count += 1
            except Exception:
                # Skip invalid task data
                continue
        
        return imported_count
    
    def execute_task_immediately(self, task_id: str) -> bool:
        """
        Execute a task immediately, bypassing the scheduler.
        
        Args:
            task_id: ID of the task to execute
            
        Returns:
            bool: True if execution was successful
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            
            # Execute the task (placeholder implementation)
            # In a real implementation, this would integrate with Windows-MCP
            print(f"Executing task immediately: {task.name}")
            
            # Simulate execution
            import time
            time.sleep(0.1)  # Brief delay to simulate work
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.mark_executed()
            
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.increment_retry()
            print(f"Task execution failed: {e}")
            return False
    
    def stop_task(self, task_id: str) -> bool:
        """
        Stop a running task.
        
        Args:
            task_id: ID of the task to stop
            
        Returns:
            bool: True if task was stopped successfully
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        if task.status != TaskStatus.RUNNING:
            return False
        
        try:
            # Stop the task (placeholder implementation)
            print(f"Stopping task: {task.name}")
            
            # Update status
            task.status = TaskStatus.PENDING
            task.update_next_execution()
            
            return True
            
        except Exception as e:
            print(f"Failed to stop task: {e}")
            return False