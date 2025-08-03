#!/usr/bin/env python3
"""
Quality check script for Windows Scheduler GUI project.
Run all code quality tools in sequence.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Run all quality checks."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    tests_path = project_root / "tests"
    
    # Only check our new scheduler GUI files
    scheduler_files = "src/models/ src/core/interfaces.py src/utils/"
    
    checks = [
        (f"uv run black --check {scheduler_files}", "Code formatting check (Black)"),
        (f"uv run flake8 {scheduler_files}", "Code linting (Flake8)"),
        (f"uv run mypy {scheduler_files}", "Type checking (MyPy)"),
        ("uv run pytest tests/ -v", "Unit tests (Pytest)"),
    ]
    
    print("🚀 Starting quality checks for Windows Scheduler GUI")
    print(f"Project root: {project_root}")
    print(f"Source path: {src_path}")
    print(f"Tests path: {tests_path}")
    
    passed = 0
    failed = 0
    
    for command, description in checks:
        if run_command(command, description):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print("📊 Quality Check Summary")
    print(f"{'='*50}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All quality checks passed!")
        return 0
    else:
        print(f"\n💥 {failed} quality check(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())