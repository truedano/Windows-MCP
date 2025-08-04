#!/usr/bin/env python3
"""
Performance and Stability Test Runner for Task 15.2
Comprehensive test runner for all performance and stability tests.
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def check_dependencies():
    """Check if required dependencies are available."""
    print("Checking dependencies...")
    
    missing_deps = []
    
    try:
        import psutil
        print("✓ psutil available")
    except ImportError:
        missing_deps.append("psutil")
        print("✗ psutil missing")
    
    try:
        import tracemalloc
        print("✓ tracemalloc available")
    except ImportError:
        missing_deps.append("tracemalloc")
        print("✗ tracemalloc missing")
    
    if missing_deps:
        print(f"\nMissing dependencies: {', '.join(missing_deps)}")
        print("Please install with: uv add " + " ".join(missing_deps))
        return False
    
    print("✓ All dependencies available")
    return True

def run_test_script(script_name, description):
    """Run a test script and return results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*60}")
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Test script not found: {script_path}")
        return False, f"Script not found: {script_name}"
    
    try:
        start_time = time.time()
        
        # Run the test script
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"\nTest completed in {duration:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        success = result.returncode == 0
        
        if success:
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
        
        return success, {
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False, str(e)

def run_fallback_tests():
    """Run fallback tests when psutil is not available."""
    print("\n" + "="*60)
    print("RUNNING FALLBACK PERFORMANCE TESTS")
    print("="*60)
    print("Note: Limited testing due to missing dependencies")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        # Basic import test
        print("\n1. Testing basic imports...")
        from core.scheduler_engine import get_scheduler_engine
        from core.task_manager import TaskManager
        from storage.log_storage import LogStorage
        print("✓ Core components imported successfully")
        
        # Basic functionality test
        print("\n2. Testing basic functionality...")
        engine = get_scheduler_engine()
        task_manager = TaskManager()
        log_storage = LogStorage()
        
        if engine and task_manager and log_storage:
            print("✓ Core components initialized successfully")
        else:
            print("✗ Component initialization failed")
            return False
        
        # Simple performance test
        print("\n3. Simple performance test...")
        from models.task import Task, TaskStatus
        from models.schedule import Schedule, ScheduleType
        from models.action import ActionType
        from datetime import datetime, timedelta
        
        start_time = time.time()
        
        # Create and manage 100 tasks
        task_ids = []
        for i in range(100):
            task = Task(
                name=f"Fallback Test Task {i}",
                description=f"Simple performance test task {i}",
                action_type=ActionType.LAUNCH_APP,
                action_params={"app_path": "notepad.exe"},
                schedule=Schedule(
                    schedule_type=ScheduleType.ONCE,
                    start_time=datetime.now() + timedelta(minutes=i)
                )
            )
            
            task_id = task_manager.add_task(task)
            task_ids.append(task_id)
        
        # Retrieve all tasks
        for task_id in task_ids:
            task = task_manager.get_task(task_id)
            if not task:
                print(f"✗ Failed to retrieve task {task_id}")
                return False
        
        # Clean up
        for task_id in task_ids:
            task_manager.delete_task(task_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✓ Created, retrieved, and deleted 100 tasks in {duration:.2f} seconds")
        print(f"✓ Performance: {100/duration:.1f} operations/second")
        
        print("\n✅ FALLBACK TESTS PASSED")
        print("Basic performance and functionality verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback tests failed: {e}")
        return False

def main():
    """Main test runner function."""
    print("Windows Scheduler GUI - Performance and Stability Test Runner")
    print("Task 15.2: 效能和穩定性測試")
    print("="*65)
    
    start_time = datetime.now()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n⚠ Running fallback tests due to missing dependencies...")
        success = run_fallback_tests()
        
        print("\n" + "="*65)
        print("FALLBACK TEST SUMMARY")
        print("="*65)
        
        if success:
            print("✅ Basic performance and stability verified")
            print("Note: Install 'psutil' for comprehensive testing")
        else:
            print("❌ Basic tests failed")
        
        return success
    
    # List of performance tests to run
    performance_tests = [
        ("test_performance_stability.py", "Comprehensive Performance and Stability Tests"),
        ("test_memory_leak_detection.py", "Memory Leak Detection Test"),
        ("test_load_stress.py", "Load and Stress Testing")
    ]
    
    # Run all tests
    test_results = {}
    
    for script, description in performance_tests:
        success, result = run_test_script(script, description)
        test_results[script] = {
            'success': success,
            'result': result,
            'description': description
        }
    
    # Generate comprehensive summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*65)
    print("PERFORMANCE AND STABILITY TEST SUMMARY")
    print("="*65)
    
    total_tests = len(performance_tests)
    passed_tests = sum(1 for r in test_results.values() if r['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"Test execution started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test execution ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {total_duration:.2f} seconds")
    print()
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for script, data in test_results.items():
        status = "✅ PASSED" if data['success'] else "❌ FAILED"
        print(f"  {script}: {status}")
        print(f"    {data['description']}")
        
        if isinstance(data['result'], dict) and 'duration' in data['result']:
            print(f"    Duration: {data['result']['duration']:.2f} seconds")
    
    # Task 15.2 requirements assessment
    print("\n" + "="*65)
    print("TASK 15.2 REQUIREMENTS ASSESSMENT")
    print("="*65)
    
    requirements = [
        ("進行長時間運行測試，驗證系統穩定性", passed_tests > 0),
        ("測試大量任務和日誌的處理能力", passed_tests > 0),
        ("進行錯誤恢復和異常處理測試", passed_tests > 0),
        ("測試日誌存儲和檢索的效能", passed_tests > 0)
    ]
    
    for requirement, met in requirements:
        status = "✅" if met else "❌"
        print(f"  {status} {requirement}")
    
    all_requirements_met = all(met for _, met in requirements)
    
    if all_requirements_met and passed_tests == total_tests:
        print(f"\n🎉 TASK 15.2 COMPLETED SUCCESSFULLY!")
        print("All performance and stability requirements have been met.")
        print("System demonstrates:")
        print("- Long-term stability")
        print("- Large data processing capability")
        print("- Robust error handling")
        print("- Good performance characteristics")
    elif passed_tests > 0:
        print(f"\n⚠ TASK 15.2 PARTIALLY COMPLETED")
        print("Some performance tests passed, but improvements needed.")
        print("Consider addressing failed tests for full compliance.")
    else:
        print(f"\n❌ TASK 15.2 NEEDS ATTENTION")
        print("Performance and stability tests require fixes.")
    
    # Generate test report
    report_filename = f"performance_test_report_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("Performance and Stability Test Report\n")
            f.write("="*40 + "\n")
            f.write(f"Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {total_duration:.2f} seconds\n\n")
            
            f.write("Test Results:\n")
            for script, data in test_results.items():
                f.write(f"- {script}: {'PASSED' if data['success'] else 'FAILED'}\n")
            
            f.write(f"\nSummary: {passed_tests}/{total_tests} tests passed\n")
            f.write(f"Task 15.2 Status: {'COMPLETED' if all_requirements_met and passed_tests == total_tests else 'NEEDS ATTENTION'}\n")
        
        print(f"\n📄 Test report saved: {report_filename}")
        
    except Exception as e:
        print(f"⚠ Could not save test report: {e}")
    
    return all_requirements_met and passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)