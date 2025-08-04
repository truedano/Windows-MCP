#!/usr/bin/env python3
"""
Memory Leak Detection Test for Windows Scheduler GUI
Specialized test for detecting memory leaks during long-term operation.
"""

import sys
import os
import gc
import psutil
import time
import threading
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class MemoryLeakDetector:
    """Memory leak detection utility."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()
        self.memory_samples = []
        self.monitoring = False
        self.monitor_thread = None
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def start_monitoring(self, interval=1.0):
        """Start memory monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_memory, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def _monitor_memory(self, interval):
        """Monitor memory usage in background."""
        while self.monitoring:
            memory_usage = self.get_memory_usage()
            timestamp = time.time()
            self.memory_samples.append((timestamp, memory_usage))
            time.sleep(interval)
    
    def analyze_leak(self):
        """Analyze memory samples for potential leaks."""
        if len(self.memory_samples) < 10:
            return False, "Insufficient data for analysis"
        
        # Calculate memory trend
        start_memory = self.memory_samples[0][1]
        end_memory = self.memory_samples[-1][1]
        memory_increase = end_memory - start_memory
        
        # Calculate average increase rate
        total_time = self.memory_samples[-1][0] - self.memory_samples[0][0]
        increase_rate = memory_increase / total_time if total_time > 0 else 0
        
        # Check for consistent upward trend
        upward_samples = 0
        for i in range(1, len(self.memory_samples)):
            if self.memory_samples[i][1] > self.memory_samples[i-1][1]:
                upward_samples += 1
        
        upward_ratio = upward_samples / (len(self.memory_samples) - 1)
        
        # Leak detection criteria
        significant_increase = memory_increase > 50  # More than 50MB increase
        consistent_growth = upward_ratio > 0.7  # More than 70% upward trend
        high_rate = increase_rate > 1.0  # More than 1MB per second
        
        is_leak = significant_increase and (consistent_growth or high_rate)
        
        analysis = {
            'total_increase': memory_increase,
            'increase_rate': increase_rate,
            'upward_ratio': upward_ratio,
            'duration': total_time,
            'sample_count': len(self.memory_samples)
        }
        
        return is_leak, analysis

def test_memory_leak_detection():
    """Test for memory leaks in core components."""
    print("Memory Leak Detection Test")
    print("=" * 30)
    
    detector = MemoryLeakDetector()
    print(f"Initial memory usage: {detector.initial_memory:.2f} MB")
    
    try:
        # Start memory monitoring
        detector.start_monitoring(interval=0.5)
        
        # Import and initialize components
        from core.scheduler_engine import get_scheduler_engine
        from core.task_manager import TaskManager
        from storage.log_storage import LogStorage
        from models.task import Task, TaskStatus
        from models.schedule import Schedule, ScheduleType
        from models.action import ActionType
        from models.execution import ExecutionLog, ExecutionStatus
        
        print("Components imported, starting leak test...")
        
        # Initialize components
        engine = get_scheduler_engine()
        task_manager = TaskManager()
        log_storage = LogStorage()
        
        # Perform repetitive operations that might cause leaks
        test_duration = 20  # seconds
        start_time = time.time()
        iteration = 0
        
        print(f"Running operations for {test_duration} seconds...")
        
        while time.time() - start_time < test_duration:
            iteration += 1
            
            # Create and delete tasks
            task = Task(
                name=f"Leak Test Task {iteration}",
                description=f"Memory leak test iteration {iteration}",
                action_type=ActionType.LAUNCH_APP,
                action_params={"app_path": "notepad.exe"},
                schedule=Schedule(
                    schedule_type=ScheduleType.ONCE,
                    start_time=datetime.now() + timedelta(seconds=30)
                )
            )
            
            task_id = task_manager.add_task(task)
            retrieved_task = task_manager.get_task(task_id)
            task_manager.delete_task(task_id)
            
            # Create and delete logs
            log = ExecutionLog(
                task_id=f"leak_test_{iteration}",
                task_name=f"Leak Test Task {iteration}",
                execution_time=datetime.now(),
                status=ExecutionStatus.SUCCESS,
                message=f"Memory leak test log {iteration}"
            )
            
            log_id = log_storage.add_log(log)
            retrieved_log = log_storage.get_log(log_id)
            log_storage.delete_log(log_id)
            
            # Force garbage collection periodically
            if iteration % 50 == 0:
                gc.collect()
                current_memory = detector.get_memory_usage()
                print(f"  Iteration {iteration}: {current_memory:.2f} MB")
            
            # Brief pause
            time.sleep(0.01)
        
        print(f"Completed {iteration} iterations")
        
        # Stop monitoring and analyze
        time.sleep(2)  # Allow final samples
        detector.stop_monitoring()
        
        is_leak, analysis = detector.analyze_leak()
        
        print("\nMemory Analysis Results:")
        print(f"- Total memory increase: {analysis['total_increase']:.2f} MB")
        print(f"- Increase rate: {analysis['increase_rate']:.2f} MB/sec")
        print(f"- Upward trend ratio: {analysis['upward_ratio']:.2f}")
        print(f"- Test duration: {analysis['duration']:.2f} seconds")
        print(f"- Memory samples: {analysis['sample_count']}")
        
        if is_leak:
            print("❌ POTENTIAL MEMORY LEAK DETECTED!")
            return False
        else:
            print("✅ No significant memory leak detected")
            return True
            
    except Exception as e:
        print(f"❌ Memory leak test failed: {e}")
        return False
    finally:
        detector.stop_monitoring()
        
        # Final cleanup
        gc.collect()
        final_memory = detector.get_memory_usage()
        total_increase = final_memory - detector.initial_memory
        print(f"Final memory usage: {final_memory:.2f} MB (+{total_increase:.2f} MB)")

if __name__ == "__main__":
    success = test_memory_leak_detection()
    sys.exit(0 if success else 1)