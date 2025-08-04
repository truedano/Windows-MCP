"""
Tests for log storage functionality.
"""

import json
import tempfile
import unittest
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.storage.log_storage import LogStorage, LogIndex
from src.models.execution import ExecutionLog, ExecutionResult


class TestLogIndex(unittest.TestCase):
    """Test cases for LogIndex class."""
    
    def setUp(self):
        """Set up test environment."""
        self.index = LogIndex()
        
        # Create test logs
        self.log1 = ExecutionLog.create_log(
            "test_schedule_1",
            ExecutionResult.success_result("launch_app", "notepad", "App launched successfully"),
            timedelta(seconds=2)
        )
        
        self.log2 = ExecutionLog.create_log(
            "test_schedule_2",
            ExecutionResult.failure_result("close_app", "chrome", "App not found"),
            timedelta(seconds=1)
        )
        
        self.log3 = ExecutionLog.create_log(
            "test_schedule_1",
            ExecutionResult.success_result("resize_window", "notepad", "Window resized"),
            timedelta(seconds=3)
        )
    
    def test_add_and_search_logs(self):
        """Test adding logs to index and searching."""
        # Add logs to index
        self.index.add_log(self.log1)
        self.index.add_log(self.log2)
        self.index.add_log(self.log3)
        
        # Search by schedule name
        result = self.index.search({'schedule_name': 'test_schedule_1'})
        self.assertEqual(len(result), 2)
        self.assertIn(self.log1.id, result)
        self.assertIn(self.log3.id, result)
        
        # Search by success status
        result = self.index.search({'success': True})
        self.assertEqual(len(result), 2)
        self.assertIn(self.log1.id, result)
        self.assertIn(self.log3.id, result)
        
        # Search by operation
        result = self.index.search({'operation': 'launch_app'})
        self.assertEqual(len(result), 1)
        self.assertIn(self.log1.id, result)
        
        # Text search
        result = self.index.search({'query': 'notepad'})
        self.assertEqual(len(result), 2)
        self.assertIn(self.log1.id, result)
        self.assertIn(self.log3.id, result)
    
    def test_remove_log(self):
        """Test removing logs from index."""
        # Add logs
        self.index.add_log(self.log1)
        self.index.add_log(self.log2)
        
        # Verify logs are indexed
        result = self.index.search({'schedule_name': 'test_schedule_1'})
        self.assertEqual(len(result), 1)
        
        # Remove log
        self.index.remove_log(self.log1)
        
        # Verify log is removed
        result = self.index.search({'schedule_name': 'test_schedule_1'})
        self.assertEqual(len(result), 0)
        
        # Other log should still be there
        result = self.index.search({'schedule_name': 'test_schedule_2'})
        self.assertEqual(len(result), 1)
    
    def test_date_filtering(self):
        """Test date-based filtering."""
        # Set specific dates for logs
        yesterday = datetime.now() - timedelta(days=1)
        today = datetime.now()
        
        self.log1.execution_time = yesterday
        self.log2.execution_time = today
        
        self.index.add_log(self.log1)
        self.index.add_log(self.log2)
        
        # Search for logs from today
        result = self.index.search({'start_date': today.date()})
        self.assertEqual(len(result), 1)
        self.assertIn(self.log2.id, result)
        
        # Search for logs up to yesterday
        result = self.index.search({'end_date': yesterday.date()})
        self.assertEqual(len(result), 1)
        self.assertIn(self.log1.id, result)
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        self.index.add_log(self.log1)
        self.index.add_log(self.log2)
        self.index.add_log(self.log3)
        
        # Search by schedule name AND success status
        result = self.index.search({
            'schedule_name': 'test_schedule_1',
            'success': True
        })
        self.assertEqual(len(result), 2)
        self.assertIn(self.log1.id, result)
        self.assertIn(self.log3.id, result)
        
        # Search by operation AND text query
        result = self.index.search({
            'operation': 'launch_app',
            'query': 'notepad'
        })
        self.assertEqual(len(result), 1)
        self.assertIn(self.log1.id, result)
    
    def test_clear_index(self):
        """Test clearing the entire index."""
        self.index.add_log(self.log1)
        self.index.add_log(self.log2)
        
        # Verify logs are indexed
        result = self.index.search({})
        self.assertGreater(len(result), 0)
        
        # Clear index
        self.index.clear()
        
        # Verify index is empty
        result = self.index.search({})
        self.assertEqual(len(result), 0)


