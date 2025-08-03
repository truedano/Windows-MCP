"""
Comprehensive tests for Task and Schedule models.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.models.task import Task, TaskStatus
from src.models.schedule import Schedule, ScheduleType, ConditionalTrigger, ConditionType
from src.models.action import ActionType


class TestTask(unittest.TestCase):
    """Test cases for Task model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.schedule = Schedule(
            schedule_type=ScheduleType.DAILY,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            repeat_enabled=True
        )
        
        self.task = Task(
            id="test_001",
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params={"app_name": "notepad"},
            schedule=self.schedule,
            status=TaskStatus.PENDING,
            created_at=datetime(2024, 1, 1, 9, 0, 0)
        )
    
    def test_task_creation(self):
        """Test task creation with all required fields."""
        self.assertEqual(self.task.id, "test_001")
        self.assertEqual(self.task.name, "Test Task")
        self.assertEqual(self.task.target_app, "notepad")
        self.assertEqual(self.task.action_type, ActionType.LAUNCH_APP)
        self.assertEqual(self.task.status, TaskStatus.PENDING)
        self.assertEqual(self.task.retry_count, 0)
        self.assertEqual(self.task.max_retries, 3)
    
    def test_is_due_with_next_execution(self):
        """Test is_due method with next_execution set."""
        # Set next execution to future
        self.task.next_execution = datetime(2024, 1, 2, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 15, 0, 0)
        self.assertFalse(self.task.is_due(current_time))
        
        # Set next execution to past
        current_time = datetime(2024, 1, 3, 10, 0, 0)
        self.assertTrue(self.task.is_due(current_time))
    
    def test_is_due_disabled_task(self):
        """Test is_due returns False for disabled tasks."""
        self.task.status = TaskStatus.DISABLED
        self.task.next_execution = datetime(2024, 1, 1, 9, 0, 0)
        current_time = datetime(2024, 1, 1, 10, 0, 0)
        self.assertFalse(self.task.is_due(current_time))
    
    def test_is_due_no_next_execution(self):
        """Test is_due returns False when next_execution is None."""
        self.task.next_execution = None
        self.assertFalse(self.task.is_due())
    
    def test_update_next_execution(self):
        """Test update_next_execution method."""
        from_time = datetime(2024, 1, 1, 11, 0, 0)
        self.task.update_next_execution(from_time)
        
        # Should be next day at 10:00 for daily schedule
        expected = datetime(2024, 1, 2, 10, 0, 0)
        self.assertEqual(self.task.next_execution, expected)
    
    def test_can_retry(self):
        """Test can_retry method."""
        self.assertTrue(self.task.can_retry())
        
        self.task.retry_count = 2
        self.assertTrue(self.task.can_retry())
        
        self.task.retry_count = 3
        self.assertFalse(self.task.can_retry())
        
        self.task.retry_count = 5
        self.assertFalse(self.task.can_retry())
    
    def test_increment_retry(self):
        """Test increment_retry method."""
        initial_count = self.task.retry_count
        self.task.increment_retry()
        self.assertEqual(self.task.retry_count, initial_count + 1)
    
    def test_reset_retry(self):
        """Test reset_retry method."""
        self.task.retry_count = 5
        self.task.reset_retry()
        self.assertEqual(self.task.retry_count, 0)
    
    def test_mark_executed(self):
        """Test mark_executed method."""
        execution_time = datetime(2024, 1, 1, 10, 30, 0)
        self.task.retry_count = 2
        
        self.task.mark_executed(execution_time)
        
        self.assertEqual(self.task.last_executed, execution_time)
        self.assertEqual(self.task.retry_count, 0)
        self.assertIsNotNone(self.task.next_execution)
    
    def test_validate_valid_task(self):
        """Test validate method with valid task."""
        self.assertTrue(self.task.validate())
    
    def test_validate_missing_id(self):
        """Test validate method with missing id."""
        self.task.id = ""
        self.assertFalse(self.task.validate())
    
    def test_validate_missing_name(self):
        """Test validate method with missing name."""
        self.task.name = ""
        self.assertFalse(self.task.validate())
    
    def test_validate_missing_target_app(self):
        """Test validate method with missing target_app."""
        self.task.target_app = ""
        self.assertFalse(self.task.validate())
    
    def test_validate_missing_schedule(self):
        """Test validate method with missing schedule."""
        self.task.schedule = None
        self.assertFalse(self.task.validate())
    
    def test_to_dict(self):
        """Test to_dict method."""
        self.task.last_executed = datetime(2024, 1, 1, 10, 0, 0)
        self.task.next_execution = datetime(2024, 1, 2, 10, 0, 0)
        
        result = self.task.to_dict()
        
        self.assertEqual(result['id'], self.task.id)
        self.assertEqual(result['name'], self.task.name)
        self.assertEqual(result['target_app'], self.task.target_app)
        self.assertEqual(result['action_type'], self.task.action_type.value)
        self.assertEqual(result['status'], self.task.status.value)
        self.assertIn('schedule', result)
        self.assertIn('created_at', result)
        self.assertIn('last_executed', result)
        self.assertIn('next_execution', result)
    
    def test_from_dict(self):
        """Test from_dict class method."""
        task_dict = {
            'id': 'test_002',
            'name': 'Test Task 2',
            'target_app': 'calculator',
            'action_type': 'close_app',
            'action_params': {'force': True},
            'schedule': {
                'schedule_type': 'once',
                'start_time': '2024-01-01T15:00:00',
                'end_time': None,
                'interval': None,
                'days_of_week': None,
                'repeat_enabled': False,
                'conditional_trigger': None
            },
            'status': 'pending',
            'created_at': '2024-01-01T14:00:00',
            'last_executed': None,
            'next_execution': None,
            'retry_count': 0,
            'max_retries': 3
        }
        
        task = Task.from_dict(task_dict)
        
        self.assertEqual(task.id, 'test_002')
        self.assertEqual(task.name, 'Test Task 2')
        self.assertEqual(task.target_app, 'calculator')
        self.assertEqual(task.action_type, ActionType.CLOSE_APP)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsInstance(task.schedule, Schedule)


