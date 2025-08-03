"""
Tests for TaskManager functionality.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.core.task_manager import TaskManager
from src.models.task import Task, TaskStatus
from src.models.action import ActionType
from src.models.schedule import Schedule, ScheduleType


class TestTaskManager(unittest.TestCase):
    """Test cases for TaskManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.task_manager = TaskManager()
        
        # Create a sample schedule for testing
        self.sample_schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=datetime.now() + timedelta(hours=1),
            end_time=None,
            interval=None,
            days_of_week=None,
            conditions=None
        )
        
        # Sample action parameters
        self.sample_action_params = {
            'app_name': 'notepad'
        }
    
    def test_create_task_success(self):
        """Test successful task creation."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Verify task was created
        self.assertIsNotNone(task_id)
        self.assertEqual(len(task_id), 36)  # UUID length
        
        # Verify task exists in manager
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.target_app, "notepad")
        self.assertEqual(task.action_type, ActionType.LAUNCH_APP)
        self.assertEqual(task.status, TaskStatus.PENDING)
    
    def test_create_task_invalid_params(self):
        """Test task creation with invalid parameters."""
        # Test with invalid action parameters
        with self.assertRaises(ValueError):
            self.task_manager.create_task(
                name="Invalid Task",
                target_app="notepad",
                action_type=ActionType.LAUNCH_APP,
                action_params={},  # Missing required app_name
                schedule=self.sample_schedule
            )
    
    def test_get_task_existing(self):
        """Test getting an existing task."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.id, task_id)
    
    def test_get_task_nonexistent(self):
        """Test getting a non-existent task."""
        task = self.task_manager.get_task("nonexistent-id")
        self.assertIsNone(task)
    
    def test_get_all_tasks(self):
        """Test getting all tasks."""
        # Initially no tasks
        tasks = self.task_manager.get_all_tasks()
        self.assertEqual(len(tasks), 0)
        
        # Create some tasks
        task_id1 = self.task_manager.create_task(
            name="Task 1",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        task_id2 = self.task_manager.create_task(
            name="Task 2",
            target_app="calculator",
            action_type=ActionType.CLOSE_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule
        )
        
        # Verify all tasks are returned
        tasks = self.task_manager.get_all_tasks()
        self.assertEqual(len(tasks), 2)
        task_ids = [task.id for task in tasks]
        self.assertIn(task_id1, task_ids)
        self.assertIn(task_id2, task_ids)
    
    def test_update_task_success(self):
        """Test successful task update."""
        task_id = self.task_manager.create_task(
            name="Original Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Update task
        success = self.task_manager.update_task(
            task_id=task_id,
            name="Updated Task",
            target_app="calculator"
        )
        
        self.assertTrue(success)
        
        # Verify changes
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.name, "Updated Task")
        self.assertEqual(task.target_app, "calculator")
    
    def test_update_task_nonexistent(self):
        """Test updating a non-existent task."""
        with self.assertRaises(ValueError):
            self.task_manager.update_task(
                task_id="nonexistent-id",
                name="Updated Task"
            )
    
    def test_update_task_invalid_params(self):
        """Test updating task with invalid parameters."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Try to update with invalid action parameters
        with self.assertRaises(ValueError):
            self.task_manager.update_task(
                task_id=task_id,
                action_params={}  # Missing required parameters
            )
    
    def test_delete_task_success(self):
        """Test successful task deletion."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Verify task exists
        self.assertIsNotNone(self.task_manager.get_task(task_id))
        
        # Delete task
        success = self.task_manager.delete_task(task_id)
        self.assertTrue(success)
        
        # Verify task is deleted
        self.assertIsNone(self.task_manager.get_task(task_id))
    
    def test_delete_task_nonexistent(self):
        """Test deleting a non-existent task."""
        with self.assertRaises(ValueError):
            self.task_manager.delete_task("nonexistent-id")
    
    def test_get_tasks_by_status(self):
        """Test getting tasks filtered by status."""
        # Create tasks with different statuses
        task_id1 = self.task_manager.create_task(
            name="Pending Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        task_id2 = self.task_manager.create_task(
            name="Running Task",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule
        )
        
        # Update one task status
        self.task_manager.update_task_status(task_id2, TaskStatus.RUNNING)
        
        # Test filtering
        pending_tasks = self.task_manager.get_tasks_by_status(TaskStatus.PENDING)
        running_tasks = self.task_manager.get_tasks_by_status(TaskStatus.RUNNING)
        
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(len(running_tasks), 1)
        self.assertEqual(pending_tasks[0].id, task_id1)
        self.assertEqual(running_tasks[0].id, task_id2)
    
    def test_get_due_tasks(self):
        """Test getting tasks that are due for execution."""
        # Create a task that's due now
        due_schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=datetime.now() - timedelta(minutes=1),  # Past time
            end_time=None,
            interval=None,
            days_of_week=None,
            conditions=None
        )
        
        # Create a task that's not due yet
        future_schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=datetime.now() + timedelta(hours=1),  # Future time
            end_time=None,
            interval=None,
            days_of_week=None,
            conditions=None
        )
        
        due_task_id = self.task_manager.create_task(
            name="Due Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=due_schedule
        )
        
        future_task_id = self.task_manager.create_task(
            name="Future Task",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={'app_name': 'calculator'},
            schedule=future_schedule
        )
        
        # Get due tasks
        due_tasks = self.task_manager.get_due_tasks()
        
        # Only the due task should be returned
        self.assertEqual(len(due_tasks), 1)
        self.assertEqual(due_tasks[0].id, due_task_id)
    
    def test_update_task_status(self):
        """Test updating task status."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Update status
        success = self.task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        self.assertTrue(success)
        
        # Verify status change
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.RUNNING)
    
    def test_mark_task_executed(self):
        """Test marking task as executed."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        execution_time = datetime.now()
        success = self.task_manager.mark_task_executed(task_id, execution_time)
        self.assertTrue(success)
        
        # Verify task was marked as executed
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.last_executed, execution_time)
        self.assertEqual(task.retry_count, 0)  # Should be reset
    
    def test_increment_task_retry(self):
        """Test incrementing task retry count."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Initial retry count should be 0
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.retry_count, 0)
        
        # Increment retry count
        success = self.task_manager.increment_task_retry(task_id)
        self.assertTrue(success)
        
        # Verify retry count increased
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.retry_count, 1)
    
    def test_can_task_retry(self):
        """Test checking if task can be retried."""
        task_id = self.task_manager.create_task(
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Initially should be able to retry
        self.assertTrue(self.task_manager.can_task_retry(task_id))
        
        # Increment retry count to maximum
        task = self.task_manager.get_task(task_id)
        for _ in range(task.max_retries):
            self.task_manager.increment_task_retry(task_id)
        
        # Should no longer be able to retry
        self.assertFalse(self.task_manager.can_task_retry(task_id))
    
    def test_get_task_count(self):
        """Test getting total task count."""
        # Initially no tasks
        self.assertEqual(self.task_manager.get_task_count(), 0)
        
        # Create some tasks
        self.task_manager.create_task(
            name="Task 1",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        self.task_manager.create_task(
            name="Task 2",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule
        )
        
        # Verify count
        self.assertEqual(self.task_manager.get_task_count(), 2)
    
    def test_get_task_count_by_status(self):
        """Test getting task count by status."""
        # Create tasks with different statuses
        task_id1 = self.task_manager.create_task(
            name="Task 1",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        task_id2 = self.task_manager.create_task(
            name="Task 2",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule
        )
        
        # Update one task status
        self.task_manager.update_task_status(task_id2, TaskStatus.RUNNING)
        
        # Test counts
        self.assertEqual(self.task_manager.get_task_count_by_status(TaskStatus.PENDING), 1)
        self.assertEqual(self.task_manager.get_task_count_by_status(TaskStatus.RUNNING), 1)
        self.assertEqual(self.task_manager.get_task_count_by_status(TaskStatus.COMPLETED), 0)
    
    def test_clear_all_tasks(self):
        """Test clearing all tasks."""
        # Create some tasks
        self.task_manager.create_task(
            name="Task 1",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        self.task_manager.create_task(
            name="Task 2",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule
        )
        
        # Verify tasks exist
        self.assertEqual(self.task_manager.get_task_count(), 2)
        
        # Clear all tasks
        success = self.task_manager.clear_all_tasks()
        self.assertTrue(success)
        
        # Verify all tasks are cleared
        self.assertEqual(self.task_manager.get_task_count(), 0)
        self.assertEqual(len(self.task_manager.get_all_tasks()), 0)
    
    def test_export_import_tasks(self):
        """Test exporting and importing tasks."""
        # Create some tasks
        task_id1 = self.task_manager.create_task(
            name="Task 1",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        task_id2 = self.task_manager.create_task(
            name="Task 2",
            target_app="calculator",
            action_type=ActionType.LAUNCH_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule
        )
        
        # Export tasks
        exported_data = self.task_manager.export_tasks()
        self.assertEqual(len(exported_data), 2)
        
        # Clear tasks
        self.task_manager.clear_all_tasks()
        self.assertEqual(self.task_manager.get_task_count(), 0)
        
        # Import tasks
        imported_count = self.task_manager.import_tasks(exported_data)
        self.assertEqual(imported_count, 2)
        self.assertEqual(self.task_manager.get_task_count(), 2)
        
        # Verify imported tasks
        imported_tasks = self.task_manager.get_all_tasks()
        imported_ids = [task.id for task in imported_tasks]
        self.assertIn(task_id1, imported_ids)
        self.assertIn(task_id2, imported_ids)
    
    def test_validate_task(self):
        """Test task validation."""
        # Create a valid task
        task_id = self.task_manager.create_task(
            name="Valid Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        task = self.task_manager.get_task(task_id)
        self.assertTrue(self.task_manager.validate_task(task))
        
        # Create an invalid task (manually for testing)
        invalid_task = Task(
            id="invalid-id",
            name="",  # Empty name should be invalid
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.assertFalse(self.task_manager.validate_task(invalid_task))
    
    @patch('src.core.task_manager.TaskManager._task_storage')
    def test_storage_integration(self, mock_storage):
        """Test integration with task storage."""
        # Set up mock storage
        mock_storage.save_task.return_value = True
        mock_storage.load_all_tasks.return_value = []
        
        # Set storage
        self.task_manager.set_task_storage(mock_storage)
        
        # Create a task
        task_id = self.task_manager.create_task(
            name="Storage Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params=self.sample_action_params,
            schedule=self.sample_schedule
        )
        
        # Verify storage was called
        mock_storage.save_task.assert_called()
        
        # Update task
        self.task_manager.update_task(task_id, name="Updated Task")
        
        # Verify storage was called again
        self.assertEqual(mock_storage.save_task.call_count, 2)


if __name__ == '__main__':
    unittest.main()