class TestLogStorage(unittest.TestCase):
    """Test cases for LogStorage class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "logs"
        self.storage = LogStorage(
            logs_dir=str(self.logs_dir),
            logs_file="test_logs.json"
        )
        
        # Create test logs
        self.log1 = ExecutionLog.create_log(
            "test_schedule_1",
            ExecutionResult.success_result("launch_app", "notepad", "App launched successfully"),
            timedelta(seconds=2)
        )
        
        self.log2 = ExecutionLog.create_log(
            "test_schedule_2",
            ExecutionResult.failure_result("close_app", "chrome", "App not found"),
            timedelta(seconds=1)
        )
        
        self.log3 = ExecutionLog.create_log(
            "test_schedule_1",
            ExecutionResult.success_result("resize_window", "notepad", "Window resized"),
            timedelta(seconds=3)
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_directory_creation(self):
        """Test that directories are created properly."""
        self.assertTrue(self.logs_dir.exists())
        self.assertTrue((self.logs_dir / "archive").exists())
    
    def test_save_and_load_logs(self):
        """Test saving and loading logs."""
        # Save logs
        self.assertTrue(self.storage.save_log(self.log1))
        self.assertTrue(self.storage.save_log(self.log2))
        self.assertTrue(self.storage.save_log(self.log3))
        
        # Load all logs
        logs = self.storage.load_logs(0, 10, {})
        self.assertEqual(len(logs), 3)
        
        # Verify logs are sorted by execution time (newest first)
        for i in range(len(logs) - 1):
            self.assertGreaterEqual(logs[i].execution_time, logs[i + 1].execution_time)
    
    def test_pagination(self):
        """Test log pagination."""
        # Save multiple logs
        for i in range(10):
            log = ExecutionLog.create_log(
                f"schedule_{i}",
                ExecutionResult.success_result("test_op", "test_target", f"Message {i}"),
                timedelta(seconds=1)
            )
            self.storage.save_log(log)
        
        # Test pagination
        page1 = self.storage.load_logs(0, 5, {})
        page2 = self.storage.load_logs(1, 5, {})
        
        self.assertEqual(len(page1), 5)
        self.assertEqual(len(page2), 5)
        
        # Verify no overlap
        page1_ids = {log.id for log in page1}
        page2_ids = {log.id for log in page2}
        self.assertEqual(len(page1_ids & page2_ids), 0)
    
    def test_filtering(self):
        """Test log filtering."""
        # Save test logs
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        self.storage.save_log(self.log3)
        
        # Filter by schedule name
        logs = self.storage.load_logs(0, 10, {'schedule_name': 'test_schedule_1'})
        self.assertEqual(len(logs), 2)
        
        # Filter by success status
        logs = self.storage.load_logs(0, 10, {'success': True})
        self.assertEqual(len(logs), 2)
        
        # Filter by operation
        logs = self.storage.load_logs(0, 10, {'operation': 'launch_app'})
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].id, self.log1.id)
    
    def test_search_logs(self):
        """Test log searching."""
        # Save test logs
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        self.storage.save_log(self.log3)
        
        # Search by text
        results = self.storage.search_logs("notepad")
        self.assertEqual(len(results), 2)
        
        results = self.storage.search_logs("chrome")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.log2.id)
        
        results = self.storage.search_logs("nonexistent")
        self.assertEqual(len(results), 0)
    
    def test_delete_logs(self):
        """Test deleting logs by date."""
        # Create logs with different dates
        old_date = datetime.now() - timedelta(days=10)
        recent_date = datetime.now() - timedelta(days=1)
        
        self.log1.execution_time = old_date
        self.log2.execution_time = recent_date
        
        # Save logs
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        
        # Verify both logs exist
        logs = self.storage.load_logs(0, 10, {})
        self.assertEqual(len(logs), 2)
        
        # Delete logs older than 5 days
        cutoff_date = datetime.now() - timedelta(days=5)
        success = self.storage.delete_logs(cutoff_date)
        self.assertTrue(success)
        
        # Verify only recent log remains
        logs = self.storage.load_logs(0, 10, {})
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].id, self.log2.id)
    
    def test_export_json(self):
        """Test exporting logs to JSON format."""
        # Save test logs
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        
        # Export to JSON
        export_path = self.temp_dir + "/export.json"
        logs = [self.log1, self.log2]
        success = self.storage.export_logs(logs, "json", export_path)
        self.assertTrue(success)
        
        # Verify export file
        self.assertTrue(Path(export_path).exists())
        
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['total_logs'], 2)
        self.assertEqual(len(data['logs']), 2)
        self.assertIn('exported_at', data)
    
    def test_export_csv(self):
        """Test exporting logs to CSV format."""
        # Save test logs
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        
        # Export to CSV
        export_path = self.temp_dir + "/export.csv"
        logs = [self.log1, self.log2]
        success = self.storage.export_logs(logs, "csv", export_path)
        self.assertTrue(success)
        
        # Verify export file
        self.assertTrue(Path(export_path).exists())
        
        with open(export_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check header and data rows
        lines = content.strip().split('\n')
        self.assertGreaterEqual(len(lines), 3)  # Header + 2 data rows
        self.assertIn('ID', lines[0])  # Header should contain ID
    
    def test_export_txt(self):
        """Test exporting logs to text format."""
        # Save test logs
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        
        # Export to TXT
        export_path = self.temp_dir + "/export.txt"
        logs = [self.log1, self.log2]
        success = self.storage.export_logs(logs, "txt", export_path)
        self.assertTrue(success)
        
        # Verify export file
        self.assertTrue(Path(export_path).exists())
        
        with open(export_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("Execution Logs Export", content)
        self.assertIn("Total logs: 2", content)
        self.assertIn(self.log1.id, content)
        self.assertIn(self.log2.id, content)
    
    def test_unsupported_export_format(self):
        """Test handling of unsupported export formats."""
        export_path = self.temp_dir + "/export.xyz"
        logs = [self.log1]
        success = self.storage.export_logs(logs, "xyz", export_path)
        self.assertFalse(success)
    
    @patch('src.storage.log_storage.MAX_LOG_FILE_SIZE', 100)  # Small size for testing
    def test_log_rotation(self):
        """Test log file rotation."""
        # Create a storage with small max file size
        small_storage = LogStorage(
            logs_dir=str(self.logs_dir),
            logs_file="small_logs.json"
        )
        small_storage.max_file_size = 100  # Very small for testing
        
        # Save enough logs to trigger rotation
        for i in range(20):
            log = ExecutionLog.create_log(
                f"schedule_{i}",
                ExecutionResult.success_result("test_op", "test_target", f"Long message {i}" * 10),
                timedelta(seconds=1)
            )
            small_storage.save_log(log)
        
        # Check that archive directory has files
        archive_dir = self.logs_dir / "archive"
        archive_files = list(archive_dir.glob("*.json.gz"))
        self.assertGreater(len(archive_files), 0)
    
    def test_rebuild_index(self):
        """Test rebuilding the search index."""
        # Save test logs
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        
        # Verify logs can be found
        logs = self.storage.search_logs("notepad")
        self.assertGreater(len(logs), 0)
        
        # Rebuild index
        success = self.storage.rebuild_index()
        self.assertTrue(success)
        
        # Verify logs can still be found
        logs = self.storage.search_logs("notepad")
        self.assertGreater(len(logs), 0)
    
    def test_get_statistics(self):
        """Test getting storage statistics."""
        # Save test logs
        self.storage.save_log(self.log1)  # Success
        self.storage.save_log(self.log2)  # Failure
        self.storage.save_log(self.log3)  # Success
        
        # Get statistics
        stats = self.storage.get_statistics()
        
        self.assertEqual(stats['total_logs'], 3)
        self.assertEqual(stats['successful_logs'], 2)
        self.assertEqual(stats['failed_logs'], 1)
        self.assertAlmostEqual(stats['success_rate'], 66.67, places=1)
        self.assertIn('current_file_size', stats)
        self.assertIn('total_size', stats)
    
    def test_memory_management(self):
        """Test memory cache management."""
        # Set small cache size for testing
        self.storage.max_logs_in_memory = 5
        
        # Save more logs than cache can hold
        logs = []
        for i in range(10):
            log = ExecutionLog.create_log(
                f"schedule_{i}",
                ExecutionResult.success_result("test_op", "test_target", f"Message {i}"),
                timedelta(seconds=1)
            )
            logs.append(log)
            self.storage.save_log(log)
        
        # Verify cache size is limited
        self.assertLessEqual(len(self.storage._log_cache), self.storage.max_logs_in_memory)
        
        # Verify we can still load all logs (from files)
        all_logs = self.storage.load_logs(0, 20, {})
        self.assertEqual(len(all_logs), 10)
    
    def test_persistence_across_instances(self):
        """Test that logs persist across storage instances."""
        # Save logs with first instance
        self.storage.save_log(self.log1)
        self.storage.save_log(self.log2)
        
        # Create new storage instance
        new_storage = LogStorage(
            logs_dir=str(self.logs_dir),
            logs_file="test_logs.json"
        )
        
        # Verify logs are loaded
        logs = new_storage.load_logs(0, 10, {})
        self.assertEqual(len(logs), 2)
        
        # Verify search works
        results = new_storage.search_logs("notepad")
        self.assertGreater(len(results), 0)
    
    def test_istorage_interface(self):
        """Test IStorage interface methods."""
        # Test save method
        success = self.storage.save(self.log1)
        self.assertTrue(success)
        
        # Test exists method
        exists = self.storage.exists(self.log1.id)
        self.assertTrue(exists)
        
        # Test load method
        logs = self.storage.load()
        self.assertIsInstance(logs, list)
        self.assertGreater(len(logs), 0)
        
        # Test delete method
        success = self.storage.delete(self.log1.id)
        self.assertTrue(success)
        
        exists = self.storage.exists(self.log1.id)
        self.assertFalse(exists)
    
    def test_concurrent_access(self):
        """Test thread-safe concurrent access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def save_logs(start_idx):
            try:
                for i in range(start_idx, start_idx + 10):
                    log = ExecutionLog.create_log(
                        f"schedule_{i}",
                        ExecutionResult.success_result("test_op", "test_target", f"Message {i}"),
                        timedelta(seconds=1)
                    )
                    success = self.storage.save_log(log)
                    results.append(success)
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=save_logs, args=(i * 10,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0)
        
        # Verify all saves were successful
        self.assertEqual(len(results), 30)
        self.assertTrue(all(results))
        
        # Verify all logs were saved
        logs = self.storage.load_logs(0, 50, {})
        self.assertEqual(len(logs), 30)


if __name__ == "__main__":
    unittest.main()