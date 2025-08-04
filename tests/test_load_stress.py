#!/usr/bin/env python3
"""
Load and Stress Testing for Windows Scheduler GUI
Tests system behavior under heavy load and stress conditions.
"""

import sys
import os
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class LoadStressTester:
    """Load and stress testing utility."""
    
    def __init__(self):
        self.results = {
            'operations_completed': 0,
            'operations_failed': 0,
            'total_time': 0,
            'errors': []
        }
        self.lock = threading.Lock()
    
    def record_success(self):
        """Record successful operation."""
        with self.lock:
            self.results['operations_completed'] += 1
    
    def record_failure(self, error):
        """Record failed operation."""
        with self.lock:
            self.results['operations_failed'] += 1
            self.results['errors'].append(str(error))
    
    def get_summary(self):
        """Get test summary."""
        total_ops = self.results['operations_completed'] + self.results['operations_failed']
        success_rate = (self.results['operations_completed'] / total_ops * 100) if total_ops > 0 else 0
        
        return {
            'total_operations': total_ops,
            'successful_operations': self.results['operations_completed'],
            'failed_operations': self.results['operations_failed'],
            'success_rate': success_rate,
            'error_count': len(self.results['errors']),
            'unique_errors': len(set(self.results['errors']))
        }

def stress_test_task_operations(tester, thread_id, operations_per_thread=100):
    """Stress test task operations in a single thread."""
    try:
        from core.task_manager import TaskManager
        from models.task import Task, TaskStatus
        from models.schedule import Schedule, ScheduleType
        from models.action import ActionType
        
        task_manager = TaskManager()
        
        for i in range(operations_per_thread):
            try:
                # Create random task
                task = Task(
                    name=f"Stress Test Task {thread_id}-{i}",
                    description=f"Load test task from thread {thread_id}, iteration {i}",
                    action_type=random.choice([ActionType.LAUNCH_APP, ActionType.CLOSE_APP, ActionType.MINIMIZE_WINDOW]),
                    action_params={
                        "app_path": random.choice(["notepad.exe", "calc.exe", "mspaint.exe"]),
                        "window_title": f"Test Window {i}"
                    },
                    schedule=Schedule(
                        schedule_type=random.choice([ScheduleType.ONCE, ScheduleType.DAILY, ScheduleType.WEEKLY]),
                        start_time=datetime.now() + timedelta(minutes=random.randint(1, 60))
                    )
                )
                
                # Add task
                task_id = task_manager.add_task(task)
                
                # Random operations
                operation = random.choice(['retrieve', 'update', 'delete'])
                
                if operation == 'retrieve':
                    retrieved_task = task_manager.get_task(task_id)
                    if retrieved_task:
                        tester.record_success()
                    else:
                        tester.record_failure("Task retrieval failed")
                
                elif operation == 'update':
                    task.description = f"Updated description {i}"
                    if task_manager.update_task(task):
                        tester.record_success()
                    else:
                        tester.record_failure("Task update failed")
                
                elif operation == 'delete':
                    if task_manager.delete_task(task_id):
                        tester.record_success()
                    else:
                        tester.record_failure("Task deletion failed")
                
                # Random delay to simulate real usage
                time.sleep(random.uniform(0.001, 0.01))
                
            except Exception as e:
                tester.record_failure(f"Task operation error: {e}")
        
        return True
        
    except Exception as e:
        tester.record_failure(f"Thread {thread_id} fatal error: {e}")
        return False

def stress_test_log_operations(tester, thread_id, operations_per_thread=200):
    """Stress test log operations in a single thread."""
    try:
        from storage.log_storage import LogStorage
        from models.execution import ExecutionLog, ExecutionStatus
        
        log_storage = LogStorage()
        
        for i in range(operations_per_thread):
            try:
                # Create random log
                log = ExecutionLog(
                    task_id=f"stress_task_{thread_id}_{i % 10}",
                    task_name=f"Stress Test Task {thread_id}",
                    execution_time=datetime.now() - timedelta(minutes=random.randint(0, 1440)),
                    status=random.choice([ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]),
                    message=f"Stress test log from thread {thread_id}, iteration {i}"
                )
                
                # Add log
                log_id = log_storage.add_log(log)
                
                # Random operations
                operation = random.choice(['retrieve', 'search', 'query', 'delete'])
                
                if operation == 'retrieve':
                    retrieved_log = log_storage.get_log(log_id)
                    if retrieved_log:
                        tester.record_success()
                    else:
                        tester.record_failure("Log retrieval failed")
                
                elif operation == 'search':
                    results = log_storage.search_logs(f"thread {thread_id}", limit=10)
                    tester.record_success()
                
                elif operation == 'query':
                    logs = log_storage.get_logs_by_status(ExecutionStatus.SUCCESS, limit=5)
                    tester.record_success()
                
                elif operation == 'delete':
                    if log_storage.delete_log(log_id):
                        tester.record_success()
                    else:
                        tester.record_failure("Log deletion failed")
                
                # Random delay
                time.sleep(random.uniform(0.001, 0.005))
                
            except Exception as e:
                tester.record_failure(f"Log operation error: {e}")
        
        return True
        
    except Exception as e:
        tester.record_failure(f"Log thread {thread_id} fatal error: {e}")
        return False

