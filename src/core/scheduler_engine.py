"""
Scheduler execution engine for Windows Scheduler GUI.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from queue import Queue, Empty
from enum import Enum

from src.models.task import Task, TaskStatus
from src.models.execution import ExecutionResult, ExecutionLog
from src.core.interfaces import ISchedulerEngine, ITaskManager, IWindowsController
from src.core.task_manager import get_task_manager
from src.core.config_manager import get_config_manager
from src.core.log_manager import get_log_manager
from src.storage.log_storage import get_log_storage
from src.utils.constants import DEFAULT_SCHEDULE_CHECK_FREQUENCY


class SchedulerState(Enum):
    """Scheduler engine states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSED = "paused"


class TaskExecutionRequest:
    """Request for task execution."""
    
    def __init__(self, task: Task, execution_time: datetime, is_retry: bool = False):
        self.task = task
        self.execution_time = execution_time
        self.is_retry = is_retry
        self.created_at = datetime.now()


class SchedulerEngine(ISchedulerEngine):
    """
    Multi-threaded scheduler engine for task execution.
    
    Manages task scheduling, execution queue, and system monitoring.
    """
    
    def __init__(self, 
                 task_manager: Optional[ITaskManager] = None,
                 windows_controller: Optional[IWindowsController] = None):
        """
        Initialize scheduler engine.
        
        Args:
            task_manager: Task manager instance
            windows_controller: Windows controller instance
        """
        self.task_manager = task_manager or get_task_manager()
        self.windows_controller = windows_controller
        self.config_manager = get_config_manager()
        self.log_manager = get_log_manager()
        self.log_storage = get_log_storage()
        
        # Scheduler state
        self._state = SchedulerState.STOPPED
        self._state_lock = threading.RLock()
        
        # Threading components
        self._scheduler_thread: Optional[threading.Thread] = None
        self._executor_threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Task execution queue
        self._execution_queue: Queue[TaskExecutionRequest] = Queue()
        self._max_concurrent_tasks = 5
        
        # Monitoring and statistics
        self._last_check_time: Optional[datetime] = None
        self._execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'last_execution_time': None,
            'next_execution_time': None
        }
        
        # Event callbacks
        self._task_executed_callbacks: List[Callable[[Task, ExecutionResult], None]] = []
        self._state_changed_callbacks: List[Callable[[SchedulerState], None]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration settings."""
        try:
            config = self.config_manager.get_config()
            self._check_frequency = config.schedule_check_frequency
            self._max_retries = config.max_retry_attempts
            
            # Subscribe to config changes
            self.config_manager.add_observer(self)
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self._check_frequency = DEFAULT_SCHEDULE_CHECK_FREQUENCY
            self._max_retries = 3
    
    def on_config_changed(self, setting_key: str, old_value: Any, new_value: Any) -> None:
        """Handle configuration changes."""
        if setting_key == "schedule_check_frequency":
            self._check_frequency = new_value
            self.logger.info(f"Updated check frequency to {new_value} seconds")
        elif setting_key == "max_retry_attempts":
            self._max_retries = new_value
            self.logger.info(f"Updated max retries to {new_value}")
    
    @property
    def state(self) -> SchedulerState:
        """Get current scheduler state."""
        with self._state_lock:
            return self._state
    
    def _set_state(self, new_state: SchedulerState) -> None:
        """Set scheduler state and notify observers."""
        with self._state_lock:
            if self._state != new_state:
                old_state = self._state
                self._state = new_state
                self.logger.info(f"Scheduler state changed: {old_state.value} -> {new_state.value}")
                
                # Notify callbacks
                for callback in self._state_changed_callbacks:
                    try:
                        callback(new_state)
                    except Exception as e:
                        self.logger.error(f"Error in state change callback: {e}")
    
    def start(self) -> bool:
        """
        Start the scheduler engine.
        
        Returns:
            True if started successfully
        """
        with self._state_lock:
            if self._state in [SchedulerState.RUNNING, SchedulerState.STARTING]:
                self.logger.warning("Scheduler is already running or starting")
                return False
            
            try:
                self._set_state(SchedulerState.STARTING)
                
                # Reset stop event
                self._stop_event.clear()
                self._pause_event.clear()
                
                # Start scheduler thread
                self._scheduler_thread = threading.Thread(
                    target=self._scheduler_loop,
                    name="SchedulerEngine-Main",
                    daemon=True
                )
                self._scheduler_thread.start()
                
                # Start executor threads
                self._start_executor_threads()
                
                self._set_state(SchedulerState.RUNNING)
                self.logger.info("Scheduler engine started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting scheduler: {e}")
                self._set_state(SchedulerState.STOPPED)
                return False
    
    def stop(self) -> bool:
        """
        Stop the scheduler engine.
        
        Returns:
            True if stopped successfully
        """
        with self._state_lock:
            if self._state == SchedulerState.STOPPED:
                self.logger.warning("Scheduler is already stopped")
                return True
            
            try:
                self._set_state(SchedulerState.STOPPING)
                
                # Signal threads to stop
                self._stop_event.set()
                
                # Wait for scheduler thread
                if self._scheduler_thread and self._scheduler_thread.is_alive():
                    self._scheduler_thread.join(timeout=5.0)
                    if self._scheduler_thread.is_alive():
                        self.logger.warning("Scheduler thread did not stop gracefully")
                
                # Wait for executor threads
                self._stop_executor_threads()
                
                # Clear execution queue
                while not self._execution_queue.empty():
                    try:
                        self._execution_queue.get_nowait()
                    except Empty:
                        break
                
                self._set_state(SchedulerState.STOPPED)
                self.logger.info("Scheduler engine stopped successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping scheduler: {e}")
                return False
    
    def pause(self) -> bool:
        """
        Pause the scheduler engine.
        
        Returns:
            True if paused successfully
        """
        with self._state_lock:
            if self._state != SchedulerState.RUNNING:
                self.logger.warning("Scheduler is not running")
                return False
            
            try:
                self._pause_event.set()
                self._set_state(SchedulerState.PAUSED)
                self.logger.info("Scheduler engine paused")
                return True
                
            except Exception as e:
                self.logger.error(f"Error pausing scheduler: {e}")
                return False
    
    def resume(self) -> bool:
        """
        Resume the scheduler engine.
        
        Returns:
            True if resumed successfully
        """
        with self._state_lock:
            if self._state != SchedulerState.PAUSED:
                self.logger.warning("Scheduler is not paused")
                return False
            
            try:
                self._pause_event.clear()
                self._set_state(SchedulerState.RUNNING)
                self.logger.info("Scheduler engine resumed")
                return True
                
            except Exception as e:
                self.logger.error(f"Error resuming scheduler: {e}")
                return False
    
    def schedule_task(self, task: Task) -> bool:
        """
        Schedule a task for execution.
        
        Args:
            task: Task to schedule
            
        Returns:
            True if scheduled successfully
        """
        try:
            if not task.validate():
                self.logger.error(f"Invalid task: {task.id}")
                return False
            
            # Update next execution time
            task.update_next_execution()
            
            # Save task
            success = self.task_manager.update_task(
                task.id,
                status=TaskStatus.PENDING,
                next_execution=task.next_execution
            )
            
            if success:
                self.logger.info(f"Task scheduled: {task.name} (next: {task.next_execution})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error scheduling task {task.id}: {e}")
            return False
    
    def execute_task(self, task: Task) -> ExecutionResult:
        """
        Execute a task immediately.
        
        Args:
            task: Task to execute
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Executing task: {task.name}")
            
            # Validate task
            if not task.validate():
                return ExecutionResult.failure_result(
                    "validate_task",
                    task.target_app,
                    "Task validation failed"
                )
            
            # Check if Windows controller is available
            if not self.windows_controller:
                return ExecutionResult.failure_result(
                    "check_controller",
                    task.target_app,
                    "Windows controller not available"
                )
            
            # Execute based on action type
            result = self._execute_action(task)
            
            # Update execution statistics
            self._update_execution_stats(result)
            
            # Log execution
            duration = datetime.now() - start_time
            self._log_execution(task, result, duration)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing task {task.id}: {e}")
            duration = datetime.now() - start_time
            
            result = ExecutionResult.failure_result(
                "execute_task",
                task.target_app,
                f"Execution error: {str(e)}"
            )
            
            self._log_execution(task, result, duration)
            return result
    
    def _execute_action(self, task: Task) -> ExecutionResult:
        """Execute the specific action for a task."""
        from src.models.action import ActionType
        
        action_type = task.action_type
        params = task.action_params
        target = task.target_app
        
        try:
            if action_type == ActionType.LAUNCH_APP:
                return self.windows_controller.launch_app(target)
            
            elif action_type == ActionType.CLOSE_APP:
                return self.windows_controller.close_app(target)
            
            elif action_type == ActionType.RESIZE_WINDOW:
                width = params.get('width', 800)
                height = params.get('height', 600)
                return self.windows_controller.resize_window(target, width, height)
            
            elif action_type == ActionType.MOVE_WINDOW:
                x = params.get('x', 100)
                y = params.get('y', 100)
                return self.windows_controller.move_window(target, x, y)
            
            elif action_type == ActionType.MINIMIZE_WINDOW:
                return self.windows_controller.minimize_window(target)
            
            elif action_type == ActionType.MAXIMIZE_WINDOW:
                return self.windows_controller.maximize_window(target)
            
            elif action_type == ActionType.FOCUS_WINDOW:
                return self.windows_controller.focus_window(target)
            
            elif action_type == ActionType.CLICK_ELEMENT:
                x = params.get('x', 0)
                y = params.get('y', 0)
                return self.windows_controller.click_element(target, x, y)
            
            elif action_type == ActionType.TYPE_TEXT:
                text = params.get('text', '')
                x = params.get('x', 0)
                y = params.get('y', 0)
                return self.windows_controller.type_text(target, text, x, y)
            
            elif action_type == ActionType.SEND_KEYS:
                keys = params.get('keys', [])
                return self.windows_controller.send_keys(keys)
            
            elif action_type == ActionType.EXECUTE_POWERSHELL:
                command = params.get('command', '')
                return self.windows_controller.execute_powershell_command(command)
            
            else:
                return ExecutionResult.failure_result(
                    "unknown_action",
                    target,
                    f"Unknown action type: {action_type}"
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                action_type.value,
                target,
                f"Action execution failed: {str(e)}"
            )
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop that checks for due tasks."""
        self.logger.info("Scheduler loop started")
        
        while not self._stop_event.is_set():
            try:
                # Check if paused
                if self._pause_event.is_set():
                    time.sleep(1)
                    continue
                
                # Check for due tasks
                self._check_due_tasks()
                
                # Update last check time
                self._last_check_time = datetime.now()
                
                # Sleep for check frequency
                self._stop_event.wait(self._check_frequency)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(1)
        
        self.logger.info("Scheduler loop stopped")
    
    def _check_due_tasks(self) -> None:
        """Check for tasks that are due for execution."""
        try:
            current_time = datetime.now()
            due_tasks = self.task_manager.get_due_tasks(current_time)
            
            if due_tasks:
                self.logger.info(f"Found {len(due_tasks)} due tasks")
                
                # Update next execution time
                next_execution = None
                for task in due_tasks:
                    if task.next_execution and (not next_execution or task.next_execution < next_execution):
                        next_execution = task.next_execution
                
                self._execution_stats['next_execution_time'] = next_execution
            
            # Queue tasks for execution
            for task in due_tasks:
                if task.status == TaskStatus.PENDING:
                    request = TaskExecutionRequest(task, current_time)
                    self._execution_queue.put(request)
                    
                    # Update task status
                    self.task_manager.update_task_status(task.id, TaskStatus.RUNNING)
                    
                    self.logger.debug(f"Queued task for execution: {task.name}")
            
        except Exception as e:
            self.logger.error(f"Error checking due tasks: {e}")
    
    def _start_executor_threads(self) -> None:
        """Start task executor threads."""
        self._executor_threads = []
        
        for i in range(self._max_concurrent_tasks):
            thread = threading.Thread(
                target=self._executor_loop,
                name=f"SchedulerEngine-Executor-{i}",
                daemon=True
            )
            thread.start()
            self._executor_threads.append(thread)
        
        self.logger.info(f"Started {len(self._executor_threads)} executor threads")
    
    def _stop_executor_threads(self) -> None:
        """Stop task executor threads."""
        # Wait for threads to finish
        for thread in self._executor_threads:
            if thread.is_alive():
                thread.join(timeout=3.0)
                if thread.is_alive():
                    self.logger.warning(f"Executor thread {thread.name} did not stop gracefully")
        
        self._executor_threads.clear()
        self.logger.info("Stopped executor threads")
    
    def _executor_loop(self) -> None:
        """Executor thread loop that processes task execution requests."""
        thread_name = threading.current_thread().name
        self.logger.debug(f"Executor loop started: {thread_name}")
        
        while not self._stop_event.is_set():
            try:
                # Get execution request with timeout
                try:
                    request = self._execution_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Execute the task
                self._process_execution_request(request)
                
                # Mark queue task as done
                self._execution_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in executor loop {thread_name}: {e}")
        
        self.logger.debug(f"Executor loop stopped: {thread_name}")
    
    def _process_execution_request(self, request: TaskExecutionRequest) -> None:
        """Process a task execution request."""
        task = request.task
        
        try:
            # Execute the task
            result = self.execute_task(task)
            
            # Handle execution result
            if result.success:
                # Mark task as completed
                task.mark_executed(request.execution_time)
                self.task_manager.update_task(
                    task.id,
                    status=TaskStatus.COMPLETED,
                    last_executed=task.last_executed,
                    next_execution=task.next_execution
                )
                
                self.logger.info(f"Task executed successfully: {task.name}")
                
            else:
                # Handle failure
                self._handle_task_failure(task, result, request.is_retry)
            
            # Notify callbacks
            for callback in self._task_executed_callbacks:
                try:
                    callback(task, result)
                except Exception as e:
                    self.logger.error(f"Error in task executed callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing execution request for task {task.id}: {e}")
            
            # Create failure result
            result = ExecutionResult.failure_result(
                "process_request",
                task.target_app,
                f"Processing error: {str(e)}"
            )
            
            self._handle_task_failure(task, result, request.is_retry)
    
    def _handle_task_failure(self, task: Task, result: ExecutionResult, is_retry: bool = False) -> None:
        """Handle task execution failure."""
        if not is_retry and task.can_retry():
            # Increment retry count and reschedule
            task.increment_retry()
            
            # Schedule retry after a delay
            retry_delay = timedelta(minutes=5 * task.retry_count)  # Exponential backoff
            retry_time = datetime.now() + retry_delay
            
            retry_request = TaskExecutionRequest(task, retry_time, is_retry=True)
            
            # Add to queue after delay (simplified - in real implementation might use a delayed queue)
            threading.Timer(retry_delay.total_seconds(), lambda: self._execution_queue.put(retry_request)).start()
            
            self.logger.warning(f"Task failed, scheduling retry {task.retry_count}/{task.max_retries}: {task.name}")
            
            # Update task status
            self.task_manager.update_task(
                task.id,
                status=TaskStatus.PENDING,
                retry_count=task.retry_count
            )
            
        else:
            # Mark task as failed
            self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
            
            # Update next execution time for recurring tasks
            if task.schedule.is_recurring():
                task.update_next_execution()
                self.task_manager.update_task(
                    task.id,
                    status=TaskStatus.PENDING,
                    next_execution=task.next_execution
                )
            
            self.logger.error(f"Task failed permanently: {task.name} - {result.message}")
    
    def _log_execution(self, task: Task, result: ExecutionResult, duration: timedelta) -> None:
        """Log task execution."""
        try:
            # Use log manager for centralized logging
            self.log_manager.log_execution(task, result, duration)
            
        except Exception as e:
            self.logger.error(f"Error logging execution: {e}")
    
    def _update_execution_stats(self, result: ExecutionResult) -> None:
        """Update execution statistics."""
        self._execution_stats['total_executions'] += 1
        self._execution_stats['last_execution_time'] = result.timestamp
        
        if result.success:
            self._execution_stats['successful_executions'] += 1
        else:
            self._execution_stats['failed_executions'] += 1
    
    def is_running(self) -> bool:
        """
        Check if scheduler is running.
        
        Returns:
            True if scheduler is running
        """
        return self._state == SchedulerState.RUNNING
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scheduler execution statistics.
        
        Returns:
            Dictionary containing statistics
        """
        stats = self._execution_stats.copy()
        
        # Add calculated fields
        total = stats['total_executions']
        if total > 0:
            stats['success_rate'] = (stats['successful_executions'] / total) * 100
            stats['failure_rate'] = (stats['failed_executions'] / total) * 100
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        # Add current state
        stats['state'] = self._state.value
        stats['last_check_time'] = self._last_check_time.isoformat() if self._last_check_time else None
        
        # Add queue information
        stats['queued_tasks'] = self._execution_queue.qsize()
        stats['active_threads'] = len([t for t in self._executor_threads if t.is_alive()])
        
        return stats
    
    def get_next_execution_time(self) -> Optional[datetime]:
        """
        Get the next scheduled execution time.
        
        Returns:
            Next execution time or None
        """
        try:
            tasks = self.task_manager.get_all_tasks()
            next_time = None
            
            for task in tasks:
                if task.status == TaskStatus.PENDING and task.next_execution:
                    if not next_time or task.next_execution < next_time:
                        next_time = task.next_execution
            
            return next_time
            
        except Exception as e:
            self.logger.error(f"Error getting next execution time: {e}")
            return None
    
    def add_task_executed_callback(self, callback: Callable[[Task, ExecutionResult], None]) -> None:
        """Add callback for task execution events."""
        self._task_executed_callbacks.append(callback)
    
    def remove_task_executed_callback(self, callback: Callable[[Task, ExecutionResult], None]) -> None:
        """Remove callback for task execution events."""
        if callback in self._task_executed_callbacks:
            self._task_executed_callbacks.remove(callback)
    
    def add_state_changed_callback(self, callback: Callable[[SchedulerState], None]) -> None:
        """Add callback for state change events."""
        self._state_changed_callbacks.append(callback)
    
    def remove_state_changed_callback(self, callback: Callable[[SchedulerState], None]) -> None:
        """Remove callback for state change events."""
        if callback in self._state_changed_callbacks:
            self._state_changed_callbacks.remove(callback)
    
    def force_check(self) -> None:
        """Force an immediate check for due tasks."""
        if self._state == SchedulerState.RUNNING:
            threading.Thread(target=self._check_due_tasks, daemon=True).start()
    
    def get_queue_size(self) -> int:
        """Get the current execution queue size."""
        return self._execution_queue.qsize()
    
    def clear_queue(self) -> int:
        """
        Clear the execution queue.
        
        Returns:
            Number of tasks removed from queue
        """
        count = 0
        while not self._execution_queue.empty():
            try:
                self._execution_queue.get_nowait()
                count += 1
            except Empty:
                break
        
        self.logger.info(f"Cleared {count} tasks from execution queue")
        return count


# Global scheduler engine instance
_scheduler_engine: Optional[SchedulerEngine] = None


def get_scheduler_engine() -> SchedulerEngine:
    """
    Get the global scheduler engine instance.
    
    Returns:
        SchedulerEngine instance
    """
    global _scheduler_engine
    if _scheduler_engine is None:
        _scheduler_engine = SchedulerEngine()
    return _scheduler_engine


def initialize_scheduler_engine(task_manager: Optional[ITaskManager] = None,
                              windows_controller: Optional[IWindowsController] = None) -> SchedulerEngine:
    """
    Initialize the global scheduler engine.
    
    Args:
        task_manager: Optional custom task manager
        windows_controller: Optional custom windows controller
        
    Returns:
        SchedulerEngine instance
    """
    global _scheduler_engine
    _scheduler_engine = SchedulerEngine(task_manager, windows_controller)
    return _scheduler_engine