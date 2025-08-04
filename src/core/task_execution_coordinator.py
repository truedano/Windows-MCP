"""
Task Execution Coordinator - Integrates task execution flow.

This module implements task 5.6 from the specifications, connecting:
- TaskManager
- SchedulerEngine  
- LogManager
- ConfigurationManager

With proper error handling and retry mechanisms.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from src.models.task import Task, TaskStatus
from src.models.execution import ExecutionResult, ExecutionLog
from src.core.interfaces import ITaskManager, ISchedulerEngine, ILogManager, IConfigObserver
from src.core.task_manager import get_task_manager
from src.core.scheduler_engine import get_scheduler_engine
from src.core.log_manager import get_log_manager
from src.core.config_manager import get_config_manager, ConfigObserver
from src.core.windows_controller import get_windows_controller
from src.core.security_manager import get_security_manager, OperationType, require_security_validation
from src.core.error_handler import get_global_error_handler, PermissionError


@dataclass
class ExecutionContext:
    """Context information for task execution."""
    task: Task
    execution_time: datetime
    retry_count: int = 0
    is_manual: bool = False
    execution_id: str = ""
    
    def __post_init__(self):
        if not self.execution_id:
            import uuid
            self.execution_id = str(uuid.uuid4())


class TaskExecutionCoordinator(ConfigObserver):
    """
    Coordinates task execution flow between all core components.
    
    Implements the integrated task execution flow as specified in task 5.6:
    - Connects TaskManager, SchedulerEngine, LogManager and ConfigurationManager
    - Implements task execution result processing and error retry mechanism
    - Provides centralized coordination for all task operations
    """
    
    def __init__(self):
        """Initialize the task execution coordinator."""
        # Core component dependencies
        self.task_manager = get_task_manager()
        self.scheduler_engine = get_scheduler_engine()
        self.log_manager = get_log_manager()
        self.config_manager = get_config_manager()
        self.windows_controller = get_windows_controller()
        
        # Configuration settings
        self._max_retries = 3
        self._retry_delay_base = 5  # Base delay in minutes
        self._execution_timeout = 300  # 5 minutes
        self._concurrent_limit = 5
        
        # Execution tracking
        self._active_executions: Dict[str, ExecutionContext] = {}
        self._execution_lock = threading.RLock()
        self._execution_callbacks: List[Callable[[Task, ExecutionResult], None]] = []
        
        # Statistics
        self._stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'retried_executions': 0,
            'coordinator_started': datetime.now()
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self._load_configuration()
        
        # Register as configuration observer
        self.config_manager.add_observer(self)
        
        # Setup scheduler callbacks
        self._setup_scheduler_integration()
        
        self.logger.info("Task Execution Coordinator initialized")
    
    def _load_configuration(self) -> None:
        """Load configuration settings."""
        try:
            config = self.config_manager.get_config()
            self._max_retries = config.max_retry_attempts
            self._execution_timeout = getattr(config, 'execution_timeout', 300)
            self._concurrent_limit = getattr(config, 'max_concurrent_tasks', 5)
            
            self.logger.info(f"Configuration loaded - max_retries: {self._max_retries}, "
                           f"timeout: {self._execution_timeout}s, concurrent: {self._concurrent_limit}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            # Use defaults
            self._max_retries = 3
            self._execution_timeout = 300
            self._concurrent_limit = 5
    
    def on_config_changed(self, setting_key: str, old_value: Any, new_value: Any) -> None:
        """Handle configuration changes."""
        if setting_key == "max_retry_attempts":
            self._max_retries = new_value
            self.logger.info(f"Updated max retries to {new_value}")
        elif setting_key == "execution_timeout":
            self._execution_timeout = new_value
            self.logger.info(f"Updated execution timeout to {new_value}s")
        elif setting_key == "max_concurrent_tasks":
            self._concurrent_limit = new_value
            self.logger.info(f"Updated concurrent limit to {new_value}")
    
    def _setup_scheduler_integration(self) -> None:
        """Setup integration with scheduler engine."""
        try:
            # Register callback for scheduler task execution
            self.scheduler_engine.add_task_executed_callback(self._on_scheduler_task_executed)
            
            # Inject windows controller into scheduler if not already set
            if not hasattr(self.scheduler_engine, 'windows_controller') or not self.scheduler_engine.windows_controller:
                self.scheduler_engine.windows_controller = self.windows_controller
            
            self.logger.info("Scheduler integration setup completed")
            
        except Exception as e:
            self.logger.error(f"Error setting up scheduler integration: {e}")
    
    def _on_scheduler_task_executed(self, task: Task, result: ExecutionResult) -> None:
        """Handle task execution from scheduler."""
        try:
            # Process the execution result
            self._process_execution_result(task, result, is_scheduled=True)
            
        except Exception as e:
            self.logger.error(f"Error processing scheduler task execution: {e}")
    
    def execute_task_immediately(self, task_id: str, force: bool = False) -> ExecutionResult:
        """
        Execute a task immediately, bypassing the scheduler.
        
        Args:
            task_id: ID of the task to execute
            force: Whether to force execution even if task is disabled
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()
        
        try:
            # Get task
            task = self.task_manager.get_task(task_id)
            if not task:
                return ExecutionResult.failure_result(
                    "get_task",
                    "unknown",
                    f"Task not found: {task_id}"
                )
            
            # Check if task can be executed
            if not force and task.status == TaskStatus.DISABLED:
                return ExecutionResult.failure_result(
                    "check_status",
                    task.target_app,
                    "Task is disabled"
                )
            
            # Check concurrent execution limit
            if len(self._active_executions) >= self._concurrent_limit:
                return ExecutionResult.failure_result(
                    "check_concurrency",
                    task.target_app,
                    "Maximum concurrent executions reached"
                )
            
            # Create execution context
            context = ExecutionContext(
                task=task,
                execution_time=start_time,
                is_manual=True
            )
            
            # Execute the task
            result = self._execute_task_with_context(context)
            
            # Process result
            self._process_execution_result(task, result, is_scheduled=False)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in immediate task execution: {e}")
            return ExecutionResult.failure_result(
                "execute_immediate",
                task.target_app if 'task' in locals() else "unknown",
                f"Execution error: {str(e)}"
            )
    
    def _execute_task_with_context(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute a task with the given context.
        
        Args:
            context: Execution context
            
        Returns:
            ExecutionResult with execution details
        """
        task = context.task
        execution_id = context.execution_id
        
        # Track active execution
        with self._execution_lock:
            self._active_executions[execution_id] = context
        
        try:
            self.logger.info(f"Executing task: {task.name} (ID: {task.id}, Execution: {execution_id})")
            
            # Update task status
            self.task_manager.update_task_status(task.id, TaskStatus.RUNNING)
            
            # Validate task before execution
            if not self.task_manager.validate_task(task):
                return ExecutionResult.failure_result(
                    "validate_task",
                    task.target_app,
                    "Task validation failed"
                )
            
            # Execute using scheduler engine's execution logic
            result = self.scheduler_engine.execute_task(task)
            
            # Update statistics
            self._update_execution_stats(result, context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing task {task.id}: {e}")
            return ExecutionResult.failure_result(
                "execute_task",
                task.target_app,
                f"Execution error: {str(e)}"
            )
        
        finally:
            # Remove from active executions
            with self._execution_lock:
                self._active_executions.pop(execution_id, None)
    
    def _process_execution_result(self, task: Task, result: ExecutionResult, is_scheduled: bool = True) -> None:
        """
        Process task execution result and handle success/failure.
        
        Args:
            task: Executed task
            result: Execution result
            is_scheduled: Whether this was a scheduled execution
        """
        try:
            if result.success:
                self._handle_successful_execution(task, result, is_scheduled)
            else:
                self._handle_failed_execution(task, result, is_scheduled)
            
            # Notify callbacks
            for callback in self._execution_callbacks:
                try:
                    callback(task, result)
                except Exception as e:
                    self.logger.error(f"Error in execution callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing execution result: {e}")
    
    def _handle_successful_execution(self, task: Task, result: ExecutionResult, is_scheduled: bool) -> None:
        """Handle successful task execution."""
        try:
            # Mark task as executed
            self.task_manager.mark_task_executed(task.id, result.timestamp)
            
            # Reset retry count
            task.reset_retry()
            
            # Update task status based on schedule type
            if task.schedule.is_recurring():
                # For recurring tasks, set back to pending with next execution time
                self.task_manager.update_task_status(task.id, TaskStatus.PENDING)
                self.logger.info(f"Recurring task completed: {task.name}, next execution: {task.next_execution}")
            else:
                # For one-time tasks, mark as completed
                self.task_manager.update_task_status(task.id, TaskStatus.COMPLETED)
                self.logger.info(f"One-time task completed: {task.name}")
            
            # Log successful execution
            duration = datetime.now() - result.timestamp
            execution_log = ExecutionLog.create_log(task.name, result, duration, task.retry_count)
            self.log_manager.add_log(execution_log)
            
            self.logger.info(f"Task executed successfully: {task.name}")
            
        except Exception as e:
            self.logger.error(f"Error handling successful execution: {e}")
    
    def _handle_failed_execution(self, task: Task, result: ExecutionResult, is_scheduled: bool) -> None:
        """Handle failed task execution with retry logic."""
        try:
            self.logger.warning(f"Task execution failed: {task.name} - {result.message}")
            
            # Check if task can be retried
            if task.can_retry():
                # Increment retry count
                task.increment_retry()
                self.task_manager.increment_task_retry(task.id)
                
                # Calculate retry delay with exponential backoff
                retry_delay = self._calculate_retry_delay(task.retry_count)
                retry_time = datetime.now() + retry_delay
                
                # Schedule retry
                self._schedule_retry(task, retry_time)
                
                self.logger.info(f"Task retry scheduled: {task.name} "
                               f"(attempt {task.retry_count}/{task.max_retries}) "
                               f"at {retry_time}")
                
                # Update statistics
                self._stats['retried_executions'] += 1
                
            else:
                # Max retries reached, mark as failed
                self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
                
                # For recurring tasks, still schedule next execution
                if task.schedule.is_recurring():
                    task.reset_retry()
                    task.update_next_execution()
                    self.task_manager.update_task_status(task.id, TaskStatus.PENDING)
                    self.logger.info(f"Failed task rescheduled for next occurrence: {task.name}")
                
                self.logger.error(f"Task failed permanently: {task.name} - max retries exceeded")
            
            # Log failed execution
            duration = datetime.now() - result.timestamp
            execution_log = ExecutionLog.create_log(task.name, result, duration, task.retry_count)
            self.log_manager.add_log(execution_log)
            
        except Exception as e:
            self.logger.error(f"Error handling failed execution: {e}")
    
    def _calculate_retry_delay(self, retry_count: int) -> timedelta:
        """
        Calculate retry delay with exponential backoff.
        
        Args:
            retry_count: Current retry count
            
        Returns:
            Delay before retry
        """
        # Exponential backoff: base_delay * (2 ^ (retry_count - 1))
        delay_minutes = self._retry_delay_base * (2 ** (retry_count - 1))
        
        # Cap at maximum delay (e.g., 60 minutes)
        delay_minutes = min(delay_minutes, 60)
        
        return timedelta(minutes=delay_minutes)
    
    def _schedule_retry(self, task: Task, retry_time: datetime) -> None:
        """
        Schedule a task retry.
        
        Args:
            task: Task to retry
            retry_time: When to retry the task
        """
        try:
            # Update task's next execution time for retry
            task.next_execution = retry_time
            self.task_manager.update_task_status(task.id, TaskStatus.PENDING)
            
            # The scheduler will pick up the task at the retry time
            self.logger.debug(f"Retry scheduled for task {task.name} at {retry_time}")
            
        except Exception as e:
            self.logger.error(f"Error scheduling retry: {e}")
    
    def _update_execution_stats(self, result: ExecutionResult, context: ExecutionContext) -> None:
        """Update execution statistics."""
        self._stats['total_executions'] += 1
        
        if result.success:
            self._stats['successful_executions'] += 1
        else:
            self._stats['failed_executions'] += 1
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary containing execution statistics
        """
        stats = self._stats.copy()
        
        # Calculate rates
        total = stats['total_executions']
        if total > 0:
            stats['success_rate'] = (stats['successful_executions'] / total) * 100
            stats['failure_rate'] = (stats['failed_executions'] / total) * 100
            stats['retry_rate'] = (stats['retried_executions'] / total) * 100
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
            stats['retry_rate'] = 0.0
        
        # Add active execution info
        with self._execution_lock:
            stats['active_executions'] = len(self._active_executions)
            stats['active_tasks'] = [ctx.task.name for ctx in self._active_executions.values()]
        
        # Add uptime
        stats['uptime'] = datetime.now() - stats['coordinator_started']
        
        return stats
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """
        Get information about currently active executions.
        
        Returns:
            List of active execution information
        """
        with self._execution_lock:
            active_info = []
            for execution_id, context in self._active_executions.items():
                active_info.append({
                    'execution_id': execution_id,
                    'task_id': context.task.id,
                    'task_name': context.task.name,
                    'target_app': context.task.target_app,
                    'started_at': context.execution_time,
                    'duration': datetime.now() - context.execution_time,
                    'is_manual': context.is_manual,
                    'retry_count': context.retry_count
                })
            return active_info
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an active execution.
        
        Args:
            execution_id: ID of execution to cancel
            
        Returns:
            True if cancellation was successful
        """
        with self._execution_lock:
            if execution_id in self._active_executions:
                context = self._active_executions[execution_id]
                task = context.task
                
                try:
                    # Update task status
                    self.task_manager.update_task_status(task.id, TaskStatus.PENDING)
                    
                    # Remove from active executions
                    del self._active_executions[execution_id]
                    
                    self.logger.info(f"Execution cancelled: {task.name} ({execution_id})")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Error cancelling execution: {e}")
                    return False
            
            return False
    
    def add_execution_callback(self, callback: Callable[[Task, ExecutionResult], None]) -> None:
        """Add callback for task execution events."""
        self._execution_callbacks.append(callback)
    
    def remove_execution_callback(self, callback: Callable[[Task, ExecutionResult], None]) -> None:
        """Remove callback for task execution events."""
        if callback in self._execution_callbacks:
            self._execution_callbacks.remove(callback)
    
    def start_coordinator(self) -> bool:
        """
        Start the task execution coordinator.
        
        Returns:
            True if started successfully
        """
        try:
            # Ensure scheduler is running
            if not self.scheduler_engine.is_running():
                if not self.scheduler_engine.start():
                    self.logger.error("Failed to start scheduler engine")
                    return False
            
            self.logger.info("Task Execution Coordinator started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting coordinator: {e}")
            return False
    
    def stop_coordinator(self) -> bool:
        """
        Stop the task execution coordinator.
        
        Returns:
            True if stopped successfully
        """
        try:
            # Cancel all active executions
            with self._execution_lock:
                execution_ids = list(self._active_executions.keys())
                for execution_id in execution_ids:
                    self.cancel_execution(execution_id)
            
            # Remove configuration observer
            self.config_manager.remove_observer(self)
            
            self.logger.info("Task Execution Coordinator stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping coordinator: {e}")
            return False


# Global coordinator instance
_task_execution_coordinator: Optional[TaskExecutionCoordinator] = None


def get_task_execution_coordinator() -> TaskExecutionCoordinator:
    """
    Get the global task execution coordinator instance.
    
    Returns:
        TaskExecutionCoordinator instance
    """
    global _task_execution_coordinator
    if _task_execution_coordinator is None:
        _task_execution_coordinator = TaskExecutionCoordinator()
    return _task_execution_coordinator


def initialize_task_execution_coordinator() -> TaskExecutionCoordinator:
    """
    Initialize the global task execution coordinator.
    
    Returns:
        TaskExecutionCoordinator instance
    """
    global _task_execution_coordinator
    _task_execution_coordinator = TaskExecutionCoordinator()
    return _task_execution_coordinator