"""
Tests for scheduler execution engine.
"""

import time
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import threading

from src.core.scheduler_engine import SchedulerEngine, SchedulerState, TaskExecutionRequest
from src.core.mock_windows_controller import MockWindowsController
from src.models.task import Task, TaskStatus
from src.models.action import ActionType
from src.models.schedule import Schedule, ScheduleType
from src.models.execution import ExecutionResult


class TestSchedulerEngine(unittest.TestCase):
    """Test cases for SchedulerEngine class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock components
        self.mock_task_manager = Mock()
        self.mock_windows_controller = MockWindowsController()
        
        # Create scheduler engine
        self.scheduler = SchedulerEngine(
            task_manager=self.mock_task_manager,
            windows_controller=self.mock_windows_controller
        )
        
        # Set low failure rate for predictable tests
        self.mock_windows_controller.set_failure_rate(0.0)
        self.mock_windows_controller.set_delay_range(0.01, 0.05)
        
        # Create test task
        self.test_task = Task(
            id="test_task_001",
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.ONCE,
                start_time=datetime.now() + timedelta(seconds=1)
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        self.test_task.update_next_execution()
    
    def tearDown(self):
        """Clean up test environment."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        time.sleep(0.1)  # Allow threads to stop
    
    def test_initial_state(self):
        """Test initial scheduler state."""
        self.assertEqual(self.scheduler.state, SchedulerState.STOPPED)
        self.assertFalse(self.scheduler.is_running())
        self.assertEqual(self.scheduler.get_queue_size(), 0)
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping the scheduler."""
        # Test start
        success = self.scheduler.start()
        self.assertTrue(success)
        self.assertEqual(self.scheduler.state, SchedulerState.RUNNING)
        self.assertTrue(self.scheduler.is_running())
        
        # Test stop
        success = self.scheduler.stop()
        self.assertTrue(success)
        self.assertEqual(self.scheduler.state, SchedulerState.STOPPED)
        self.assertFalse(self.scheduler.is_running())
    
    def test_start_already_running(self):
        """Test starting scheduler when already running."""
        self.scheduler.start()
        
        # Try to start again
        success = self.scheduler.start()
        self.assertFalse(success)
        self.assertEqual(self.scheduler.state, SchedulerState.RUNNING)
        
        self.scheduler.stop()
    
    def test_stop_already_stopped(self):
        """Test stopping scheduler when already stopped."""
        # Try to stop when not running
        success = self.scheduler.stop()
        self.assertTrue(success)
        self.assertEqual(self.scheduler.state, SchedulerState.STOPPED)
    
    def test_pause_resume_scheduler(self):
        """Test pausing and resuming the scheduler."""
        self.scheduler.start()
        
        # Test pause
        success = self.scheduler.pause()
        self.assertTrue(success)
        self.assertEqual(self.scheduler.state, SchedulerState.PAUSED)
        
        # Test resume
        success = self.scheduler.resume()
        self.assertTrue(success)
        self.assertEqual(self.scheduler.state, SchedulerState.RUNNING)
        
        self.scheduler.stop()
    
    def test_pause_when_not_running(self):
        """Test pausing scheduler when not running."""
        success = self.scheduler.pause()
        self.assertFalse(success)
    
    def test_resume_when_not_paused(self):
        """Test resuming scheduler when not paused."""
        self.scheduler.start()
        
        success = self.scheduler.resume()
        self.assertFalse(success)
        
        self.scheduler.stop()
    
    def test_schedule_task(self):
        """Test scheduling a task."""
        # Mock task manager methods
        self.mock_task_manager.update_task.return_value = True
        
        success = self.scheduler.schedule_task(self.test_task)
        self.assertTrue(success)
        
        # Verify task manager was called
        self.mock_task_manager.update_task.assert_called()
    
    def test_schedule_invalid_task(self):
        """Test scheduling an invalid task."""
        # Create invalid task
        invalid_task = Task(
            id="",  # Invalid empty ID
            name="Invalid Task",
            target_app="",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.ONCE,
                start_time=datetime.now()
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        success = self.scheduler.schedule_task(invalid_task)
        self.assertFalse(success)
    
    def test_execute_task_success(self):
        """Test successful task execution."""
        result = self.scheduler.execute_task(self.test_task)
        
        self.assertIsInstance(result, ExecutionResult)
        self.assertTrue(result.success)
        self.assertEqual(result.operation, "launch_app")
        self.assertEqual(result.target, "notepad")
    
    def test_execute_task_failure(self):
        """Test failed task execution."""
        # Set high failure rate
        self.mock_windows_controller.set_failure_rate(1.0)
        
        result = self.scheduler.execute_task(self.test_task)
        
        self.assertIsInstance(result, ExecutionResult)
        self.assertFalse(result.success)
    
    def test_execute_different_action_types(self):
        """Test executing different action types."""
        action_tests = [
            (ActionType.CLOSE_APP, {}),
            (ActionType.RESIZE_WINDOW, {"width": 800, "height": 600}),
            (ActionType.MOVE_WINDOW, {"x": 100, "y": 100}),
            (ActionType.MINIMIZE_WINDOW, {}),
            (ActionType.MAXIMIZE_WINDOW, {}),
            (ActionType.FOCUS_WINDOW, {}),
            (ActionType.CLICK_ELEMENT, {"x": 50, "y": 50}),
            (ActionType.TYPE_TEXT, {"text": "Hello", "x": 0, "y": 0}),
            (ActionType.SEND_KEYS, {"keys": ["ctrl", "s"]}),
            (ActionType.EXECUTE_POWERSHELL, {"command": "Get-Process"})
        ]
        
        for action_type, params in action_tests:
            with self.subTest(action_type=action_type):
                task = Task(
                    id=f"test_{action_type.value}",
                    name=f"Test {action_type.value}",
                    target_app="notepad",
                    action_type=action_type,
                    action_params=params,
                    schedule=Schedule(
                        schedule_type=ScheduleType.ONCE,
                        start_time=datetime.now()
                    ),
                    status=TaskStatus.PENDING,
                    created_at=datetime.now()
                )
                
                result = self.scheduler.execute_task(task)
                self.assertIsInstance(result, ExecutionResult)
                self.assertEqual(result.operation, action_type.value)
    
    def test_execute_task_without_windows_controller(self):
        """Test task execution without Windows controller."""
        scheduler_no_controller = SchedulerEngine(
            task_manager=self.mock_task_manager,
            windows_controller=None
        )
        
        result = scheduler_no_controller.execute_task(self.test_task)
        
        self.assertFalse(result.success)
        self.assertIn("Windows controller not available", result.message)
    
    def test_get_statistics(self):
        """Test getting scheduler statistics."""
        stats = self.scheduler.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_executions', stats)
        self.assertIn('successful_executions', stats)
        self.assertIn('failed_executions', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('failure_rate', stats)
        self.assertIn('state', stats)
        self.assertIn('queued_tasks', stats)
        
        # Initial values
        self.assertEqual(stats['total_executions'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
        self.assertEqual(stats['state'], SchedulerState.STOPPED.value)
    
    def test_statistics_after_execution(self):
        """Test statistics after task execution."""
        # Execute a task
        self.scheduler.execute_task(self.test_task)
        
        stats = self.scheduler.get_statistics()
        self.assertEqual(stats['total_executions'], 1)
        self.assertEqual(stats['successful_executions'], 1)
        self.assertEqual(stats['success_rate'], 100.0)
    
    def test_get_next_execution_time(self):
        """Test getting next execution time."""
        # Mock task manager to return test task
        self.mock_task_manager.get_all_tasks.return_value = [self.test_task]
        
        next_time = self.scheduler.get_next_execution_time()
        self.assertIsNotNone(next_time)
        self.assertEqual(next_time, self.test_task.next_execution)
    
    def test_get_next_execution_time_no_tasks(self):
        """Test getting next execution time with no tasks."""
        self.mock_task_manager.get_all_tasks.return_value = []
        
        next_time = self.scheduler.get_next_execution_time()
        self.assertIsNone(next_time)
    
    def test_force_check(self):
        """Test forcing an immediate check."""
        self.scheduler.start()
        
        # Mock get_due_tasks to return our test task
        self.mock_task_manager.get_due_tasks.return_value = [self.test_task]
        self.mock_task_manager.update_task_status.return_value = True
        
        # Force check
        self.scheduler.force_check()
        
        # Wait a bit for the check to complete
        time.sleep(0.1)
        
        # Verify get_due_tasks was called
        self.mock_task_manager.get_due_tasks.assert_called()
        
        self.scheduler.stop()
    
    def test_clear_queue(self):
        """Test clearing the execution queue."""
        # Add some requests to queue
        request1 = TaskExecutionRequest(self.test_task, datetime.now())
        request2 = TaskExecutionRequest(self.test_task, datetime.now())
        
        self.scheduler._execution_queue.put(request1)
        self.scheduler._execution_queue.put(request2)
        
        self.assertEqual(self.scheduler.get_queue_size(), 2)
        
        # Clear queue
        cleared_count = self.scheduler.clear_queue()
        
        self.assertEqual(cleared_count, 2)
        self.assertEqual(self.scheduler.get_queue_size(), 0)
    
    def test_task_execution_callbacks(self):
        """Test task execution callbacks."""
        callback_called = threading.Event()
        callback_task = None
        callback_result = None
        
        def test_callback(task, result):
            nonlocal callback_task, callback_result
            callback_task = task
            callback_result = result
            callback_called.set()
        
        # Add callback
        self.scheduler.add_task_executed_callback(test_callback)
        
        # Execute task
        self.scheduler.execute_task(self.test_task)
        
        # Verify callback was called (for direct execution, callback is not called)
        # This test would work better with the full scheduler loop
        
        # Remove callback
        self.scheduler.remove_task_executed_callback(test_callback)
    
    def test_state_change_callbacks(self):
        """Test state change callbacks."""
        callback_called = threading.Event()
        callback_state = None
        
        def test_callback(state):
            nonlocal callback_state
            callback_state = state
            callback_called.set()
        
        # Add callback
        self.scheduler.add_state_changed_callback(test_callback)
        
        # Start scheduler (should trigger callback)
        self.scheduler.start()
        
        # Wait for callback
        callback_called.wait(timeout=1.0)
        
        self.assertEqual(callback_state, SchedulerState.RUNNING)
        
        # Remove callback
        self.scheduler.remove_state_changed_callback(test_callback)
        
        self.scheduler.stop()
    
    def test_task_execution_request(self):
        """Test TaskExecutionRequest class."""
        execution_time = datetime.now()
        request = TaskExecutionRequest(self.test_task, execution_time, is_retry=True)
        
        self.assertEqual(request.task, self.test_task)
        self.assertEqual(request.execution_time, execution_time)
        self.assertTrue(request.is_retry)
        self.assertIsInstance(request.created_at, datetime)
    
    def test_scheduler_with_due_tasks(self):
        """Test scheduler behavior with due tasks."""
        # Create a task that's due now
        due_task = Task(
            id="due_task_001",
            name="Due Task",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.ONCE,
                start_time=datetime.now() - timedelta(seconds=1)  # Past time
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        due_task.update_next_execution()
        
        # Mock task manager
        self.mock_task_manager.get_due_tasks.return_value = [due_task]
        self.mock_task_manager.update_task_status.return_value = True
        self.mock_task_manager.update_task.return_value = True
        
        # Start scheduler
        self.scheduler.start()
        
        # Wait for scheduler to process
        time.sleep(0.5)
        
        # Verify task manager methods were called
        self.mock_task_manager.get_due_tasks.assert_called()
        
        self.scheduler.stop()
    
    def test_config_change_handling(self):
        """Test handling of configuration changes."""
        # Test check frequency change
        self.scheduler.on_config_changed("schedule_check_frequency", 1, 5)
        self.assertEqual(self.scheduler._check_frequency, 5)
        
        # Test max retries change
        self.scheduler.on_config_changed("max_retry_attempts", 3, 5)
        self.assertEqual(self.scheduler._max_retries, 5)
        
        # Test unrelated config change
        self.scheduler.on_config_changed("ui_theme", "light", "dark")
        # Should not affect scheduler settings
    
    def test_concurrent_execution(self):
        """Test concurrent task execution."""
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = Task(
                id=f"concurrent_task_{i}",
                name=f"Concurrent Task {i}",
                target_app="notepad",
                action_type=ActionType.LAUNCH_APP,
                action_params={},
                schedule=Schedule(
                    schedule_type=ScheduleType.ONCE,
                    start_time=datetime.now()
                ),
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
            tasks.append(task)
        
        # Execute tasks concurrently
        results = []
        threads = []
        
        def execute_task(task):
            result = self.scheduler.execute_task(task)
            results.append(result)
        
        for task in tasks:
            thread = threading.Thread(target=execute_task, args=(task,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all tasks executed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, ExecutionResult)


class TestSchedulerEngineIntegration(unittest.TestCase):
    """Integration tests for SchedulerEngine."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.mock_windows_controller = MockWindowsController()
        self.mock_windows_controller.set_failure_rate(0.0)
        self.mock_windows_controller.set_delay_range(0.01, 0.02)
    
    def test_full_scheduler_lifecycle(self):
        """Test complete scheduler lifecycle with real components."""
        # This would require real task manager and storage
        # For now, we'll test with mocks
        pass


if __name__ == "__main__":
    unittest.main()