class TestSchedule(unittest.TestCase):
    """Test cases for Schedule model."""
    
    def test_once_schedule_next_execution(self):
        """Test next execution calculation for ONCE schedule."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=start_time
        )
        
        # Before start time
        from_time = datetime(2024, 1, 1, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertEqual(next_exec, start_time)
        
        # After start time
        from_time = datetime(2024, 1, 1, 11, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertIsNone(next_exec)
    
    def test_daily_schedule_next_execution(self):
        """Test next execution calculation for DAILY schedule."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        schedule = Schedule(
            schedule_type=ScheduleType.DAILY,
            start_time=start_time,
            repeat_enabled=True
        )
        
        # Before start time on same day
        from_time = datetime(2024, 1, 1, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertEqual(next_exec, start_time)
        
        # After start time on same day
        from_time = datetime(2024, 1, 1, 11, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 2, 10, 0, 0)
        self.assertEqual(next_exec, expected)
        
        # Multiple days later
        from_time = datetime(2024, 1, 5, 11, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 6, 10, 0, 0)
        self.assertEqual(next_exec, expected)
    
    def test_daily_schedule_with_end_time(self):
        """Test daily schedule with end time constraint."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 3, 10, 0, 0)
        schedule = Schedule(
            schedule_type=ScheduleType.DAILY,
            start_time=start_time,
            end_time=end_time,
            repeat_enabled=True
        )
        
        # Within range
        from_time = datetime(2024, 1, 2, 11, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 3, 10, 0, 0)
        self.assertEqual(next_exec, expected)
        
        # Beyond end time
        from_time = datetime(2024, 1, 4, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertIsNone(next_exec)
    
    def test_weekly_schedule_next_execution(self):
        """Test next execution calculation for WEEKLY schedule."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)  # Monday
        schedule = Schedule(
            schedule_type=ScheduleType.WEEKLY,
            start_time=start_time,
            days_of_week=[0, 2, 4],  # Monday, Wednesday, Friday
            repeat_enabled=True
        )
        
        # From Monday before start time
        from_time = datetime(2024, 1, 1, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertEqual(next_exec, start_time)
        
        # From Monday after start time
        from_time = datetime(2024, 1, 1, 11, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 3, 10, 0, 0)  # Wednesday
        self.assertEqual(next_exec, expected)
        
        # From Tuesday
        from_time = datetime(2024, 1, 2, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 3, 10, 0, 0)  # Wednesday
        self.assertEqual(next_exec, expected)
    
    def test_weekly_schedule_no_days(self):
        """Test weekly schedule with no days specified."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        schedule = Schedule(
            schedule_type=ScheduleType.WEEKLY,
            start_time=start_time,
            days_of_week=None,
            repeat_enabled=True
        )
        
        from_time = datetime(2024, 1, 1, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertIsNone(next_exec)
    
    def test_custom_schedule_next_execution(self):
        """Test next execution calculation for CUSTOM schedule."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        interval = timedelta(hours=2)
        schedule = Schedule(
            schedule_type=ScheduleType.CUSTOM,
            start_time=start_time,
            interval=interval,
            repeat_enabled=True
        )
        
        # Before start time
        from_time = datetime(2024, 1, 1, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertEqual(next_exec, start_time)
        
        # After start time, first interval
        from_time = datetime(2024, 1, 1, 11, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 1, 12, 0, 0)
        self.assertEqual(next_exec, expected)
        
        # Multiple intervals later
        from_time = datetime(2024, 1, 1, 15, 30, 0)
        next_exec = schedule.get_next_execution(from_time)
        expected = datetime(2024, 1, 1, 16, 0, 0)
        self.assertEqual(next_exec, expected)
    
    def test_custom_schedule_no_interval(self):
        """Test custom schedule with no interval specified."""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        schedule = Schedule(
            schedule_type=ScheduleType.CUSTOM,
            start_time=start_time,
            interval=None,
            repeat_enabled=True
        )
        
        from_time = datetime(2024, 1, 1, 9, 0, 0)
        next_exec = schedule.get_next_execution(from_time)
        self.assertIsNone(next_exec)
    
    def test_should_execute_no_condition(self):
        """Test should_execute with no conditional trigger."""
        schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=datetime(2024, 1, 1, 10, 0, 0)
        )
        
        context = {'window_titles': ['Notepad']}
        self.assertTrue(schedule.should_execute(context))
    
    def test_should_execute_with_condition(self):
        """Test should_execute with conditional trigger."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="notepad",
            enabled=True
        )
        
        schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            conditional_trigger=trigger
        )
        
        # Condition met
        context = {'window_titles': ['Notepad - Untitled']}
        self.assertTrue(schedule.should_execute(context))
        
        # Condition not met
        context = {'window_titles': ['Calculator']}
        self.assertFalse(schedule.should_execute(context))
    
    def test_to_dict(self):
        """Test to_dict method."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_EXISTS,
            condition_value="chrome",
            enabled=True
        )
        
        schedule = Schedule(
            schedule_type=ScheduleType.WEEKLY,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 12, 31, 23, 59, 59),
            interval=timedelta(hours=1),
            days_of_week=[1, 3, 5],
            repeat_enabled=True,
            conditional_trigger=trigger
        )
        
        result = schedule.to_dict()
        
        self.assertEqual(result['schedule_type'], 'weekly')
        self.assertIn('start_time', result)
        self.assertIn('end_time', result)
        self.assertEqual(result['interval'], 3600.0)  # 1 hour in seconds
        self.assertEqual(result['days_of_week'], [1, 3, 5])
        self.assertTrue(result['repeat_enabled'])
        self.assertIsNotNone(result['conditional_trigger'])
    
    def test_from_dict(self):
        """Test from_dict class method."""
        schedule_dict = {
            'schedule_type': 'daily',
            'start_time': '2024-01-01T10:00:00',
            'end_time': '2024-12-31T23:59:59',
            'interval': 3600.0,
            'days_of_week': [0, 2, 4],
            'repeat_enabled': True,
            'conditional_trigger': {
                'condition_type': 'process_running',
                'condition_value': 'chrome.exe',
                'enabled': True
            }
        }
        
        schedule = Schedule.from_dict(schedule_dict)
        
        self.assertEqual(schedule.schedule_type, ScheduleType.DAILY)
        self.assertEqual(schedule.start_time, datetime(2024, 1, 1, 10, 0, 0))
        self.assertEqual(schedule.end_time, datetime(2024, 12, 31, 23, 59, 59))
        self.assertEqual(schedule.interval, timedelta(hours=1))
        self.assertEqual(schedule.days_of_week, [0, 2, 4])
        self.assertTrue(schedule.repeat_enabled)
        self.assertIsNotNone(schedule.conditional_trigger)
        self.assertEqual(schedule.conditional_trigger.condition_type, ConditionType.PROCESS_RUNNING)


