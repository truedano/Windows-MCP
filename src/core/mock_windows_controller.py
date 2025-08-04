"""
Mock Windows controller for testing and development.
"""

import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.core.interfaces import IWindowsController
from src.models.execution import ExecutionResult
from src.models.data_models import App


class MockWindowsController(IWindowsController):
    """Mock implementation of Windows controller for testing."""
    
    def __init__(self):
        """Initialize mock controller."""
        self._mock_apps = [
            App(
                name="notepad",
                title="記事本",
                process_id=1234,
                window_handle=12345,
                is_visible=True,
                x=100, y=100, width=800, height=600
            ),
            App(
                name="calculator",
                title="小算盤",
                process_id=5678,
                window_handle=56789,
                is_visible=True,
                x=200, y=200, width=400, height=500
            ),
            App(
                name="chrome",
                title="Google Chrome",
                process_id=9012,
                window_handle=90123,
                is_visible=True,
                x=0, y=0, width=1024, height=768
            )
        ]
        
        # Simulate some randomness in operations
        self._failure_rate = 0.1  # 10% chance of failure
        self._delay_range = (0.1, 1.0)  # Random delay between operations
    
    def _simulate_delay(self) -> None:
        """Simulate operation delay."""
        delay = random.uniform(*self._delay_range)
        time.sleep(delay)
    
    def _should_fail(self) -> bool:
        """Determine if operation should fail randomly."""
        return random.random() < self._failure_rate
    
    def get_running_apps(self) -> List[App]:
        """Get list of currently running applications."""
        self._simulate_delay()
        return self._mock_apps.copy()
    
    def launch_app(self, app_name: str) -> ExecutionResult:
        """Launch an application."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "launch_app",
                app_name,
                f"Failed to launch {app_name}: Application not found"
            )
        
        # Check if app is already running
        existing_app = next((app for app in self._mock_apps if app.name == app_name), None)
        if existing_app:
            return ExecutionResult.success_result(
                "launch_app",
                app_name,
                f"Application {app_name} is already running"
            )
        
        # Add new app to running apps
        new_app = App(
            name=app_name,
            title=f"Mock {app_name}",
            pid=random.randint(10000, 99999),
            window_handle=random.randint(100000, 999999),
            is_visible=True,
            x=random.randint(0, 500),
            y=random.randint(0, 300),
            width=800,
            height=600
        )
        self._mock_apps.append(new_app)
        
        return ExecutionResult.success_result(
            "launch_app",
            app_name,
            f"Successfully launched {app_name}"
        )
    
    def close_app(self, app_name: str) -> ExecutionResult:
        """Close an application."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "close_app",
                app_name,
                f"Failed to close {app_name}: Access denied"
            )
        
        # Find and remove app
        app_to_remove = None
        for app in self._mock_apps:
            if app.name == app_name:
                app_to_remove = app
                break
        
        if app_to_remove:
            self._mock_apps.remove(app_to_remove)
            return ExecutionResult.success_result(
                "close_app",
                app_name,
                f"Successfully closed {app_name}"
            )
        else:
            return ExecutionResult.failure_result(
                "close_app",
                app_name,
                f"Application {app_name} not found"
            )
    
    def resize_window(self, app_name: str, width: int, height: int) -> ExecutionResult:
        """Resize application window."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "resize_window",
                app_name,
                f"Failed to resize {app_name}: Window not accessible"
            )
        
        # Find app and update dimensions
        for app in self._mock_apps:
            if app.name == app_name:
                app.width = width
                app.height = height
                return ExecutionResult.success_result(
                    "resize_window",
                    app_name,
                    f"Resized {app_name} to {width}x{height}"
                )
        
        return ExecutionResult.failure_result(
            "resize_window",
            app_name,
            f"Application {app_name} not found"
        )
    
    def move_window(self, app_name: str, x: int, y: int) -> ExecutionResult:
        """Move application window."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "move_window",
                app_name,
                f"Failed to move {app_name}: Window not accessible"
            )
        
        # Find app and update position
        for app in self._mock_apps:
            if app.name == app_name:
                app.x = x
                app.y = y
                return ExecutionResult.success_result(
                    "move_window",
                    app_name,
                    f"Moved {app_name} to ({x}, {y})"
                )
        
        return ExecutionResult.failure_result(
            "move_window",
            app_name,
            f"Application {app_name} not found"
        )
    
    def minimize_window(self, app_name: str) -> ExecutionResult:
        """Minimize application window."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "minimize_window",
                app_name,
                f"Failed to minimize {app_name}: Window not accessible"
            )
        
        # Find app and set visibility
        for app in self._mock_apps:
            if app.name == app_name:
                app.is_visible = False
                return ExecutionResult.success_result(
                    "minimize_window",
                    app_name,
                    f"Minimized {app_name}"
                )
        
        return ExecutionResult.failure_result(
            "minimize_window",
            app_name,
            f"Application {app_name} not found"
        )
    
    def maximize_window(self, app_name: str) -> ExecutionResult:
        """Maximize application window."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "maximize_window",
                app_name,
                f"Failed to maximize {app_name}: Window not accessible"
            )
        
        # Find app and set to full screen
        for app in self._mock_apps:
            if app.name == app_name:
                app.x = 0
                app.y = 0
                app.width = 1920
                app.height = 1080
                app.is_visible = True
                return ExecutionResult.success_result(
                    "maximize_window",
                    app_name,
                    f"Maximized {app_name}"
                )
        
        return ExecutionResult.failure_result(
            "maximize_window",
            app_name,
            f"Application {app_name} not found"
        )
    
    def focus_window(self, app_name: str) -> ExecutionResult:
        """Focus application window."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "focus_window",
                app_name,
                f"Failed to focus {app_name}: Window not accessible"
            )
        
        # Find app and set visible
        for app in self._mock_apps:
            if app.name == app_name:
                app.is_visible = True
                return ExecutionResult.success_result(
                    "focus_window",
                    app_name,
                    f"Focused {app_name}"
                )
        
        return ExecutionResult.failure_result(
            "focus_window",
            app_name,
            f"Application {app_name} not found"
        )
    
    def click_element(self, app_name: str, x: int, y: int) -> ExecutionResult:
        """Click on element in application window."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "click_element",
                app_name,
                f"Failed to click in {app_name}: Element not found"
            )
        
        # Check if app exists
        app_exists = any(app.name == app_name for app in self._mock_apps)
        if not app_exists:
            return ExecutionResult.failure_result(
                "click_element",
                app_name,
                f"Application {app_name} not found"
            )
        
        return ExecutionResult.success_result(
            "click_element",
            app_name,
            f"Clicked at ({x}, {y}) in {app_name}"
        )
    
    def type_text(self, app_name: str, text: str, x: int, y: int) -> ExecutionResult:
        """Type text at specific location in application window."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "type_text",
                app_name,
                f"Failed to type in {app_name}: Input field not accessible"
            )
        
        # Check if app exists
        app_exists = any(app.name == app_name for app in self._mock_apps)
        if not app_exists:
            return ExecutionResult.failure_result(
                "type_text",
                app_name,
                f"Application {app_name} not found"
            )
        
        return ExecutionResult.success_result(
            "type_text",
            app_name,
            f"Typed '{text}' at ({x}, {y}) in {app_name}"
        )
    
    def send_keys(self, keys: List[str]) -> ExecutionResult:
        """Send keyboard shortcuts."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "send_keys",
                "system",
                f"Failed to send keys: {'+'.join(keys)}"
            )
        
        return ExecutionResult.success_result(
            "send_keys",
            "system",
            f"Sent keys: {'+'.join(keys)}"
        )
    
    def execute_powershell_command(self, command: str) -> ExecutionResult:
        """Execute custom PowerShell command."""
        self._simulate_delay()
        
        if self._should_fail():
            return ExecutionResult.failure_result(
                "execute_powershell",
                "system",
                f"PowerShell command failed: {command}"
            )
        
        # Simulate some common commands
        if "Get-Process" in command:
            output = "Mock process list output"
        elif "Get-Service" in command:
            output = "Mock service list output"
        else:
            output = f"Mock output for: {command}"
        
        return ExecutionResult.success_result(
            "execute_powershell",
            "system",
            f"PowerShell command executed successfully",
            details={"output": output, "command": command}
        )
    
    def get_app_state(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Get current state of application."""
        self._simulate_delay()
        
        # Find app
        for app in self._mock_apps:
            if app.name == app_name:
                return {
                    "name": app.name,
                    "title": app.title,
                    "pid": app.pid,
                    "window_handle": app.window_handle,
                    "is_visible": app.is_visible,
                    "position": {"x": app.x, "y": app.y},
                    "size": {"width": app.width, "height": app.height},
                    "state": "running"
                }
        
        return None
    
    def set_failure_rate(self, rate: float) -> None:
        """Set the failure rate for testing purposes."""
        self._failure_rate = max(0.0, min(1.0, rate))
    
    def set_delay_range(self, min_delay: float, max_delay: float) -> None:
        """Set the delay range for testing purposes."""
        self._delay_range = (min_delay, max_delay)