def run_load_stress_tests():
    """Run comprehensive load and stress tests."""
    print("Load and Stress Testing")
    print("=" * 25)
    
    # Test 1: Concurrent Task Operations
    print("\n1. Concurrent Task Operations Stress Test")
    print("-" * 45)
    
    task_tester = LoadStressTester()
    start_time = time.time()
    
    # Run concurrent task operations
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(stress_test_task_operations, task_tester, i, 50)
            for i in range(8)
        ]
        
        task_results = [future.result() for future in as_completed(futures)]
    
    task_time = time.time() - start_time
    task_summary = task_tester.get_summary()
    
    print(f"Task Operations Results:")
    print(f"- Duration: {task_time:.2f} seconds")
    print(f"- Total operations: {task_summary['total_operations']}")
    print(f"- Successful: {task_summary['successful_operations']}")
    print(f"- Failed: {task_summary['failed_operations']}")
    print(f"- Success rate: {task_summary['success_rate']:.1f}%")
    print(f"- Operations/sec: {task_summary['total_operations']/task_time:.1f}")
    print(f"- Threads completed: {sum(task_results)}/8")
    
    # Test 2: Concurrent Log Operations
    print("\n2. Concurrent Log Operations Stress Test")
    print("-" * 44)
    
    log_tester = LoadStressTester()
    start_time = time.time()
    
    # Run concurrent log operations
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(stress_test_log_operations, log_tester, i, 100)
            for i in range(6)
        ]
        
        log_results = [future.result() for future in as_completed(futures)]
    
    log_time = time.time() - start_time
    log_summary = log_tester.get_summary()
    
    print(f"Log Operations Results:")
    print(f"- Duration: {log_time:.2f} seconds")
    print(f"- Total operations: {log_summary['total_operations']}")
    print(f"- Successful: {log_summary['successful_operations']}")
    print(f"- Failed: {log_summary['failed_operations']}")
    print(f"- Success rate: {log_summary['success_rate']:.1f}%")
    print(f"- Operations/sec: {log_summary['total_operations']/log_time:.1f}")
    print(f"- Threads completed: {sum(log_results)}/6")
    
    # Test 3: Mixed Operations Under Load
    print("\n3. Mixed Operations Under Load")
    print("-" * 32)
    
    mixed_tester = LoadStressTester()
    start_time = time.time()
    
    # Run mixed operations
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit both task and log operations
        futures = []
        
        # 5 task operation threads
        for i in range(5):
            futures.append(executor.submit(stress_test_task_operations, mixed_tester, f"task_{i}", 30))
        
        # 5 log operation threads
        for i in range(5):
            futures.append(executor.submit(stress_test_log_operations, mixed_tester, f"log_{i}", 60))
        
        mixed_results = [future.result() for future in as_completed(futures)]
    
    mixed_time = time.time() - start_time
    mixed_summary = mixed_tester.get_summary()
    
    print(f"Mixed Operations Results:")
    print(f"- Duration: {mixed_time:.2f} seconds")
    print(f"- Total operations: {mixed_summary['total_operations']}")
    print(f"- Successful: {mixed_summary['successful_operations']}")
    print(f"- Failed: {mixed_summary['failed_operations']}")
    print(f"- Success rate: {mixed_summary['success_rate']:.1f}%")
    print(f"- Operations/sec: {mixed_summary['total_operations']/mixed_time:.1f}")
    print(f"- Threads completed: {sum(mixed_results)}/10")
    
    # Overall Assessment
    print("\n" + "=" * 50)
    print("LOAD AND STRESS TEST SUMMARY")
    print("=" * 50)
    
    overall_success_rate = (
        task_summary['success_rate'] + 
        log_summary['success_rate'] + 
        mixed_summary['success_rate']
    ) / 3
    
    total_operations = (
        task_summary['total_operations'] + 
        log_summary['total_operations'] + 
        mixed_summary['total_operations']
    )
    
    total_time = task_time + log_time + mixed_time
    overall_throughput = total_operations / total_time
    
    print(f"Overall Results:")
    print(f"- Total operations: {total_operations}")
    print(f"- Average success rate: {overall_success_rate:.1f}%")
    print(f"- Overall throughput: {overall_throughput:.1f} ops/sec")
    print(f"- Total test time: {total_time:.2f} seconds")
    
    # Performance criteria
    success_threshold = 95.0  # 95% success rate
    throughput_threshold = 50.0  # 50 operations per second
    
    performance_pass = (
        overall_success_rate >= success_threshold and
        overall_throughput >= throughput_threshold
    )
    
    if performance_pass:
        print("\n✅ LOAD AND STRESS TESTS PASSED!")
        print("System demonstrates good performance under load")
    else:
        print("\n❌ LOAD AND STRESS TESTS FAILED!")
        if overall_success_rate < success_threshold:
            print(f"- Success rate below threshold: {overall_success_rate:.1f}% < {success_threshold}%")
        if overall_throughput < throughput_threshold:
            print(f"- Throughput below threshold: {overall_throughput:.1f} < {throughput_threshold} ops/sec")
    
    return performance_pass

if __name__ == "__main__":
    success = run_load_stress_tests()
    sys.exit(0 if success else 1)