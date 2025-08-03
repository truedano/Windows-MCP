"""
Tests for TaskStorage functionality.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from src.storage.task_storage import TaskStorage
from src.models.task import Task, TaskStatus
from src.models.action import ActionType
from src.models.schedule import Schedule, ScheduleType


class TestTaskStorage(unittest.TestCase):
    """Test cases for TaskStorage class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.test_dir) / "test_tasks.json"
        self.backup_dir = Path(self.test_dir) / "backups"
        
        # Create task storage instance
        self.storage = TaskStorage(
            storage_path=str(self.storage_path),
            backup_dir=str(self.backup_dir)
        )
        
        # Create sample task for testing
        self.sample_schedule = Schedule(
            schedule_type=ScheduleType.ONCE,
            start_time=datetime.now() + timedelta(hours=1),
            end_time=None,
            interval=None,
            days_of_week=None,
            conditions=None
        )
        
        self.sample_task = Task(
            id="test-task-1",
            name="Test Task",
            target_app="notepad",
            action_type=ActionType.LAUNCH_APP,
            action_params={'app_name': 'notepad'},
            schedule=self.sample_schedule,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test TaskStorage initialization."""
        # Verify directories were created
        self.assertTrue(self.storage_path.parent.exists())
        self.assertTrue(self.backup_dir.exists())
        
        # Verify empty tasks file was created
        self.assertTrue(self.storage_path.exists())
        
        # Verify file contains empty dict
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data, {})
    
    def test_save_task_success(self):
        """Test successful task saving."""
        success = self.storage.save_task(self.sample_task)
        self.assertTrue(success)
        
        # Verify task was saved to file
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn(self.sample_task.id, data)
        self.assertEqual(data[self.sample_task.id]['name'], self.sample_task.name)
    
    def test_save_task_update_existing(self):
        """Test updating an existing task."""
        # Save initial task
        self.storage.save_task(self.sample_task)
        
        # Update task
        self.sample_task.name = "Updated Task"
        success = self.storage.save_task(self.sample_task)
        self.assertTrue(success)
        
        # Verify update
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data[self.sample_task.id]['name'], "Updated Task")
    
    def test_load_task_existing(self):
        """Test loading an existing task."""
        # Save task first
        self.storage.save_task(self.sample_task)
        
        # Load task
        loaded_task = self.storage.load_task(self.sample_task.id)
        
        self.assertIsNotNone(loaded_task)
        self.assertEqual(loaded_task.id, self.sample_task.id)
        self.assertEqual(loaded_task.name, self.sample_task.name)
        self.assertEqual(loaded_task.target_app, self.sample_task.target_app)
        self.assertEqual(loaded_task.action_type, self.sample_task.action_type)
    
    def test_load_task_nonexistent(self):
        """Test loading a non-existent task."""
        loaded_task = self.storage.load_task("nonexistent-id")
        self.assertIsNone(loaded_task)
    
    def test_load_all_tasks_empty(self):
        """Test loading all tasks when storage is empty."""
        tasks = self.storage.load_all_tasks()
        self.assertEqual(len(tasks), 0)
    
    def test_load_all_tasks_with_data(self):
        """Test loading all tasks with data."""
        # Create multiple tasks
        task2 = Task(
            id="test-task-2",
            name="Test Task 2",
            target_app="calculator",
            action_type=ActionType.CLOSE_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Save tasks
        self.storage.save_task(self.sample_task)
        self.storage.save_task(task2)
        
        # Load all tasks
        tasks = self.storage.load_all_tasks()
        
        self.assertEqual(len(tasks), 2)
        task_ids = [task.id for task in tasks]
        self.assertIn(self.sample_task.id, task_ids)
        self.assertIn(task2.id, task_ids)
    
    def test_delete_task_existing(self):
        """Test deleting an existing task."""
        # Save task first
        self.storage.save_task(self.sample_task)
        
        # Verify task exists
        self.assertIsNotNone(self.storage.load_task(self.sample_task.id))
        
        # Delete task
        success = self.storage.delete_task(self.sample_task.id)
        self.assertTrue(success)
        
        # Verify task is deleted
        self.assertIsNone(self.storage.load_task(self.sample_task.id))
    
    def test_delete_task_nonexistent(self):
        """Test deleting a non-existent task."""
        success = self.storage.delete_task("nonexistent-id")
        self.assertFalse(success)
    
    def test_backup_tasks(self):
        """Test creating a backup of tasks."""
        # Save some tasks
        self.storage.save_task(self.sample_task)
        
        # Create backup
        backup_path = self.storage.backup_tasks()
        
        self.assertTrue(Path(backup_path).exists())
        self.assertTrue(backup_path.endswith('.json'))
        
        # Verify backup content
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        self.assertIn(self.sample_task.id, backup_data)
    
    def test_backup_tasks_custom_name(self):
        """Test creating a backup with custom name."""
        self.storage.save_task(self.sample_task)
        
        custom_name = "custom_backup.json"
        backup_path = self.storage.backup_tasks(custom_name)
        
        self.assertTrue(backup_path.endswith(custom_name))
        self.assertTrue(Path(backup_path).exists())
    
    def test_restore_tasks_success(self):
        """Test successful task restoration."""
        # Save original tasks
        self.storage.save_task(self.sample_task)
        
        # Create backup
        backup_path = self.storage.backup_tasks()
        
        # Clear tasks
        self.storage.clear_all_tasks()
        self.assertEqual(len(self.storage.load_all_tasks()), 0)
        
        # Restore from backup
        success = self.storage.restore_tasks(backup_path)
        self.assertTrue(success)
        
        # Verify restoration
        tasks = self.storage.load_all_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, self.sample_task.id)
    
    def test_restore_tasks_nonexistent_file(self):
        """Test restoring from non-existent backup file."""
        success = self.storage.restore_tasks("nonexistent_backup.json")
        self.assertFalse(success)
    
    def test_get_task_count(self):
        """Test getting task count."""
        # Initially empty
        self.assertEqual(self.storage.get_task_count(), 0)
        
        # Add tasks
        self.storage.save_task(self.sample_task)
        self.assertEqual(self.storage.get_task_count(), 1)
        
        # Add another task
        task2 = Task(
            id="test-task-2",
            name="Test Task 2",
            target_app="calculator",
            action_type=ActionType.CLOSE_APP,
            action_params={'app_name': 'calculator'},
            schedule=self.sample_schedule,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        self.storage.save_task(task2)
        self.assertEqual(self.storage.get_task_count(), 2)
    
    def test_clear_all_tasks(self):
        """Test clearing all tasks."""
        # Add some tasks
        self.storage.save_task(self.sample_task)
        self.assertEqual(self.storage.get_task_count(), 1)
        
        # Clear all tasks
        success = self.storage.clear_all_tasks()
        self.assertTrue(success)
        
        # Verify all tasks are cleared
        self.assertEqual(self.storage.get_task_count(), 0)
        self.assertEqual(len(self.storage.load_all_tasks()), 0)
    
    def test_export_tasks(self):
        """Test exporting tasks."""
        # Save some tasks
        self.storage.save_task(self.sample_task)
        
        # Export tasks
        export_path = Path(self.test_dir) / "exported_tasks.json"
        success = self.storage.export_tasks(str(export_path))
        self.assertTrue(success)
        
        # Verify export file
        self.assertTrue(export_path.exists())
        
        with open(export_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        self.assertIn(self.sample_task.id, export_data)
    
    def test_import_tasks_merge(self):
        """Test importing tasks with merge."""
        # Create import data
        import_data = {
            "imported-task-1": {
                "id": "imported-task-1",
                "name": "Imported Task",
                "target_app": "notepad",
                "action_type": "launch_app",
                "action_params": {"app_name": "notepad"},
                "schedule": self.sample_schedule.to_dict(),
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "last_executed": None,
                "next_execution": None,
                "retry_count": 0,
                "max_retries": 3
            }
        }
        
        # Save to import file
        import_path = Path(self.test_dir) / "import_tasks.json"
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_data, f)
        
        # Save existing task
        self.storage.save_task(self.sample_task)
        
        # Import tasks (merge)
        imported_count = self.storage.import_tasks(str(import_path), merge=True)
        self.assertEqual(imported_count, 1)
        
        # Verify both tasks exist
        tasks = self.storage.load_all_tasks()
        self.assertEqual(len(tasks), 2)
        
        task_ids = [task.id for task in tasks]
        self.assertIn(self.sample_task.id, task_ids)
        self.assertIn("imported-task-1", task_ids)
    
    def test_import_tasks_replace(self):
        """Test importing tasks with replace."""
        # Create import data
        import_data = {
            "imported-task-1": {
                "id": "imported-task-1",
                "name": "Imported Task",
                "target_app": "notepad",
                "action_type": "launch_app",
                "action_params": {"app_name": "notepad"},
                "schedule": self.sample_schedule.to_dict(),
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "last_executed": None,
                "next_execution": None,
                "retry_count": 0,
                "max_retries": 3
            }
        }
        
        # Save to import file
        import_path = Path(self.test_dir) / "import_tasks.json"
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_data, f)
        
        # Save existing task
        self.storage.save_task(self.sample_task)
        
        # Import tasks (replace)
        imported_count = self.storage.import_tasks(str(import_path), merge=False)
        self.assertEqual(imported_count, 1)
        
        # Verify only imported task exists
        tasks = self.storage.load_all_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, "imported-task-1")
    
    def test_get_storage_info(self):
        """Test getting storage information."""
        # Save a task
        self.storage.save_task(self.sample_task)
        
        # Create a backup
        self.storage.backup_tasks("test_backup.json")
        
        # Get storage info
        info = self.storage.get_storage_info()
        
        self.assertIn('storage_path', info)
        self.assertIn('backup_dir', info)
        self.assertIn('file_exists', info)
        self.assertIn('file_size', info)
        self.assertIn('task_count', info)
        self.assertIn('last_modified', info)
        self.assertIn('backups', info)
        
        self.assertTrue(info['file_exists'])
        self.assertEqual(info['task_count'], 1)
        self.assertGreater(info['file_size'], 0)
        self.assertEqual(len(info['backups']), 1)
    
    def test_cleanup_old_backups(self):
        """Test cleaning up old backup files."""
        # Create multiple backups
        for i in range(5):
            self.storage.backup_tasks(f"backup_{i}.json")
        
        # Verify all backups exist
        backup_files = list(self.backup_dir.glob("*.json"))
        self.assertEqual(len(backup_files), 5)
        
        # Clean up, keeping only 3
        deleted_count = self.storage.cleanup_old_backups(keep_count=3)
        self.assertEqual(deleted_count, 2)
        
        # Verify only 3 backups remain
        remaining_files = list(self.backup_dir.glob("*.json"))
        self.assertEqual(len(remaining_files), 3)
    
    def test_exists_method(self):
        """Test the exists method."""
        # Task doesn't exist initially
        self.assertFalse(self.storage.exists(self.sample_task.id))
        
        # Save task
        self.storage.save_task(self.sample_task)
        
        # Task should exist now
        self.assertTrue(self.storage.exists(self.sample_task.id))
    
    def test_generic_storage_methods(self):
        """Test generic storage interface methods."""
        # Test save method
        success = self.storage.save(self.sample_task)
        self.assertTrue(success)
        
        # Test load method
        tasks = self.storage.load()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, self.sample_task.id)
        
        # Test delete method
        success = self.storage.delete(self.sample_task.id)
        self.assertTrue(success)
        
        # Verify deletion
        self.assertFalse(self.storage.exists(self.sample_task.id))
    
    def test_corrupted_file_handling(self):
        """Test handling of corrupted JSON files."""
        # Write invalid JSON to file
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        # Should handle gracefully and return empty list
        tasks = self.storage.load_all_tasks()
        self.assertEqual(len(tasks), 0)
        
        # Should create backup of corrupted file
        corrupted_backup = self.storage_path.with_suffix('.corrupted.json')
        self.assertTrue(corrupted_backup.exists())
    
    def test_invalid_task_data_handling(self):
        """Test handling of invalid task data during import."""
        # Create import data with invalid task
        import_data = {
            "valid-task": {
                "id": "valid-task",
                "name": "Valid Task",
                "target_app": "notepad",
                "action_type": "launch_app",
                "action_params": {"app_name": "notepad"},
                "schedule": self.sample_schedule.to_dict(),
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "last_executed": None,
                "next_execution": None,
                "retry_count": 0,
                "max_retries": 3
            },
            "invalid-task": {
                "id": "invalid-task",
                "name": "",  # Invalid empty name
                "target_app": "",  # Invalid empty target_app
                "action_type": "invalid_action",  # Invalid action type
                "action_params": {},
                "schedule": {},  # Invalid schedule
                "status": "invalid_status",  # Invalid status
                "created_at": "invalid_date",  # Invalid date
            }
        }
        
        # Save to import file
        import_path = Path(self.test_dir) / "mixed_import.json"
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_data, f)
        
        # Import should only import valid tasks
        imported_count = self.storage.import_tasks(str(import_path))
        self.assertEqual(imported_count, 1)  # Only valid task imported
        
        # Verify only valid task exists
        tasks = self.storage.load_all_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, "valid-task")
    
    def test_thread_safety(self):
        """Test thread safety of storage operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def save_task_worker(task_id):
            try:
                task = Task(
                    id=task_id,
                    name=f"Task {task_id}",
                    target_app="notepad",
                    action_type=ActionType.LAUNCH_APP,
                    action_params={'app_name': 'notepad'},
                    schedule=self.sample_schedule,
                    status=TaskStatus.PENDING,
                    created_at=datetime.now()
                )
                success = self.storage.save_task(task)
                results.append((task_id, success))
            except Exception as e:
                errors.append((task_id, str(e)))
        
        # Create multiple threads to save tasks concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=save_task_worker, args=(f"thread-task-{i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10)
        
        # Verify all tasks were saved
        all_tasks = self.storage.load_all_tasks()
        self.assertEqual(len(all_tasks), 10)
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_permission_error_handling(self, mock_open):
        """Test handling of permission errors."""
        # Should handle permission errors gracefully
        success = self.storage.save_task(self.sample_task)
        self.assertFalse(success)
        
        task = self.storage.load_task(self.sample_task.id)
        self.assertIsNone(task)


if __name__ == '__main__':
    unittest.main()