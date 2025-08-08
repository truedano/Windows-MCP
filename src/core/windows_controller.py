"""
Windows Controller implementation for integrating with Windows-MCP functionality.
"""

import subprocess
import json
import psutil
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from .interfaces import IWindowsController
from ..models.execution import ExecutionResult
from ..models.data_models import App
from ..models.action import ActionType


class WindowsController(IWindowsController):
    """
    Windows controller that integrates Windows-MCP functionality for application control.
    
    This class provides methods to interact with Windows applications using the same
    tools available in the Windows-MCP project.
    """
    
    def __init__(self):
        """Initialize the Windows controller."""
        self._last_scan_time = None
        self._cached_apps = []
        self._cache_duration = 5  # seconds
    
    def get_running_apps(self) -> List[App]:
        """
        Get list of currently running applications.
        
        Returns:
            List[App]: List of running applications with their details
        """
        try:
            # Use cache if recent scan available
            current_time = time.time()
            if (self._last_scan_time and 
                current_time - self._last_scan_time < self._cache_duration):
                return self._cached_apps.copy()
            
            apps = []
            
            # Get all processes with window titles
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] and proc_info['exe']:
                        # Try to get window information using PowerShell
                        window_info = self._get_window_info(proc_info['pid'])
                        
                        if window_info and window_info.get('title'):
                            app = App(
                                name=proc_info['name'],
                                title=window_info['title'],
                                process_id=proc_info['pid'],
                                window_handle=window_info.get('handle'),
                                is_visible=window_info.get('visible', True),
                                x=window_info.get('x', 0),
                                y=window_info.get('y', 0),
                                width=window_info.get('width', 0),
                                height=window_info.get('height', 0)
                            )
                            apps.append(app)
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Update cache
            self._cached_apps = apps
            self._last_scan_time = current_time
            
            return apps.copy()
            
        except Exception as e:
            return []
    
    def launch_app(self, app_name: str) -> ExecutionResult:
        """
        Launch an application using Windows-MCP Launch-Tool functionality.
        
        Args:
            app_name: Name of the application to launch
            
        Returns:
            ExecutionResult: Result of the launch operation
        """
        try:
            # Use PowerShell to launch application
            # Try direct launch first, then fallback to Start Apps search
            powershell_cmd = f"""
            try {{
                Start-Process "{app_name}" -ErrorAction Stop
                Write-Output "SUCCESS: Launched {app_name}"
            }} catch {{
                # Try to find in Start Apps if direct launch fails
                try {{
                    $app = Get-StartApps | Where-Object {{$_.Name -like "*{app_name}*"}} | Select-Object -First 1
                    if ($app) {{
                        Start-Process -FilePath $app.AppID -ErrorAction Stop
                        Write-Output "SUCCESS: Launched $($app.Name)"
                    }} else {{
                        Write-Output "ERROR: Could not find or launch {app_name}"
                    }}
                }} catch {{
                    Write-Output "ERROR: Could not find or launch {app_name}"
                }}
            }}
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="launch_app",
                    target=app_name,
                    message=f"Successfully launched {app_name}"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="launch_app",
                    target=app_name,
                    message=f"Failed to launch {app_name}: {result}",
                    details={"powershell_output": result}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="launch_app",
                target=app_name,
                message=f"Exception occurred while launching {app_name}: {str(e)}",
                details={"exception": str(e)}
            )
    
    def close_app(self, app_name: str) -> ExecutionResult:
        """
        Close an application by name.
        
        Args:
            app_name: Name of the application to close
            
        Returns:
            ExecutionResult: Result of the close operation
        """
        try:
            # Find the process by name
            closed_processes = []
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == app_name.lower() or app_name.lower() in proc.info['name'].lower():
                        proc.terminate()
                        closed_processes.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_processes:
                # Wait a moment for graceful termination
                time.sleep(1)
                
                # Force kill if still running
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if (proc.info['name'].lower() == app_name.lower() or 
                            app_name.lower() in proc.info['name'].lower()):
                            if proc.info['pid'] in closed_processes:
                                proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return ExecutionResult.success_result(
                    operation="close_app",
                    target=app_name,
                    message=f"Successfully closed {app_name} (PIDs: {closed_processes})"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="close_app",
                    target=app_name,
                    message=f"No running processes found for {app_name}"
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="close_app",
                target=app_name,
                message=f"Exception occurred while closing {app_name}: {str(e)}",
                details={"exception": str(e)}
            )
    
    def resize_window(self, app_name: str, width: int, height: int) -> ExecutionResult:
        """
        Resize application window using Windows-MCP Resize-Tool functionality.
        
        Args:
            app_name: Name of the application
            width: New window width
            height: New window height
            
        Returns:
            ExecutionResult: Result of the resize operation
        """
        try:
            # Use PowerShell to resize window (mimics Windows-MCP Resize-Tool)
            powershell_cmd = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
                    [DllImport("user32.dll")]
                    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
                    [DllImport("user32.dll")]
                    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                    public struct RECT {{ public int Left; public int Top; public int Right; public int Bottom; }}
                }}
"@

            $processes = Get-Process | Where-Object {{$_.ProcessName -like "*{app_name}*" -and $_.MainWindowTitle -ne ""}}
            if ($processes) {{
                $process = $processes[0]
                $hwnd = $process.MainWindowHandle
                if ($hwnd -ne [IntPtr]::Zero) {{
                    $rect = New-Object Win32+RECT
                    [Win32]::GetWindowRect($hwnd, [ref]$rect)
                    $x = $rect.Left
                    $y = $rect.Top
                    $result = [Win32]::SetWindowPos($hwnd, [IntPtr]::Zero, $x, $y, {width}, {height}, 0x0040)
                    if ($result) {{
                        Write-Output "SUCCESS: Resized window to {width}x{height}"
                    }} else {{
                        Write-Output "ERROR: Failed to resize window"
                    }}
                }} else {{
                    Write-Output "ERROR: No main window handle found"
                }}
            }} else {{
                Write-Output "ERROR: Process {app_name} not found or has no window"
            }}
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="resize_window",
                    target=app_name,
                    message=f"Successfully resized {app_name} window to {width}x{height}"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="resize_window",
                    target=app_name,
                    message=f"Failed to resize {app_name} window: {result}",
                    details={"powershell_output": result, "width": width, "height": height}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="resize_window",
                target=app_name,
                message=f"Exception occurred while resizing {app_name} window: {str(e)}",
                details={"exception": str(e), "width": width, "height": height}
            )
    
    def move_window(self, app_name: str, x: int, y: int) -> ExecutionResult:
        """
        Move application window to specified coordinates.
        
        Args:
            app_name: Name of the application
            x: New X coordinate
            y: New Y coordinate
            
        Returns:
            ExecutionResult: Result of the move operation
        """
        try:
            # Use PowerShell to move window
            powershell_cmd = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
                    [DllImport("user32.dll")]
                    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
                    [DllImport("user32.dll")]
                    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                    public struct RECT {{ public int Left; public int Top; public int Right; public int Bottom; }}
                }}
"@

            $processes = Get-Process | Where-Object {{$_.ProcessName -like "*{app_name}*" -and $_.MainWindowTitle -ne ""}}
            if ($processes) {{
                $process = $processes[0]
                $hwnd = $process.MainWindowHandle
                if ($hwnd -ne [IntPtr]::Zero) {{
                    $rect = New-Object Win32+RECT
                    [Win32]::GetWindowRect($hwnd, [ref]$rect)
                    $width = $rect.Right - $rect.Left
                    $height = $rect.Bottom - $rect.Top
                    $result = [Win32]::SetWindowPos($hwnd, [IntPtr]::Zero, {x}, {y}, $width, $height, 0x0040)
                    if ($result) {{
                        Write-Output "SUCCESS: Moved window to ({x}, {y})"
                    }} else {{
                        Write-Output "ERROR: Failed to move window"
                    }}
                }} else {{
                    Write-Output "ERROR: No main window handle found"
                }}
            }} else {{
                Write-Output "ERROR: Process {app_name} not found or has no window"
            }}
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="move_window",
                    target=app_name,
                    message=f"Successfully moved {app_name} window to ({x}, {y})"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="move_window",
                    target=app_name,
                    message=f"Failed to move {app_name} window: {result}",
                    details={"powershell_output": result, "x": x, "y": y}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="move_window",
                target=app_name,
                message=f"Exception occurred while moving {app_name} window: {str(e)}",
                details={"exception": str(e), "x": x, "y": y}
            )
    
    def minimize_window(self, app_name: str) -> ExecutionResult:
        """
        Minimize application window.
        
        Args:
            app_name: Name of the application
            
        Returns:
            ExecutionResult: Result of the minimize operation
        """
        try:
            powershell_cmd = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                }}
"@

            $processes = Get-Process | Where-Object {{$_.ProcessName -like "*{app_name}*" -and $_.MainWindowTitle -ne ""}}
            if ($processes) {{
                $process = $processes[0]
                $hwnd = $process.MainWindowHandle
                if ($hwnd -ne [IntPtr]::Zero) {{
                    $result = [Win32]::ShowWindow($hwnd, 2)  # SW_SHOWMINIMIZED
                    if ($result) {{
                        Write-Output "SUCCESS: Minimized window"
                    }} else {{
                        Write-Output "ERROR: Failed to minimize window"
                    }}
                }} else {{
                    Write-Output "ERROR: No main window handle found"
                }}
            }} else {{
                Write-Output "ERROR: Process {app_name} not found or has no window"
            }}
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="minimize_window",
                    target=app_name,
                    message=f"Successfully minimized {app_name} window"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="minimize_window",
                    target=app_name,
                    message=f"Failed to minimize {app_name} window: {result}",
                    details={"powershell_output": result}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="minimize_window",
                target=app_name,
                message=f"Exception occurred while minimizing {app_name} window: {str(e)}",
                details={"exception": str(e)}
            )
    
    def maximize_window(self, app_name: str) -> ExecutionResult:
        """
        Maximize application window.
        
        Args:
            app_name: Name of the application
            
        Returns:
            ExecutionResult: Result of the maximize operation
        """
        try:
            powershell_cmd = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                }}
"@

            $processes = Get-Process | Where-Object {{$_.ProcessName -like "*{app_name}*" -and $_.MainWindowTitle -ne ""}}
            if ($processes) {{
                $process = $processes[0]
                $hwnd = $process.MainWindowHandle
                if ($hwnd -ne [IntPtr]::Zero) {{
                    $result = [Win32]::ShowWindow($hwnd, 3)  # SW_SHOWMAXIMIZED
                    if ($result) {{
                        Write-Output "SUCCESS: Maximized window"
                    }} else {{
                        Write-Output "ERROR: Failed to maximize window"
                    }}
                }} else {{
                    Write-Output "ERROR: No main window handle found"
                }}
            }} else {{
                Write-Output "ERROR: Process {app_name} not found or has no window"
            }}
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="maximize_window",
                    target=app_name,
                    message=f"Successfully maximized {app_name} window"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="maximize_window",
                    target=app_name,
                    message=f"Failed to maximize {app_name} window: {result}",
                    details={"powershell_output": result}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="maximize_window",
                target=app_name,
                message=f"Exception occurred while maximizing {app_name} window: {str(e)}",
                details={"exception": str(e)}
            )
    
    def focus_window(self, app_name: str) -> ExecutionResult:
        """
        Bring application window to foreground.
        
        Args:
            app_name: Name of the application
            
        Returns:
            ExecutionResult: Result of the focus operation
        """
        try:
            powershell_cmd = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    public static extern bool SetForegroundWindow(IntPtr hWnd);
                    [DllImport("user32.dll")]
                    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                }}
"@

            $processes = Get-Process | Where-Object {{$_.ProcessName -like "*{app_name}*" -and $_.MainWindowTitle -ne ""}}
            if ($processes) {{
                $process = $processes[0]
                $hwnd = $process.MainWindowHandle
                if ($hwnd -ne [IntPtr]::Zero) {{
                    [Win32]::ShowWindow($hwnd, 1)  # SW_SHOWNORMAL
                    $result = [Win32]::SetForegroundWindow($hwnd)
                    if ($result) {{
                        Write-Output "SUCCESS: Focused window"
                    }} else {{
                        Write-Output "ERROR: Failed to focus window"
                    }}
                }} else {{
                    Write-Output "ERROR: No main window handle found"
                }}
            }} else {{
                Write-Output "ERROR: Process {app_name} not found or has no window"
            }}
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="focus_window",
                    target=app_name,
                    message=f"Successfully focused {app_name} window"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="focus_window",
                    target=app_name,
                    message=f"Failed to focus {app_name} window: {result}",
                    details={"powershell_output": result}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="focus_window",
                target=app_name,
                message=f"Exception occurred while focusing {app_name} window: {str(e)}",
                details={"exception": str(e)}
            )
    
    def execute_action(self, action_type: ActionType, params: Dict[str, Any]) -> ExecutionResult:
        """
        Execute a specific action based on action type and parameters.
        
        Args:
            action_type: Type of action to execute
            params: Parameters for the action
            
        Returns:
            ExecutionResult: Result of the action execution
        """
        try:
            if action_type == ActionType.LAUNCH_APP:
                return self.launch_app(params.get('app_name', ''))
            
            elif action_type == ActionType.CLOSE_APP:
                return self.close_app(params.get('app_name', ''))
            
            elif action_type == ActionType.RESIZE_WINDOW:
                return self.resize_window(
                    params.get('app_name', ''),
                    params.get('width', 800),
                    params.get('height', 600)
                )
            
            elif action_type == ActionType.MOVE_WINDOW:
                return self.move_window(
                    params.get('app_name', ''),
                    params.get('x', 0),
                    params.get('y', 0)
                )
            
            elif action_type == ActionType.MINIMIZE_WINDOW:
                return self.minimize_window(params.get('app_name', ''))
            
            elif action_type == ActionType.MAXIMIZE_WINDOW:
                return self.maximize_window(params.get('app_name', ''))
            
            elif action_type == ActionType.FOCUS_WINDOW:
                return self.focus_window(params.get('app_name', ''))
            
            elif action_type == ActionType.CLICK_ABS:
                return self.click_abs(
                    x=params.get('x', 0),
                    y=params.get('y', 0)
                )
            
            elif action_type == ActionType.TYPE_TEXT:
                return self.type_text(
                    params.get('app_name', ''),
                    params.get('text', ''),
                    params.get('x', 0),
                    params.get('y', 0)
                )
            
            elif action_type == ActionType.SEND_KEYS:
                return self.send_keys(params.get('keys', []))
            
            elif action_type == ActionType.CUSTOM_COMMAND:
                return self.execute_powershell_command(params.get('command', ''))
            
            # New action types from Windows-MCP
            elif action_type == ActionType.SWITCH_APP:
                return self.focus_window(params.get('app_name', ''))  # Same as focus_window
            
            elif action_type == ActionType.DRAG_ELEMENT:
                return self.drag_element(
                    params.get('app_name', ''),
                    params.get('from_x', 0),
                    params.get('from_y', 0),
                    params.get('to_x', 0),
                    params.get('to_y', 0)
                )
            
            elif action_type == ActionType.MOVE_MOUSE:
                return self.move_mouse(
                    params.get('x', 0),
                    params.get('y', 0)
                )
            
            elif action_type == ActionType.SCROLL:
                return self.scroll(
                    params.get('app_name', ''),
                    params.get('x', 0),
                    params.get('y', 0),
                    params.get('direction', 'down'),
                    params.get('scroll_type', 'vertical'),
                    params.get('wheel_times', 1)
                )
            
            elif action_type == ActionType.PRESS_KEY:
                return self.press_key(params.get('key', ''))
            
            elif action_type == ActionType.CLIPBOARD_COPY:
                return self.clipboard_copy(params.get('text', ''))
            
            elif action_type == ActionType.CLIPBOARD_PASTE:
                return self.clipboard_paste(
                    params.get('app_name', ''),
                    params.get('x', 0),
                    params.get('y', 0)
                )
            
            elif action_type == ActionType.GET_DESKTOP_STATE:
                return self.get_desktop_state(params.get('use_vision', False))
            
            elif action_type == ActionType.WAIT:
                return self.wait(params.get('duration', 1))
            
            elif action_type == ActionType.SCRAPE_WEBPAGE:
                return self.scrape_webpage(params.get('url', ''))
            
            else:
                return ExecutionResult.failure_result(
                    operation=action_type.value,
                    target="unknown",
                    message=f"Unsupported action type: {action_type.value}"
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation=action_type.value if action_type else "unknown",
                target="unknown",
                message=f"Exception occurred while executing action: {str(e)}",
                details={"exception": str(e), "params": params}
            )
    
    def click_abs(self, x: int, y: int) -> ExecutionResult:
        """
        Click on a specific element at absolute screen coordinates.

        Args:
            x: Absolute X coordinate to click
            y: Absolute Y coordinate to click
        
        Returns:
            ExecutionResult: Result of the click operation
        """
        try:
            powershell_cmd = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    public static extern bool SetProcessDPIAware();
                    [DllImport("user32.dll")]
                    public static extern bool SetProcessDpiAwarenessContext(IntPtr dpiContext);
                    [DllImport("user32.dll")]
                    public static extern bool SetCursorPos(int X, int Y);
                    [DllImport("user32.dll")]
                    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);
                }}
"@

            # Ensure the PowerShell process is DPI aware to avoid coordinate scaling issues
            try {{ [Win32]::SetProcessDPIAware() | Out-Null }} catch {{ }}

            # Move cursor and click at absolute coordinates
            [Win32]::SetCursorPos({x}, {y})
            [Win32]::mouse_event(0x02, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
            [Win32]::mouse_event(0x04, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
            
            Write-Output "SUCCESS: Clicked at ({x}, {y})"
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="click_abs",
                    target="screen",
                    message=f"Successfully clicked at ({x}, {y})"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="click_abs",
                    target="screen",
                    message=f"Failed to click at ({x}, {y}): {result}",
                    details={{"powershell_output": result, "x": x, "y": y}}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="click_abs",
                target="screen",
                message=f"Exception occurred while clicking: {str(e)}",
                details={{"exception": str(e), "x": x, "y": y}}
            )
    
    def type_text(self, app_name: str, text: str, x: int, y: int) -> ExecutionResult:
        """
        Type text at a specific location on the screen.
        
        Args:
            app_name: Name of the application to focus
            text: Text to type
            x: Absolute X coordinate to type at
            y: Absolute Y coordinate to type at
            
        Returns:
            ExecutionResult: Result of the type operation
        """
        try:
            # If an app_name is provided, focus the application window first
            if app_name:
                focus_result = self.focus_window(app_name)
                if not focus_result.success:
                    return ExecutionResult.failure_result(
                        operation="type_text",
                        target=app_name,
                        message=f"Failed to focus app before typing: {focus_result.message}",
                        details={"focus_error": focus_result.details}
                    )
                # Wait for the window to gain focus
                time.sleep(0.5)

            # Click at the absolute position to focus the input field
            click_result = self.click_abs(x=x, y=y)
            if not click_result.success:
                return ExecutionResult.failure_result(
                    operation="type_text",
                    target=app_name,
                    message=f"Failed to click before typing: {click_result.message}",
                    details={"click_error": click_result.details}
                )
            
            # Wait a moment for the click to register
            time.sleep(0.5)
            
            # Use PowerShell to type text (mimics Windows-MCP type_tool)
            # Escape special characters for PowerShell
            escaped_text = text.replace("'", "''").replace('"', '""')
            
            powershell_cmd = f"""
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.SendKeys]::SendWait('{escaped_text}')
            Write-Output "SUCCESS: Typed text at ({x}, {y}) in {app_name}"
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="type_text",
                    target=app_name,
                    message=f"Successfully typed text at ({x}, {y}) in {app_name}"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="type_text",
                    target=app_name,
                    message=f"Failed to type text in {app_name}: {result}",
                    details={"powershell_output": result, "text": text, "x": x, "y": y}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="type_text",
                target=app_name,
                message=f"Exception occurred while typing in {app_name}: {str(e)}",
                details={"exception": str(e), "text": text, "x": x, "y": y}
            )
    
    def send_keys(self, keys: List[str]) -> ExecutionResult:
        """
        Send keyboard shortcuts (mimics Windows-MCP shortcut_tool).
        
        Args:
            keys: List of keys to send (e.g., ["ctrl", "c"])
            
        Returns:
            ExecutionResult: Result of the send keys operation
        """
        try:
            # Convert keys to SendKeys format
            sendkeys_format = self._convert_to_sendkeys_format(keys)
            
            powershell_cmd = f"""
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.SendKeys]::SendWait('{sendkeys_format}')
            Write-Output "SUCCESS: Sent keys {' + '.join(keys)}"
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and "SUCCESS:" in result:
                return ExecutionResult.success_result(
                    operation="send_keys",
                    target="system",
                    message=f"Successfully sent keys: {' + '.join(keys)}"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="send_keys",
                    target="system",
                    message=f"Failed to send keys: {result}",
                    details={"powershell_output": result, "keys": keys}
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="send_keys",
                target="system",
                message=f"Exception occurred while sending keys: {str(e)}",
                details={"exception": str(e), "keys": keys}
            )
    
    def get_mouse_position(self) -> Optional[Dict[str, int]]:
        """
        Get the current absolute position of the mouse cursor.

        Returns:
            Optional[Dict[str, int]]: Dictionary with 'x' and 'y' coordinates or None on failure.
        """
        try:
            powershell_cmd = '''
            Add-Type -AssemblyName System.Windows.Forms
            $pos = [System.Windows.Forms.Cursor]::Position
            @{x=$pos.X; y=$pos.Y} | ConvertTo-Json
            '''
            result = self._execute_powershell(powershell_cmd)
            if result and result.startswith('{'):
                pos = json.loads(result)
                return {"x": int(pos["x"]), "y": int(pos["y"])}
            return None
        except Exception:
            return None

    def get_app_state(self, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Optional[Dict[str, Any]]: Application state information or None if not found
        """
        try:
            # Find the application in running apps
            running_apps = self.get_running_apps()
            
            for app in running_apps:
                if app_name.lower() in app.name.lower() or app_name.lower() in app.title.lower():
                    return {
                        "name": app.name,
                        "title": app.title,
                        "process_id": app.process_id,
                        "window_handle": app.window_handle,
                        "is_visible": app.is_visible,
                        "position": {"x": app.x, "y": app.y},
                        "size": {"width": app.width, "height": app.height},
                        "status": "running"
                    }
            
            return None
            
        except Exception as e:
            return None

    def execute_powershell_command(self, command: str) -> ExecutionResult:
        """
        Execute a custom PowerShell command.
        
        Args:
            command: PowerShell command to execute
            
        Returns:
            ExecutionResult: Result of the command execution
        """
        try:
            result = self._execute_powershell(command)
            
            if result is not None:
                return ExecutionResult.success_result(
                    operation="custom_command",
                    target="powershell",
                    message=f"PowerShell command executed successfully"
                )
            else:
                return ExecutionResult.failure_result(
                    operation="custom_command",
                    target="powershell",
                    message="PowerShell command execution failed"
                )
                
        except Exception as e:
            return ExecutionResult.failure_result(
                operation="custom_command",
                target="powershell",
                message=f"Exception occurred while executing PowerShell command: {str(e)}",
                details={"exception": str(e), "command": command}
            )
    
    def _execute_powershell(self, command: str) -> Optional[str]:
        """
        Execute a PowerShell command and return the output.
        
        Args:
            command: PowerShell command to execute
            
        Returns:
            Optional[str]: Command output or None if failed
        """
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"ERROR: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "ERROR: PowerShell command timed out"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _get_window_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """
        Get window information for a specific process ID.
        
        Args:
            pid: Process ID
            
        Returns:
            Optional[Dict[str, Any]]: Window information or None if not found
        """
        try:
            powershell_cmd = f"""
            $process = Get-Process -Id {pid} -ErrorAction SilentlyContinue
            if ($process -and $process.MainWindowTitle -ne "") {{
                $hwnd = $process.MainWindowHandle
                if ($hwnd -ne [IntPtr]::Zero) {{
                    Add-Type @"
                        using System;
                        using System.Runtime.InteropServices;
                        public class Win32 {{
                            [DllImport("user32.dll")]
                            public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
                            [DllImport("user32.dll")]
                            public static extern bool IsWindowVisible(IntPtr hWnd);
                            public struct RECT {{ public int Left; public int Top; public int Right; public int Bottom; }}
                        }}
"@
                    $rect = New-Object Win32+RECT
                    $visible = [Win32]::IsWindowVisible($hwnd)
                    $hasRect = [Win32]::GetWindowRect($hwnd, [ref]$rect)
                    
                    if ($hasRect) {{
                        $info = @{{
                            title = $process.MainWindowTitle
                            handle = $hwnd.ToInt64()
                            visible = $visible
                            x = $rect.Left
                            y = $rect.Top
                            width = $rect.Right - $rect.Left
                            height = $rect.Bottom - $rect.Top
                        }}
                        $info | ConvertTo-Json
                    }}
                }}
            }}
            """
            
            result = self._execute_powershell(powershell_cmd)
            
            if result and result.startswith('{'):
                return json.loads(result)
            else:
                return None
                
        except Exception:
            return None
    
    def _convert_to_sendkeys_format(self, keys: List[str]) -> str:
        """
        Convert key list to SendKeys format.
        
        Args:
            keys: List of keys to convert
            
        Returns:
            str: SendKeys format string
        """
        # Mapping of common keys to SendKeys format
        key_mapping = {
            'ctrl': '^',
            'alt': '%',
            'shift': '+',
            'win': '^{ESC}',  # Windows key approximation
            'tab': '{TAB}',
            'enter': '{ENTER}',
            'space': ' ',
            'backspace': '{BACKSPACE}',
            'delete': '{DELETE}',
            'home': '{HOME}',
            'end': '{END}',
            'pageup': '{PGUP}',
            'pagedown': '{PGDN}',
            'insert': '{INSERT}',
            'escape': '{ESC}',
            'up': '{UP}',
            'down': '{DOWN}',
            'left': '{LEFT}',
            'right': '{RIGHT}',
            'f1': '{F1}', 'f2': '{F2}', 'f3': '{F3}', 'f4': '{F4}',
            'f5': '{F5}', 'f6': '{F6}', 'f7': '{F7}', 'f8': '{F8}',
            'f9': '{F9}', 'f10': '{F10}', 'f11': '{F11}', 'f12': '{F12}',
            'numlock': '{NUMLOCK}',
            'capslock': '{CAPSLOCK}',
            'scrolllock': '{SCROLLLOCK}',
            'printscreen': '{PRTSC}',
            'pause': '{BREAK}',
        }
        
        result = ""
        modifier_keys = []
        
        for key in keys:
            key_lower = key.lower().strip()
            
            # Check if it's a modifier key
            if key_lower in ['ctrl', 'alt', 'shift']:
                modifier_keys.append(key_mapping[key_lower])
            else:
                # Add modifiers first
                for modifier in modifier_keys:
                    result += modifier
                
                # Add the main key
                if key_lower in key_mapping:
                    result += key_mapping[key_lower]
                elif len(key_lower) == 1:
                    result += key_lower
                else:
                    result += f"{{{key_lower}}}"
                
                # Clear modifiers after use
                modifier_keys = []
        
        return result


# Global windows controller instance
_windows_controller: Optional[WindowsController] = None


def get_windows_controller() -> WindowsController:
    """
    Get the global windows controller instance.
    
    Returns:
        WindowsController instance
    """
    global _windows_controller
    if _windows_controller is None:
        _windows_controller = WindowsController()
    return _windows_controller


def initialize_windows_controller() -> WindowsController:
    """
    Initialize the global windows controller.
    
    Returns:
        WindowsController instance
    """
    global _windows_controller
    _windows_controller = WindowsController()
    return _windows_controller