class TestConditionalTrigger(unittest.TestCase):
    """Test cases for ConditionalTrigger model."""
    
    def test_window_title_contains(self):
        """Test WINDOW_TITLE_CONTAINS condition."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="notepad",
            enabled=True
        )
        
        # Case insensitive match
        context = {'window_titles': ['Notepad - Untitled', 'Chrome']}
        self.assertTrue(trigger.evaluate(context))
        
        # Partial match
        context = {'window_titles': ['My Notepad Document']}
        self.assertTrue(trigger.evaluate(context))
        
        # No match
        context = {'window_titles': ['Calculator', 'Chrome']}
        self.assertFalse(trigger.evaluate(context))
        
        # Empty list
        context = {'window_titles': []}
        self.assertFalse(trigger.evaluate(context))
    
    def test_window_title_equals(self):
        """Test WINDOW_TITLE_EQUALS condition."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_EQUALS,
            condition_value="notepad",
            enabled=True
        )
        
        # Exact match (case insensitive)
        context = {'window_titles': ['Notepad', 'Chrome']}
        self.assertTrue(trigger.evaluate(context))
        
        # Partial match should fail
        context = {'window_titles': ['Notepad - Untitled']}
        self.assertFalse(trigger.evaluate(context))
        
        # No match
        context = {'window_titles': ['Calculator']}
        self.assertFalse(trigger.evaluate(context))
    
    def test_window_exists(self):
        """Test WINDOW_EXISTS condition."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_EXISTS,
            condition_value="chrome",
            enabled=True
        )
        
        # App exists
        context = {'running_apps': ['chrome', 'notepad', 'calculator']}
        self.assertTrue(trigger.evaluate(context))
        
        # App doesn't exist
        context = {'running_apps': ['notepad', 'calculator']}
        self.assertFalse(trigger.evaluate(context))
        
        # Case insensitive
        context = {'running_apps': ['Chrome']}
        self.assertTrue(trigger.evaluate(context))
    
    def test_process_running(self):
        """Test PROCESS_RUNNING condition."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.PROCESS_RUNNING,
            condition_value="chrome.exe",
            enabled=True
        )
        
        # Process running
        context = {'running_processes': ['chrome.exe', 'notepad.exe']}
        self.assertTrue(trigger.evaluate(context))
        
        # Process not running
        context = {'running_processes': ['notepad.exe', 'calc.exe']}
        self.assertFalse(trigger.evaluate(context))
        
        # Case insensitive
        context = {'running_processes': ['Chrome.exe']}
        self.assertTrue(trigger.evaluate(context))
    
    def test_time_range(self):
        """Test TIME_RANGE condition."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.TIME_RANGE,
            condition_value="09:00-17:00",
            enabled=True
        )
        
        # Within range
        context = {'current_time': datetime(2024, 1, 1, 12, 0, 0)}
        self.assertTrue(trigger.evaluate(context))
        
        # Before range
        context = {'current_time': datetime(2024, 1, 1, 8, 0, 0)}
        self.assertFalse(trigger.evaluate(context))
        
        # After range
        context = {'current_time': datetime(2024, 1, 1, 18, 0, 0)}
        self.assertFalse(trigger.evaluate(context))
        
        # At start boundary
        context = {'current_time': datetime(2024, 1, 1, 9, 0, 0)}
        self.assertTrue(trigger.evaluate(context))
        
        # At end boundary
        context = {'current_time': datetime(2024, 1, 1, 17, 0, 0)}
        self.assertTrue(trigger.evaluate(context))
    
    def test_time_range_crossing_midnight(self):
        """Test TIME_RANGE condition crossing midnight."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.TIME_RANGE,
            condition_value="22:00-06:00",
            enabled=True
        )
        
        # Late night (within range)
        context = {'current_time': datetime(2024, 1, 1, 23, 0, 0)}
        self.assertTrue(trigger.evaluate(context))
        
        # Early morning (within range)
        context = {'current_time': datetime(2024, 1, 1, 5, 0, 0)}
        self.assertTrue(trigger.evaluate(context))
        
        # Daytime (outside range)
        context = {'current_time': datetime(2024, 1, 1, 12, 0, 0)}
        self.assertFalse(trigger.evaluate(context))
    
    def test_time_range_invalid_format(self):
        """Test TIME_RANGE condition with invalid format."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.TIME_RANGE,
            condition_value="invalid-format",
            enabled=True
        )
        
        context = {'current_time': datetime(2024, 1, 1, 12, 0, 0)}
        self.assertFalse(trigger.evaluate(context))
    
    def test_system_idle(self):
        """Test SYSTEM_IDLE condition."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.SYSTEM_IDLE,
            condition_value="30",  # 30 minutes
            enabled=True
        )
        
        # System idle long enough
        context = {'idle_time_minutes': 45}
        self.assertTrue(trigger.evaluate(context))
        
        # System not idle long enough
        context = {'idle_time_minutes': 15}
        self.assertFalse(trigger.evaluate(context))
        
        # Exact boundary
        context = {'idle_time_minutes': 30}
        self.assertTrue(trigger.evaluate(context))
    
    def test_system_idle_invalid_value(self):
        """Test SYSTEM_IDLE condition with invalid value."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.SYSTEM_IDLE,
            condition_value="not-a-number",
            enabled=True
        )
        
        context = {'idle_time_minutes': 45}
        self.assertFalse(trigger.evaluate(context))
    
    def test_disabled_trigger(self):
        """Test that disabled triggers always return True."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,
            condition_value="nonexistent",
            enabled=False
        )
        
        context = {'window_titles': ['Calculator']}
        self.assertTrue(trigger.evaluate(context))
    
    def test_unknown_condition_type(self):
        """Test behavior with unknown condition type."""
        # This test simulates what would happen if a new condition type
        # was added but not implemented in evaluate method
        trigger = ConditionalTrigger(
            condition_type=ConditionType.WINDOW_TITLE_CONTAINS,  # Valid type
            condition_value="test",
            enabled=True
        )
        
        # Manually change to simulate unknown type
        trigger.condition_type = "unknown_type"
        
        context = {'window_titles': ['test']}
        # Should return False for unknown condition types
        self.assertFalse(trigger.evaluate(context))
    
    def test_to_dict(self):
        """Test to_dict method."""
        trigger = ConditionalTrigger(
            condition_type=ConditionType.PROCESS_RUNNING,
            condition_value="chrome.exe",
            enabled=False
        )
        
        result = trigger.to_dict()
        
        self.assertEqual(result['condition_type'], 'process_running')
        self.assertEqual(result['condition_value'], 'chrome.exe')
        self.assertFalse(result['enabled'])
    
    def test_from_dict(self):
        """Test from_dict class method."""
        trigger_dict = {
            'condition_type': 'time_range',
            'condition_value': '09:00-17:00',
            'enabled': True
        }
        
        trigger = ConditionalTrigger.from_dict(trigger_dict)
        
        self.assertEqual(trigger.condition_type, ConditionType.TIME_RANGE)
        self.assertEqual(trigger.condition_value, '09:00-17:00')
        self.assertTrue(trigger.enabled)
    
    def test_from_dict_default_enabled(self):
        """Test from_dict with default enabled value."""
        trigger_dict = {
            'condition_type': 'window_exists',
            'condition_value': 'notepad'
            # enabled not specified, should default to True
        }
        
        trigger = ConditionalTrigger.from_dict(trigger_dict)
        
        self.assertTrue(trigger.enabled)


if __name__ == '__main__':
    unittest.main()