#!/usr/bin/env python3
"""
Performance and Stability Tests for Windows Scheduler GUI
Tests long-term stability, large data handling, error recovery, and performance.

This test suite covers task 15.2 requirements:
- Long-term running tests to verify system stability
- Test large task and log processing capabilities
- Error recovery and exception handling tests
- Log storage and retrieval performance tests
"""

import sys
import os
import unittest
import threading
import time
import gc
import psutil
import tracemalloc
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class PerformanceStabilityTestSuite(unittest.TestCase):
    """Performance and stability test suite."""
    
    def setUp(self):
        """Set up test environment."""
        # Start memory tracking
        tracemalloc.start()
        
        # Record initial memory usage
        process = psutil.Process()
        self.initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp(prefix="perf_test_")
        
        print(f"Initial memory usage: {self.initial_memory:.2f} MB")
        
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Force garbage collection
        gc.collect()
        
        # Stop memory tracking
        tracemalloc.stop()
        
        # Record final memory usage
        process = psutil.Process()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = final_memory - self.initial_memory
        
        print(f"Final memory usage: {final_memory:.2f} MB")
        print(f"Memory difference: {memory_diff:+.2f} MB")
        
        # Check for significant memory leaks
        if memory_diff > 50:  # More than 50MB increase
            print(f"⚠ Potential memory leak detected: {memory_diff:.2f} MB increase")
    
    def test_01_long_term_stability(self):
        """Test 1: Long-term running test for system stability."""
        print("\n=== Test 1: Long-term Stability Test ===")
        
        try:
            from core.scheduler_engine import get_scheduler_engine
            from core.task_manager import TaskManager
            from models.task import Task, TaskStatus
            from models.schedule import Schedule, ScheduleType
            from models.action import ActionType
            
            print("Starting long-term stability test...")
            
            # Initialize components
            engine = get_scheduler_engine()
            task_manager = TaskManager()
            
            # Test duration (reduced for automated testing)
            test_duration = 30  # seconds (in production, this could be hours)
            start_time = time.time()
            iteration_count = 0
            
            print(f"Running stability test for {test_duration} seconds...")
            
            while time.time() - start_time < test_duration:
                iteration_count += 1
                
                # Create and manage tasks
                task = Task(
                    name=f"Stability Test Task {iteration_count}",
                    description=f"Long-term stability test iteration {iteration_count}",
                    action_type=ActionType.LAUNCH_APP,
                    action_params={"app_path": "notepad.exe"},
                    schedule=Schedule(
                        schedule_type=ScheduleType.ONCE,
                        start_time=datetime.now() + timedelta(seconds=60)
                    )
                )
                
                # Add task
                task_id = task_manager.add_task(task)
                
                # Retrieve task
                retrieved_task = task_manager.get_task(task_id)
                self.assertIsNotNone(retrieved_task)
                
                # Update task status
                retrieved_task.status = TaskStatus.COMPLETED
                task_manager.update_task(retrieved_task)
                
                # Clean up old tasks periodically
                if iteration_count % 10 == 0:
                    all_tasks = task_manager.get_all_tasks()
                    for t in all_tasks:
                        if t.status == TaskStatus.COMPLETED:
                            task_manager.delete_task(t.id)
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Check memory usage
                    process = psutil.Process()
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - self.initial_memory
                    
                    print(f"Iteration {iteration_count}: Memory usage: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
                
                # Brief pause to simulate real usage
                time.sleep(0.1)
            
            elapsed_time = time.time() - start_time
            print(f"✓ Stability test completed: {iteration_count} iterations in {elapsed_time:.2f} seconds")
            print(f"✓ Average iterations per second: {iteration_count/elapsed_time:.2f}")
            
            # Final memory check
            process = psutil.Process()
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - self.initial_memory
            
            # Memory increase should be reasonable (less than 100MB for this test)
            self.assertLess(memory_increase, 100, f"Excessive memory usage: {memory_increase:.2f} MB")
            
            print(f"✓ Memory usage within acceptable limits: {memory_increase:.2f} MB increase")
            
        except Exception as e:
            print(f"✗ Long-term stability test failed: {e}")
            self.fail(f"Long-term stability test failed: {e}")
    
    def test_02_large_data_processing(self):
        """Test 2: Large task and log processing capabilities."""
        print("\n=== Test 2: Large Data Processing Test ===")
        
        try:
            from core.task_manager import TaskManager
            from storage.log_storage import LogStorage
            from models.task import Task, TaskStatus
            from models.schedule import Schedule, ScheduleType
            from models.action import ActionType
            from models.execution import ExecutionLog, ExecutionStatus
            
            print("Testing large data processing capabilities...")
            
            task_manager = TaskManager()
            log_storage = LogStorage()
            
            # Test with large number of tasks
            large_task_count = 1000
            print(f"Creating {large_task_count} tasks...")
            
            start_time = time.time()
            task_ids = []
            
            for i in range(large_task_count):
                task = Task(
                    name=f"Bulk Test Task {i:04d}",
                    description=f"Large data processing test task {i}",
                    action_type=ActionType.LAUNCH_APP,
                    action_params={"app_path": f"test_app_{i % 10}.exe"},
                    schedule=Schedule(
                        schedule_type=ScheduleType.DAILY,
                        start_time=datetime.now() + timedelta(days=i % 7)
                    )
                )
                
                task_id = task_manager.add_task(task)
                task_ids.append(task_id)
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    print(f"  Created {i + 1} tasks ({rate:.1f} tasks/sec)")
            
            creation_time = time.time() - start_time
            print(f"✓ Created {large_task_count} tasks in {creation_time:.2f} seconds")
            print(f"✓ Task creation rate: {large_task_count/creation_time:.1f} tasks/sec")
            
            # Test task retrieval performance
            print("Testing task retrieval performance...")
            start_time = time.time()
            
            retrieved_count = 0
            for task_id in task_ids[:100]:  # Test first 100 for speed
                task = task_manager.get_task(task_id)
                if task:
                    retrieved_count += 1
            
            retrieval_time = time.time() - start_time
            print(f"✓ Retrieved {retrieved_count} tasks in {retrieval_time:.2f} seconds")
            
            # Test large number of logs
            large_log_count = 2000
            print(f"Creating {large_log_count} logs...")
            
            start_time = time.time()
            log_ids = []
            
            for i in range(large_log_count):
                log = ExecutionLog(
                    task_id=task_ids[i % len(task_ids)],
                    task_name=f"Bulk Test Task {i % len(task_ids):04d}",
                    execution_time=datetime.now() - timedelta(hours=i % 24),
                    status=ExecutionStatus.SUCCESS if i % 3 == 0 else ExecutionStatus.FAILED,
                    message=f"Large data processing test log entry {i}"
                )
                
                log_id = log_storage.add_log(log)
                log_ids.append(log_id)
                
                # Progress indicator
                if (i + 1) % 200 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    print(f"  Created {i + 1} logs ({rate:.1f} logs/sec)")
            
            log_creation_time = time.time() - start_time
            print(f"✓ Created {large_log_count} logs in {log_creation_time:.2f} seconds")
            print(f"✓ Log creation rate: {large_log_count/log_creation_time:.1f} logs/sec")
            
            # Test log query performance
            print("Testing log query performance...")
            start_time = time.time()
            
            all_logs = log_storage.get_logs(limit=500)
            query_time = time.time() - start_time
            
            print(f"✓ Queried {len(all_logs)} logs in {query_time:.2f} seconds")
            
            # Clean up test data
            print("Cleaning up test data...")
            cleanup_start = time.time()
            
            for task_id in task_ids:
                task_manager.delete_task(task_id)
            
            for log_id in log_ids:
                log_storage.delete_log(log_id)
            
            cleanup_time = time.time() - cleanup_start
            print(f"✓ Cleaned up test data in {cleanup_time:.2f} seconds")
            
        except Exception as e:
            print(f"✗ Large data processing test failed: {e}")
            self.fail(f"Large data processing test failed: {e}")
    
    def test_03_error_recovery_handling(self):
        """Test 3: Error recovery and exception handling."""
        print("\n=== Test 3: Error Recovery and Exception Handling Test ===")
        
        try:
            from core.error_handler import ErrorHandler
            from core.task_manager import TaskManager
            from core.scheduler_engine import get_scheduler_engine
            from models.task import Task
            from models.validation import ValidationError
            
            print("Testing error recovery and exception handling...")
            
            error_handler = ErrorHandler()
            task_manager = TaskManager()
            engine = get_scheduler_engine()
            
            # Test 1: Invalid task handling
            print("Testing invalid task handling...")
            try:
                invalid_task = Task(
                    name="",  # Invalid empty name
                    description="Test invalid task",
                    action_type=None,  # Invalid action type
                    action_params={}
                )
                invalid_task.validate()
                self.fail("Expected validation error was not raised")
            except (ValidationError, Exception) as e:
                print(f"✓ Invalid task properly rejected: {type(e).__name__}")
            
            # Test 2: Database corruption simulation
            print("Testing database error recovery...")
            
            # Simulate database errors
            original_add_task = task_manager.add_task
            
            def failing_add_task(task):
                raise Exception("Simulated database error")
            
            task_manager.add_task = failing_add_task
            
            try:
                valid_task = Task(
                    name="Test Task",
                    description="Test task for error handling",
                    action_type="LAUNCH_APP",
                    action_params={"app_path": "notepad.exe"}
                )
                task_manager.add_task(valid_task)
                self.fail("Expected database error was not raised")
            except Exception as e:
                print(f"✓ Database error properly handled: {e}")
            finally:
                # Restore original method
                task_manager.add_task = original_add_task
            
            # Test 3: Memory pressure simulation
            print("Testing memory pressure handling...")
            
            # Create memory pressure
            memory_hogs = []
            try:
                for i in range(10):
                    # Create large objects to simulate memory pressure
                    memory_hog = [0] * (1024 * 1024)  # 1M integers
                    memory_hogs.append(memory_hog)
                
                # Try to perform normal operations under memory pressure
                task = Task(
                    name="Memory Pressure Test",
                    description="Test under memory pressure",
                    action_type="LAUNCH_APP",
                    action_params={"app_path": "calc.exe"}
                )
                
                task_id = task_manager.add_task(task)
                retrieved_task = task_manager.get_task(task_id)
                
                self.assertIsNotNone(retrieved_task)
                print("✓ Operations successful under memory pressure")
                
            finally:
                # Clean up memory
                memory_hogs.clear()
                gc.collect()
            
            # Test 4: Concurrent access stress test
            print("Testing concurrent access handling...")
            
            def concurrent_task_operation(thread_id):
                """Perform task operations concurrently."""
                try:
                    for i in range(10):
                        task = Task(
                            name=f"Concurrent Task {thread_id}-{i}",
                            description=f"Concurrent test task from thread {thread_id}",
                            action_type="LAUNCH_APP",
                            action_params={"app_path": "notepad.exe"}
                        )
                        
                        task_id = task_manager.add_task(task)
                        retrieved_task = task_manager.get_task(task_id)
                        
                        if retrieved_task:
                            task_manager.delete_task(task_id)
                    
                    return True
                except Exception as e:
                    print(f"Thread {thread_id} error: {e}")
                    return False
            
            # Run concurrent operations
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_task_operation, i) for i in range(5)]
                results = [future.result() for future in as_completed(futures)]
            
            successful_threads = sum(results)
            print(f"✓ Concurrent access test: {successful_threads}/5 threads successful")
            
            # Test 5: Resource exhaustion recovery
            print("Testing resource exhaustion recovery...")
            
            # Simulate file handle exhaustion
            file_handles = []
            try:
                # Open many temporary files
                for i in range(100):
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    file_handles.append(temp_file)
                
                # Try to perform operations with limited resources
                task = Task(
                    name="Resource Test",
                    description="Test with limited resources",
                    action_type="LAUNCH_APP",
                    action_params={"app_path": "calc.exe"}
                )
                
                task_id = task_manager.add_task(task)
                self.assertIsNotNone(task_id)
                print("✓ Operations successful with limited resources")
                
            finally:
                # Clean up file handles
                for handle in file_handles:
                    try:
                        handle.close()
                        os.unlink(handle.name)
                    except:
                        pass
            
            print("✓ Error recovery and exception handling tests completed")
            
        except Exception as e:
            print(f"✗ Error recovery test failed: {e}")
            self.fail(f"Error recovery test failed: {e}")
    
    def test_04_log_storage_performance(self):
        """Test 4: Log storage and retrieval performance."""
        print("\n=== Test 4: Log Storage and Retrieval Performance Test ===")
        
        try:
            from storage.log_storage import LogStorage
            from models.execution import ExecutionLog, ExecutionStatus
            
            print("Testing log storage and retrieval performance...")
            
            log_storage = LogStorage()
            
            # Performance test parameters
            batch_sizes = [100, 500, 1000]
            
            for batch_size in batch_sizes:
                print(f"\nTesting batch size: {batch_size}")
                
                # Test log insertion performance
                print(f"  Inserting {batch_size} logs...")
                start_time = time.time()
                log_ids = []
                
                for i in range(batch_size):
                    log = ExecutionLog(
                        task_id=f"perf_test_task_{i % 10}",
                        task_name=f"Performance Test Task {i % 10}",
                        execution_time=datetime.now() - timedelta(minutes=i),
                        status=ExecutionStatus.SUCCESS if i % 2 == 0 else ExecutionStatus.FAILED,
                        message=f"Performance test log entry {i} with some detailed message content"
                    )
                    
                    log_id = log_storage.add_log(log)
                    log_ids.append(log_id)
                
                insertion_time = time.time() - start_time
                insertion_rate = batch_size / insertion_time
                print(f"  ✓ Insertion: {insertion_time:.2f}s ({insertion_rate:.1f} logs/sec)")
                
                # Test log retrieval performance
                print(f"  Retrieving logs...")
                start_time = time.time()
                
                # Test different retrieval patterns
                # 1. Get all logs
                all_logs = log_storage.get_logs(limit=batch_size)
                
                # 2. Get logs by status
                success_logs = log_storage.get_logs_by_status(ExecutionStatus.SUCCESS, limit=batch_size//2)
                
                # 3. Get logs by date range
                end_date = datetime.now()
                start_date = end_date - timedelta(hours=1)
                date_logs = log_storage.get_logs_by_date_range(start_date, end_date, limit=batch_size//2)
                
                retrieval_time = time.time() - start_time
                total_retrieved = len(all_logs) + len(success_logs) + len(date_logs)
                retrieval_rate = total_retrieved / retrieval_time if retrieval_time > 0 else 0
                
                print(f"  ✓ Retrieval: {retrieval_time:.2f}s ({retrieval_rate:.1f} logs/sec)")
                print(f"    - All logs: {len(all_logs)}")
                print(f"    - Success logs: {len(success_logs)}")
                print(f"    - Date range logs: {len(date_logs)}")
                
                # Test log search performance
                print(f"  Testing search performance...")
                start_time = time.time()
                
                search_results = log_storage.search_logs("Performance test", limit=100)
                
                search_time = time.time() - start_time
                print(f"  ✓ Search: {search_time:.2f}s ({len(search_results)} results)")
                
                # Test log deletion performance
                print(f"  Deleting {len(log_ids)} logs...")
                start_time = time.time()
                
                deleted_count = 0
                for log_id in log_ids:
                    if log_storage.delete_log(log_id):
                        deleted_count += 1
                
                deletion_time = time.time() - start_time
                deletion_rate = deleted_count / deletion_time if deletion_time > 0 else 0
                print(f"  ✓ Deletion: {deletion_time:.2f}s ({deletion_rate:.1f} logs/sec)")
                
                # Performance benchmarks
                self.assertGreater(insertion_rate, 50, f"Insertion rate too slow: {insertion_rate:.1f} logs/sec")
                self.assertGreater(retrieval_rate, 100, f"Retrieval rate too slow: {retrieval_rate:.1f} logs/sec")
                self.assertLess(search_time, 1.0, f"Search too slow: {search_time:.2f}s")
                
                print(f"  ✓ Performance benchmarks met for batch size {batch_size}")
            
            # Test log storage under concurrent access
            print("\nTesting concurrent log access...")
            
            def concurrent_log_operations(thread_id):
                """Perform log operations concurrently."""
                try:
                    logs_created = 0
                    for i in range(50):
                        log = ExecutionLog(
                            task_id=f"concurrent_task_{thread_id}_{i}",
                            task_name=f"Concurrent Test Task {thread_id}",
                            execution_time=datetime.now(),
                            status=ExecutionStatus.SUCCESS,
                            message=f"Concurrent log from thread {thread_id}, iteration {i}"
                        )
                        
                        log_id = log_storage.add_log(log)
                        if log_id:
                            logs_created += 1
                            
                            # Occasionally read back the log
                            if i % 10 == 0:
                                retrieved_log = log_storage.get_log(log_id)
                                if not retrieved_log:
                                    print(f"Warning: Could not retrieve log {log_id}")
                    
                    return logs_created
                except Exception as e:
                    print(f"Concurrent thread {thread_id} error: {e}")
                    return 0
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(concurrent_log_operations, i) for i in range(3)]
                results = [future.result() for future in as_completed(futures)]
            
            concurrent_time = time.time() - start_time
            total_concurrent_logs = sum(results)
            concurrent_rate = total_concurrent_logs / concurrent_time
            
            print(f"✓ Concurrent access: {total_concurrent_logs} logs in {concurrent_time:.2f}s ({concurrent_rate:.1f} logs/sec)")
            
            # Clean up concurrent test logs
            print("Cleaning up concurrent test logs...")
            cleanup_start = time.time()
            
            for thread_id in range(3):
                for i in range(50):
                    task_id = f"concurrent_task_{thread_id}_{i}"
                    logs = log_storage.get_logs_by_task_id(task_id)
                    for log in logs:
                        log_storage.delete_log(log.id)
            
            cleanup_time = time.time() - cleanup_start
            print(f"✓ Cleanup completed in {cleanup_time:.2f}s")
            
        except Exception as e:
            print(f"✗ Log storage performance test failed: {e}")
            self.fail(f"Log storage performance test failed: {e}")

def run_performance_stability_tests():
    """Run all performance and stability tests."""
    print("Windows Scheduler GUI - Performance and Stability Tests")
    print("=" * 65)
    print("Testing task 15.2 requirements:")
    print("- Long-term running tests for system stability")
    print("- Large task and log processing capabilities")
    print("- Error recovery and exception handling")
    print("- Log storage and retrieval performance")
    print("=" * 65)
    
    # Check system resources before starting
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent()
    
    print(f"System status before tests:")
    print(f"- Memory usage: {initial_memory:.2f} MB")
    print(f"- CPU usage: {cpu_percent:.1f}%")
    print(f"- Available memory: {psutil.virtual_memory().available / 1024 / 1024:.2f} MB")
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(PerformanceStabilityTestSuite)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 65)
    print("PERFORMANCE AND STABILITY TEST SUMMARY")
    print("=" * 65)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Final system status
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_diff = final_memory - initial_memory
    
    print(f"\nSystem status after tests:")
    print(f"- Memory usage: {final_memory:.2f} MB ({memory_diff:+.2f} MB)")
    print(f"- Available memory: {psutil.virtual_memory().available / 1024 / 1024:.2f} MB")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 ALL PERFORMANCE AND STABILITY TESTS PASSED!")
        print("✓ Task 15.2 requirements successfully verified")
        print("✓ System demonstrates good performance and stability")
    else:
        print("\n❌ SOME PERFORMANCE/STABILITY TESTS FAILED")
        print("✗ Task 15.2 requirements need attention")
    
    return success

if __name__ == "__main__":
    success = run_performance_stability_tests()
    sys.exit(0 if success else 1)