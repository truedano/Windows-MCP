"""
Unit tests for conditional trigger functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.models.schedule import ConditionalTrigger, ConditionType, Schedule, ScheduleType
from src.core.system_context_provider import SystemContextProvider, SystemContext
from src.core.scheduler_engine import SchedulerEngine
from src.models.task import Task, TaskStatus
from src.models.action import ActionType
from src.models.execution import ExecutionResult


class TestConditionalTriggerEvaluation(unittest.TestCase):
    """Test cases for conditional trigger evaluation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.current_time = datetime.now()
        
    def test_window_title_contains_evaluation(self):
        """Test WINDOW_TITLE_CONTAINS condition evaluation."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="notepad",
            enabled=True
        )
        
        # Test positive case - title contains pattern
        context = {
            'window_titles': ['Notepad - Untitled', 'Chrome Browser'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test case insensitive matching
        context = {
            'window_titles': ['NOTEPAD - Document.txt', 'Calculator'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test partial matching
        context = {
            'window_titles': ['My Notepad Editor', 'Firefox'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test negative case - no matching title
        context = {
            'window_titles': ['Calculator', 'Chrome Browser'],
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
        
        # Test empty window titles
        context = {
            'window_titles': [],
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
    
    def test_window_title_equals_evaluation(self):
        """Test WINDOW_TITLE_EQUALS condition evaluation."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_EQUALS,
            condition_value="notepad",
            enabled=True
        )
        
        # Test exact match (case insensitive)
        context = {
            'window_titles': ['Notepad', 'Chrome'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test case insensitive exact match
        context = {
            'window_titles': ['NOTEPAD', 'Calculator'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test partial match should fail
        context = {
            'window_titles': ['Notepad - Untitled', 'Chrome'],
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
        
        # Test no match
        context = {
            'window_titles': ['Calculator', 'Chrome'],
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
    
    def test_window_exists_evaluation(self):
        """Test WINDOW_EXISTS condition evaluation."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_EXISTS,
            condition_value="chrome",
            enabled=True
        )
        
        # Test app exists
        context = {
            'running_apps': ['chrome.exe', 'notepad.exe', 'calculator.exe'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test case insensitive matching
        context = {
            'running_apps': ['Chrome.exe', 'Notepad.exe'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test app doesn't exist
        context = {
            'running_apps': ['notepad.exe', 'calculator.exe'],
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
        
        # Test empty running apps
        context = {
            'running_apps': [],
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
    
    def test_process_running_evaluation(self):
        """Test PROCESS_RUNNING condition evaluation."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.PROCESS_RUNNING,
            condition_value="chrome.exe",
            enabled=True
        )
        
        # Test process is running
        context = {
            'running_processes': ['chrome.exe', 'notepad.exe', 'explorer.exe'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test case insensitive matching
        context = {
            'running_processes': ['Chrome.exe', 'Notepad.exe'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test process not running
        context = {
            'running_processes': ['notepad.exe', 'explorer.exe'],
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
    
    def test_time_range_evaluation(self):
        """Test TIME_RANGE condition evaluation."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.TIME_RANGE,
            condition_value="09:00-17:00",
            enabled=True
        )
        
        # Test time within range
        test_time = datetime.now().replace(hour=12, minute=30, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test time at start of range
        test_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test time at end of range
        test_time = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test time outside range (before)
        test_time = datetime.now().replace(hour=8, minute=30, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertFalse(trigger.evaluate(context))
        
        # Test time outside range (after)
        test_time = datetime.now().replace(hour=18, minute=30, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertFalse(trigger.evaluate(context))
    
    def test_time_range_across_midnight(self):
        """Test TIME_RANGE condition that crosses midnight."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.TIME_RANGE,
            condition_value="22:00-06:00",
            enabled=True
        )
        
        # Test time in evening part of range
        test_time = datetime.now().replace(hour=23, minute=30, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test time in morning part of range
        test_time = datetime.now().replace(hour=3, minute=30, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test time outside range
        test_time = datetime.now().replace(hour=12, minute=30, second=0, microsecond=0)
        context = {
            'current_time': test_time
        }
        self.assertFalse(trigger.evaluate(context))
    
    def test_system_idle_evaluation(self):
        """Test SYSTEM_IDLE condition evaluation."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.SYSTEM_IDLE,
            condition_value="10",  # 10 minutes
            enabled=True
        )
        
        # Test system idle for required time
        context = {
            'idle_time_minutes': 15,
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test system idle for exact required time
        context = {
            'idle_time_minutes': 10,
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
        
        # Test system not idle long enough
        context = {
            'idle_time_minutes': 5,
            'current_time': self.current_time
        }
        self.assertFalse(trigger.evaluate(context))
        
        # Test invalid idle time value
        trigger_invalid = ConditionalTrigger(
            condition_type=ConditionType.SYSTEM_IDLE,
            condition_value="invalid",
            enabled=True
        )
        context = {
            'idle_time_minutes': 15,
            'current_time': self.current_time
        }
        self.assertFalse(trigger_invalid.evaluate(context))
    
    def test_disabled_trigger(self):
        """Test that disabled triggers always return True."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="notepad",
            enabled=False
        )
        
        # Even with no matching windows, disabled trigger should return True
        context = {
            'window_titles': ['Calculator', 'Chrome'],
            'current_time': self.current_time
        }
        self.assertTrue(trigger.evaluate(context))
    
    def test_invalid_condition_type(self):
        """Test handling of invalid condition types."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="test",
            enabled=True
        )
        
        # Manually set invalid condition type
        trigger.condition_type = "invalid_type"
        
        context = {
            'window_titles': ['test'],
            'current_time': self.current_time
        }
        
        # Should return False for unknown condition types
        self.assertFalse(trigger.evaluate(context))


class TestSystemContextProvider(unittest.TestCase):
    """Test cases for SystemContextProvider."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_windows_controller = Mock()
        self.provider = SystemContextProvider(self.mock_windows_controller)
    
    @patch('src.core.system_context_provider.psutil.process_iter')
    def test_get_current_context(self, mock_process_iter):
        """Test getting current system context."""
        # Mock running applications
        mock_app1 = Mock()
        mock_app1.name = "notepad.exe"
        mock_app1.title = "Notepad - Untitled"
        
        mock_app2 = Mock()
        mock_app2.name = "chrome.exe"
        mock_app2.title = "Chrome Browser"
        
        self.mock_windows_controller.get_running_apps.return_value = [mock_app1, mock_app2]
        
        # Mock running processes
        mock_proc1 = Mock()
        mock_proc1.info = {'name': 'notepad.exe'}
        mock_proc2 = Mock()
        mock_proc2.info = {'name': 'chrome.exe'}
        mock_proc3 = Mock()
        mock_proc3.info = {'name': 'explorer.exe'}
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2, mock_proc3]
        
        # Get context
        context = self.provider.get_current_context()
        
        # Verify context content
        self.assertIsInstance(context, SystemContext)
        self.assertEqual(context.running_apps, ["notepad.exe", "chrome.exe"])
        self.assertEqual(context.window_titles, ["Notepad - Untitled", "Chrome Browser"])
        self.assertEqual(context.running_processes, ["notepad.exe", "chrome.exe", "explorer.exe"])
        self.assertIsInstance(context.current_time, datetime)
        self.assertIsInstance(context.idle_time_minutes, int)
    
    def test_context_caching(self):
        """Test that context is cached for performance."""
        # Mock applications
        mock_app = Mock()
        mock_app.name = "notepad.exe"
        mock_app.title = "Notepad"
        self.mock_windows_controller.get_running_apps.return_value = [mock_app]
        
        # Get context twice
        context1 = self.provider.get_current_context()
        context2 = self.provider.get_current_context()
        
        # Should be the same cached instance
        self.assertIs(context1, context2)
        
        # Windows controller should only be called once due to caching
        self.assertEqual(self.mock_windows_controller.get_running_apps.call_count, 1)
    
    def test_force_refresh(self):
        """Test forcing refresh of cached context."""
        # Mock applications
        mock_app = Mock()
        mock_app.name = "notepad.exe"
        mock_app.title = "Notepad"
        self.mock_windows_controller.get_running_apps.return_value = [mock_app]
        
        # Get context, then force refresh
        context1 = self.provider.get_current_context()
        context2 = self.provider.get_current_context(force_refresh=True)
        
        # Should be different instances
        self.assertIsNot(context1, context2)
        
        # Windows controller should be called twice
        self.assertEqual(self.mock_windows_controller.get_running_apps.call_count, 2)
    
    def test_fallback_on_controller_error(self):
        """Test fallback behavior when windows controller fails."""
        # Make windows controller raise exception
        self.mock_windows_controller.get_running_apps.side_effect = Exception("Controller error")
        
        with patch('src.core.system_context_provider.psutil.process_iter') as mock_process_iter:
            # Mock process information
            mock_proc = Mock()
            mock_proc.info = {'name': 'notepad.exe', 'exe': '/path/to/notepad.exe'}
            mock_process_iter.return_value = [mock_proc]
            
            # Should not raise exception and use fallback
            context = self.provider.get_current_context()
            
            self.assertIsInstance(context, SystemContext)
            self.assertEqual(context.running_apps, ['notepad.exe'])
    
    def test_utility_methods(self):
        """Test utility methods for checking specific conditions."""
        # Mock applications
        mock_app1 = Mock()
        mock_app1.name = "notepad.exe"
        mock_app1.title = "Notepad - Document"
        
        mock_app2 = Mock()
        mock_app2.name = "chrome.exe"
        mock_app2.title = "Chrome Browser"
        
        self.mock_windows_controller.get_running_apps.return_value = [mock_app1, mock_app2]
        
        with patch('src.core.system_context_provider.psutil.process_iter') as mock_process_iter:
            mock_proc = Mock()
            mock_proc.info = {'name': 'explorer.exe'}
            mock_process_iter.return_value = [mock_proc]
            
            # Test utility methods
            self.assertTrue(self.provider.is_app_running("notepad.exe"))
            self.assertTrue(self.provider.is_app_running("CHROME.EXE"))  # Case insensitive
            self.assertFalse(self.provider.is_app_running("calculator.exe"))
            
            self.assertTrue(self.provider.is_window_open("Notepad"))
            self.assertTrue(self.provider.is_window_open("chrome"))  # Case insensitive
            self.assertFalse(self.provider.is_window_open("Calculator"))
            
            self.assertTrue(self.provider.is_process_running("explorer.exe"))
            self.assertFalse(self.provider.is_process_running("nonexistent.exe"))


class TestSchedulerEngineConditionalTriggers(unittest.TestCase):
    """Test cases for conditional trigger integration in scheduler engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_task_manager = Mock()
        self.mock_windows_controller = Mock()
        self.mock_system_context_provider = Mock()
        
        self.scheduler = SchedulerEngine(
            task_manager=self.mock_task_manager,
            windows_controller=self.mock_windows_controller,
            system_context_provider=self.mock_system_context_provider
        )
        
        # Create test task with conditional trigger
        self.test_task = Task(
            id="test-task-1",
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.DAILY,
                start_time=datetime.now(),
                conditional_trigger=ConditionalTrigger(
                    condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
                    condition_value="work",
                    enabled=True
                )
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            next_execution=datetime.now()
        )
    
    def test_conditional_trigger_evaluation_in_scheduler(self):
        """Test that scheduler evaluates conditional triggers before executing tasks."""
        # Mock due tasks
        self.mock_task_manager.get_due_tasks.return_value = [self.test_task]
        
        # Mock system context that should pass the condition
        mock_context = SystemContext(
            window_titles=["Work Document - Notepad"],
            running_apps=["notepad.exe"],
            running_processes=["notepad.exe"],
            current_time=datetime.now(),
            idle_time_minutes=0,
            last_updated=datetime.now()
        )
        self.mock_system_context_provider.get_current_context.return_value = mock_context
        
        # Mock task manager methods
        self.mock_task_manager.update_task_status = Mock()
        
        # Check due tasks
        self.scheduler._check_due_tasks()
        
        # Verify system context was requested
        self.mock_system_context_provider.get_current_context.assert_called_once()
        
        # Verify task was queued for execution (condition passed)
        self.assertEqual(self.scheduler.get_queue_size(), 1)
        
        # Verify task status was updated
        self.mock_task_manager.update_task_status.assert_called_once_with(
            self.test_task.id, TaskStatus.RUNNING
        )
    
    def test_conditional_trigger_blocks_execution(self):
        """Test that failed conditional triggers prevent task execution."""
        # Mock due tasks
        self.mock_task_manager.get_due_tasks.return_value = [self.test_task]
        
        # Mock system context that should fail the condition
        mock_context = SystemContext(
            window_titles=["Personal Document - Notepad"],  # No "work" in title
            running_apps=["notepad.exe"],
            running_processes=["notepad.exe"],
            current_time=datetime.now(),
            idle_time_minutes=0,
            last_updated=datetime.now()
        )
        self.mock_system_context_provider.get_current_context.return_value = mock_context
        
        # Mock task manager methods
        self.mock_task_manager.update_task_status = Mock()
        
        # Check due tasks
        self.scheduler._check_due_tasks()
        
        # Verify system context was requested
        self.mock_system_context_provider.get_current_context.assert_called_once()
        
        # Verify task was NOT queued for execution (condition failed)
        self.assertEqual(self.scheduler.get_queue_size(), 0)
        
        # Verify task status was NOT updated to running
        self.mock_task_manager.update_task_status.assert_not_called()
    
    def test_task_without_conditional_trigger(self):
        """Test that tasks without conditional triggers execute normally."""
        # Create task without conditional trigger
        task_no_condition = Task(
            id="test-task-2",
            name="Test Task No Condition",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.DAILY,
                start_time=datetime.now(),
                conditional_trigger=None  # No conditional trigger
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            next_execution=datetime.now()
        )
        
        # Mock due tasks
        self.mock_task_manager.get_due_tasks.return_value = [task_no_condition]
        
        # Mock system context
        mock_context = SystemContext(
            window_titles=[],
            running_apps=[],
            running_processes=[],
            current_time=datetime.now(),
            idle_time_minutes=0,
            last_updated=datetime.now()
        )
        self.mock_system_context_provider.get_current_context.return_value = mock_context
        
        # Mock task manager methods
        self.mock_task_manager.update_task_status = Mock()
        
        # Check due tasks
        self.scheduler._check_due_tasks()
        
        # Verify task was queued for execution (no condition to fail)
        self.assertEqual(self.scheduler.get_queue_size(), 1)
        
        # Verify task status was updated
        self.mock_task_manager.update_task_status.assert_called_once_with(
            task_no_condition.id, TaskStatus.RUNNING
        )
    
    def test_multiple_tasks_mixed_conditions(self):
        """Test scheduler handling multiple tasks with different conditional trigger results."""
        # Create tasks with different conditions
        task_pass = Task(
            id="task-pass",
            name="Task Pass",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.DAILY,
                start_time=datetime.now(),
                conditional_trigger=ConditionalTrigger(
                    condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
                    condition_value="work",
                    enabled=True
                )
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            next_execution=datetime.now()
        )
        
        task_fail = Task(
            id="task-fail",
            name="Task Fail",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.DAILY,
                start_time=datetime.now(),
                conditional_trigger=ConditionalTrigger(
                    condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
                    condition_value="personal",
                    enabled=True
                )
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            next_execution=datetime.now()
        )
        
        task_no_condition = Task(
            id="task-no-condition",
            name="Task No Condition",
            target_app="chrome",
            action_type=ActionType.LAUNCH_APP,
            action_params={},
            schedule=Schedule(
                schedule_type=ScheduleType.DAILY,
                start_time=datetime.now(),
                conditional_trigger=None
            ),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            next_execution=datetime.now()
        )
        
        # Mock due tasks
        self.mock_task_manager.get_due_tasks.return_value = [task_pass, task_fail, task_no_condition]
        
        # Mock system context that passes first condition but fails second
        mock_context = SystemContext(
            window_titles=["Work Document - Notepad"],  # Contains "work" but not "personal"
            running_apps=["notepad.exe"],
            running_processes=["notepad.exe"],
            current_time=datetime.now(),
            idle_time_minutes=0,
            last_updated=datetime.now()
        )
        self.mock_system_context_provider.get_current_context.return_value = mock_context
        
        # Mock task manager methods
        self.mock_task_manager.update_task_status = Mock()
        
        # Check due tasks
        self.scheduler._check_due_tasks()
        
        # Verify only 2 tasks were queued (task_pass and task_no_condition)
        self.assertEqual(self.scheduler.get_queue_size(), 2)
        
        # Verify correct tasks had status updated
        expected_calls = [
            unittest.mock.call(task_pass.id, TaskStatus.RUNNING),
            unittest.mock.call(task_no_condition.id, TaskStatus.RUNNING)
        ]
        self.mock_task_manager.update_task_status.assert_has_calls(expected_calls, any_order=True)


if __name__ == '__main__':
    unittest.main()