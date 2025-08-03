"""
Window State Manager for tracking and managing window states.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import time

from .windows_controller import WindowsController
from ..models.data_models import App
from ..models.execution import ExecutionResult


class WindowStateManager:
    """
    Manages window states and provides advanced window control functionality.
    
    This class extends the basic WindowsController functionality with:
    - Window state tracking and history
    - Batch window operations
    - Window state validation
    - Advanced window positioning and sizing
    """
    
    def __init__(self, controller: WindowsController):
        """
        Initialize the Window State Manager.
        
        Args:
            controller: WindowsController instance to use for operations
        """
        self.controller = controller
        self._window_states: Dict[str, Dict[str, Any]] = {}
        self._state_history: Dict[str, List[Dict[str, Any]]] = {}
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = 5.0  # seconds
    
    def start_monitoring(self, interval: float = 5.0) -> bool:
        """
        Start monitoring window states.
        
        Args:
            interval: Monitoring interval in seconds
            
        Returns:
            bool: True if monitoring started successfully
        """
        if self._monitoring:
            return False
        
        self._monitor_interval = interval
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        return True
    
    def stop_monitoring(self) -> bool:
        """
        Stop monitoring window states.
        
        Returns:
            bool: True if monitoring stopped successfully
        """
        if not self._monitoring:
            return False
        
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        return True
    
    def get_window_state_history(self, app_name: str) -> List[Dict[str, Any]]:
        """
        Get the state history for a specific application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            List[Dict[str, Any]]: List of historical states
        """
        return self._state_history.get(app_name, [])
    
    def get_current_window_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current states of all tracked windows.
        
        Returns:
            Dict[str, Dict[str, Any]]: Current window states
        """
        return self._window_states.copy()
    
    def restore_window_state(self, app_name: str, target_state: Dict[str, Any]) -> ExecutionResult:
        """
        Restore a window to a specific state.
        
        Args:
            app_name: Name of the application
            target_state: Target state to restore to
            
        Returns:
            ExecutionResult: Result of the restore operation
        """
        try:
            # Get current state
            current_state = self.controller.get_app_state(app_name)
            if not current_state:
                return ExecutionResult.failure_result(
                    operation="restore_window_state",
                    target=app_name,
                    message=f"Application {app_name} not found"
                )
            
            # Restore position if specified
            if 'position' in target_state:
                pos = target_state['position']
                move_result = self.controller.move_window(app_name, pos['x'], pos['y'])
                if not move_result.success:
                    return move_result
            
            # Restore size if specified
            if 'size' in target_state:
                size = target_state['size']
                resize_result = self.controller.resize_window(app_name, size['width'], size['height'])
                if not resize_result.success:
                    return resize_result
            
            # Restore visibility state if specified
            if 'is_visible' in target_state:
                if target_state['is_visible']:
                    focus_result = self.controller.focus_window(app_name)
                    if not focus_result.success:
                        return focus_result
                else:
                    minimize_result = self.controller.minimize_window(app_name)
                    if not minimize_result.success:
                        return minimize_result
            
            return ExecutionResult.success_result(
                operation="restore_window_state",
                target=app_name,
                message=f"Successfully restored window state for {app_name}"
            )
            
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="restore_window_state",
                target=app_name,
                message=f"Exception occurred while restoring window state: {str(e)}",
                details={"exception": str(e), "target_state": target_state}
            )
    
    def batch_window_operations(self, operations: List[Dict[str, Any]]) -> List[ExecutionResult]:
        """
        Execute multiple window operations in batch.
        
        Args:
            operations: List of operation dictionaries with 'action', 'app_name', and 'params'
            
        Returns:
            List[ExecutionResult]: Results of all operations
        """
        results = []
        
        for operation in operations:
            try:
                action = operation.get('action')
                app_name = operation.get('app_name', '')
                params = operation.get('params', {})
                
                if action == 'launch':
                    result = self.controller.launch_app(app_name)
                elif action == 'close':
                    result = self.controller.close_app(app_name)
                elif action == 'resize':
                    result = self.controller.resize_window(
                        app_name, params.get('width', 800), params.get('height', 600)
                    )
                elif action == 'move':
                    result = self.controller.move_window(
                        app_name, params.get('x', 0), params.get('y', 0)
                    )
                elif action == 'minimize':
                    result = self.controller.minimize_window(app_name)
                elif action == 'maximize':
                    result = self.controller.maximize_window(app_name)
                elif action == 'focus':
                    result = self.controller.focus_window(app_name)
                else:
                    result = ExecutionResult.failure_result(
                        operation="batch_operation",
                        target=app_name,
                        message=f"Unknown action: {action}"
                    )
                
                results.append(result)
                
            except Exception as e:
                result = ExecutionResult.failure_result(
                    operation="batch_operation",
                    target=operation.get('app_name', 'unknown'),
                    message=f"Exception in batch operation: {str(e)}",
                    details={"exception": str(e), "operation": operation}
                )
                results.append(result)
        
        return results
    
    def arrange_windows_grid(self, app_names: List[str], grid_rows: int, grid_cols: int) -> List[ExecutionResult]:
        """
        Arrange multiple windows in a grid layout.
        
        Args:
            app_names: List of application names to arrange
            grid_rows: Number of rows in the grid
            grid_cols: Number of columns in the grid
            
        Returns:
            List[ExecutionResult]: Results of arrangement operations
        """
        results = []
        
        if len(app_names) > grid_rows * grid_cols:
            result = ExecutionResult.failure_result(
                operation="arrange_windows_grid",
                target="multiple",
                message=f"Too many windows ({len(app_names)}) for grid ({grid_rows}x{grid_cols})"
            )
            return [result]
        
        try:
            # Get screen dimensions (assume 1920x1080 for now)
            screen_width = 1920
            screen_height = 1080
            
            # Calculate window dimensions
            window_width = screen_width // grid_cols
            window_height = screen_height // grid_rows
            
            # Arrange windows
            for i, app_name in enumerate(app_names):
                row = i // grid_cols
                col = i % grid_cols
                
                x = col * window_width
                y = row * window_height
                
                # Resize and move window
                resize_result = self.controller.resize_window(app_name, window_width, window_height)
                results.append(resize_result)
                
                if resize_result.success:
                    move_result = self.controller.move_window(app_name, x, y)
                    results.append(move_result)
        
        except Exception as e:
            result = ExecutionResult.failure_result(
                operation="arrange_windows_grid",
                target="multiple",
                message=f"Exception occurred during grid arrangement: {str(e)}",
                details={"exception": str(e)}
            )
            results.append(result)
        
        return results
    
    def validate_window_state(self, app_name: str, expected_state: Dict[str, Any]) -> bool:
        """
        Validate that a window is in the expected state.
        
        Args:
            app_name: Name of the application
            expected_state: Expected state to validate against
            
        Returns:
            bool: True if window state matches expectations
        """
        try:
            current_state = self.controller.get_app_state(app_name)
            if not current_state:
                return False
            
            # Check position if specified
            if 'position' in expected_state:
                expected_pos = expected_state['position']
                current_pos = current_state['position']
                if (abs(current_pos['x'] - expected_pos['x']) > 10 or 
                    abs(current_pos['y'] - expected_pos['y']) > 10):
                    return False
            
            # Check size if specified
            if 'size' in expected_state:
                expected_size = expected_state['size']
                current_size = current_state['size']
                if (abs(current_size['width'] - expected_size['width']) > 10 or 
                    abs(current_size['height'] - expected_size['height']) > 10):
                    return False
            
            # Check visibility if specified
            if 'is_visible' in expected_state:
                if current_state['is_visible'] != expected_state['is_visible']:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        while self._monitoring:
            try:
                # Get current running apps
                running_apps = self.controller.get_running_apps()
                current_time = datetime.now()
                
                # Update states for each app
                for app in running_apps:
                    app_name = app.name
                    
                    # Create state snapshot
                    state = {
                        'timestamp': current_time,
                        'name': app.name,
                        'title': app.title,
                        'process_id': app.process_id,
                        'is_visible': app.is_visible,
                        'position': {'x': app.x, 'y': app.y},
                        'size': {'width': app.width, 'height': app.height}
                    }
                    
                    # Update current state
                    self._window_states[app_name] = state
                    
                    # Add to history
                    if app_name not in self._state_history:
                        self._state_history[app_name] = []
                    
                    self._state_history[app_name].append(state)
                    
                    # Limit history size (keep last 100 entries)
                    if len(self._state_history[app_name]) > 100:
                        self._state_history[app_name] = self._state_history[app_name][-100:]
                
                # Clean up states for apps that are no longer running
                current_app_names = {app.name for app in running_apps}
                for app_name in list(self._window_states.keys()):
                    if app_name not in current_app_names:
                        del self._window_states[app_name]
                
            except Exception:
                # Continue monitoring even if there's an error
                pass
            
            # Wait for next monitoring cycle
            time.sleep(self._monitor_interval)