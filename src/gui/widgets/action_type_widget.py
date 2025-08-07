"""
Action type widget for dynamic action configuration.
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Dict, Any, Callable, List
from pynput import mouse

from src.models.action import ActionType, validate_action_params


class ActionTypeWidget(ttk.Frame):
    """Widget for configuring action types and parameters."""
    
    def __init__(self, parent: tk.Widget, on_change: Optional[Callable[[], None]] = None):
        """
        Initialize the action type widget.
        
        Args:
            parent: Parent widget
            on_change: Callback function when configuration changes
        """
        super().__init__(parent)
        self.on_change = on_change
        self.mouse_listener = None
        self.capture_button = None
        
        # Variables
        self.action_type_var = tk.StringVar(value=ActionType.LAUNCH_APP.value)
        
        # Parameter variables for different action types
        self.app_name_var = tk.StringVar()
        self.width_var = tk.IntVar(value=800)
        self.height_var = tk.IntVar(value=600)
        self.x_var = tk.IntVar(value=100)
        self.y_var = tk.IntVar(value=100)
        self.text_var = tk.StringVar()
        self.keys_var = tk.StringVar()
        self.command_var = tk.StringVar()
        
        # Create UI
        self._create_ui()
        
        # Bind events
        self._bind_events()
        
        # Update parameter frame initially
        self._on_action_type_change()
    
    def _create_ui(self):
        """Create the widget UI."""
        # Action type selection
        type_frame = ttk.LabelFrame(self, text="動作類型", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Action type options
        action_types = [
            (ActionType.LAUNCH_APP.value, "啟動應用程式"),
            (ActionType.CLOSE_APP.value, "關閉應用程式"),
            (ActionType.RESIZE_WINDOW.value, "調整視窗大小"),
            (ActionType.MOVE_WINDOW.value, "移動視窗位置"),
            (ActionType.MINIMIZE_WINDOW.value, "最小化視窗"),
            (ActionType.MAXIMIZE_WINDOW.value, "最大化視窗"),
            (ActionType.RESTORE_WINDOW.value, "還原視窗"),
            (ActionType.FOCUS_WINDOW.value, "聚焦視窗"),
            (ActionType.CLICK_ABS.value, "點擊絕對座標 (click_abs)"),
            (ActionType.TYPE_TEXT.value, "輸入文字"),
            (ActionType.SEND_KEYS.value, "發送按鍵"),
            (ActionType.CUSTOM_COMMAND.value, "自訂命令")
        ]
        
        self.type_combo = ttk.Combobox(type_frame, textvariable=self.action_type_var,
                                     values=[at[0] for at in action_types],
                                     state="readonly", width=30)
        self.type_combo.pack(fill=tk.X)
        
        # Parameters frame
        self.params_frame = ttk.LabelFrame(self, text="動作參數", padding=10)
        self.params_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create parameter input frames (initially hidden)
        self._create_parameter_frames()
    
    def _create_parameter_frames(self):
        """Create parameter input frames for different action types."""
        # App name frame (used by multiple actions)
        self.app_name_frame = ttk.Frame(self.params_frame)
        ttk.Label(self.app_name_frame, text="應用程式名稱:").pack(anchor=tk.W)
        
        # Common applications list
        common_apps = [
            "notepad", "calculator", "chrome", "firefox", "edge",
            "explorer", "cmd", "powershell", "winword", "excel",
            "outlook", "teams", "discord", "spotify", "vlc"
        ]
        
        # Use ComboBox instead of Entry to allow both selection and custom input
        app_combo = ttk.Combobox(self.app_name_frame, textvariable=self.app_name_var, 
                                values=common_apps, width=37)
        app_combo.pack(fill=tk.X, pady=(5, 10))
        ttk.Label(self.app_name_frame, text="選擇常用應用程式或輸入自訂應用程式名稱", 
                 font=("", 8), foreground="gray").pack(anchor=tk.W)
        
        self.app_name_optional_label = ttk.Label(self.app_name_frame,
                                                 text="（可選）點擊前聚焦此應用程式",
                                                 font=("", 8), foreground="blue")
        
        # Resize window parameters
        self.resize_frame = ttk.Frame(self.params_frame)
        
        size_frame = ttk.Frame(self.resize_frame)
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(size_frame, text="寬度:").pack(side=tk.LEFT)
        width_spinbox = ttk.Spinbox(size_frame, from_=100, to=9999, 
                                  textvariable=self.width_var, width=8)
        width_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(size_frame, text="高度:").pack(side=tk.LEFT)
        height_spinbox = ttk.Spinbox(size_frame, from_=100, to=9999, 
                                   textvariable=self.height_var, width=8)
        height_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # Move window parameters
        self.move_frame = ttk.Frame(self.params_frame)
        
        pos_frame = ttk.Frame(self.move_frame)
        pos_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pos_frame, text="X座標:").pack(side=tk.LEFT)
        x_spinbox = ttk.Spinbox(pos_frame, from_=0, to=9999, 
                              textvariable=self.x_var, width=8)
        x_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(pos_frame, text="Y座標:").pack(side=tk.LEFT)
        y_spinbox = ttk.Spinbox(pos_frame, from_=0, to=9999, 
                              textvariable=self.y_var, width=8)
        y_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # Click element parameters
        self.click_frame = ttk.Frame(self.params_frame)
        
        top_click_frame = ttk.Frame(self.click_frame)
        top_click_frame.pack(fill=tk.X, pady=(0, 10))

        self.capture_button = ttk.Button(top_click_frame, text="取得座標", command=self._start_click_capture)
        self.capture_button.pack(side=tk.LEFT)

        click_pos_frame = ttk.Frame(self.click_frame)
        click_pos_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(click_pos_frame, text="點擊X座標:").pack(side=tk.LEFT)
        click_x_spinbox = ttk.Spinbox(click_pos_frame, from_=0, to=9999,
                                    textvariable=self.x_var, width=8)
        click_x_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(click_pos_frame, text="點擊Y座標:").pack(side=tk.LEFT)
        click_y_spinbox = ttk.Spinbox(click_pos_frame, from_=0, to=9999,
                                    textvariable=self.y_var, width=8)
        click_y_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(self.click_frame,
                  text="座標為螢幕絕對座標。可選填應用程式名稱以在點擊前聚焦。",
                  font=("", 8), foreground="gray").pack(anchor=tk.W)
        
        # Type text parameters
        self.type_text_frame = ttk.Frame(self.params_frame)
        
        ttk.Label(self.type_text_frame, text="輸入文字:").pack(anchor=tk.W)
        text_entry = ttk.Entry(self.type_text_frame, textvariable=self.text_var, width=40)
        text_entry.pack(fill=tk.X, pady=(5, 10))
        
        text_pos_frame = ttk.Frame(self.type_text_frame)
        text_pos_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(text_pos_frame, text="輸入位置X:").pack(side=tk.LEFT)
        text_x_spinbox = ttk.Spinbox(text_pos_frame, from_=0, to=9999, 
                                   textvariable=self.x_var, width=8)
        text_x_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(text_pos_frame, text="輸入位置Y:").pack(side=tk.LEFT)
        text_y_spinbox = ttk.Spinbox(text_pos_frame, from_=0, to=9999, 
                                   textvariable=self.y_var, width=8)
        text_y_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # Send keys parameters
        self.send_keys_frame = ttk.Frame(self.params_frame)
        
        ttk.Label(self.send_keys_frame, text="按鍵組合:").pack(anchor=tk.W)
        keys_entry = ttk.Entry(self.send_keys_frame, textvariable=self.keys_var, width=40)
        keys_entry.pack(fill=tk.X, pady=(5, 10))
        
        keys_help = ttk.Label(self.send_keys_frame, 
                            text="用逗號分隔按鍵，例如: ctrl,c 或 alt,tab 或 f5",
                            font=("", 8), foreground="gray")
        keys_help.pack(anchor=tk.W)
        
        # Common keys reference
        common_keys_text = ("常用按鍵: ctrl, alt, shift, win, tab, enter, space, backspace, "
                          "delete, home, end, pageup, pagedown, f1-f12, up, down, left, right")
        common_keys_label = ttk.Label(self.send_keys_frame, text=common_keys_text,
                                    font=("", 8), foreground="gray", wraplength=400)
        common_keys_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Custom command parameters
        self.custom_command_frame = ttk.Frame(self.params_frame)
        
        ttk.Label(self.custom_command_frame, text="PowerShell命令:").pack(anchor=tk.W)
        command_text = tk.Text(self.custom_command_frame, height=4, width=50)
        command_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # Bind text widget to variable
        def on_command_change(*args):
            self.command_var.set(command_text.get("1.0", tk.END).strip())
            self._on_change_callback()
        
        command_text.bind("<KeyRelease>", on_command_change)
        command_text.bind("<FocusOut>", on_command_change)
        
        ttk.Label(self.custom_command_frame, 
                 text="輸入要執行的PowerShell命令，請謹慎使用",
                 font=("", 8), foreground="red").pack(anchor=tk.W)
    
    def _bind_events(self):
        """Bind widget events."""
        self.type_combo.bind("<<ComboboxSelected>>", self._on_action_type_change)
        
        # Bind parameter variables
        self.app_name_var.trace_add("write", lambda *args: self._on_change_callback())
        self.width_var.trace_add("write", lambda *args: self._on_change_callback())
        self.height_var.trace_add("write", lambda *args: self._on_change_callback())
        self.x_var.trace_add("write", lambda *args: self._on_change_callback())
        self.y_var.trace_add("write", lambda *args: self._on_change_callback())
        self.text_var.trace_add("write", lambda *args: self._on_change_callback())
        self.keys_var.trace_add("write", lambda *args: self._on_change_callback())
        self.command_var.trace_add("write", lambda *args: self._on_change_callback())
    
    def _on_action_type_change(self, event=None):
        """Handle action type change."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self._reset_capture_button()

        # Hide all parameter frames
        for frame in [self.app_name_frame, self.resize_frame, self.move_frame,
                     self.click_frame, self.type_text_frame, self.send_keys_frame,
                     self.custom_command_frame]:
            frame.pack_forget()
        
        self.app_name_optional_label.pack_forget()
        
        action_type = ActionType(self.action_type_var.get())
        
        # Show relevant parameter frames
        if action_type in [ActionType.LAUNCH_APP, ActionType.CLOSE_APP,
                          ActionType.MINIMIZE_WINDOW, ActionType.MAXIMIZE_WINDOW,
                          ActionType.RESTORE_WINDOW, ActionType.FOCUS_WINDOW]:
            self.app_name_frame.pack(fill=tk.X)
        
        elif action_type == ActionType.RESIZE_WINDOW:
            self.app_name_frame.pack(fill=tk.X)
            self.resize_frame.pack(fill=tk.X)
        
        elif action_type == ActionType.MOVE_WINDOW:
            self.app_name_frame.pack(fill=tk.X)
            self.move_frame.pack(fill=tk.X)
        
        elif action_type == ActionType.CLICK_ABS:
            self.click_frame.pack(fill=tk.X)
        
        elif action_type == ActionType.TYPE_TEXT:
            self.app_name_frame.pack(fill=tk.X)
            self.type_text_frame.pack(fill=tk.X)
        
        elif action_type == ActionType.SEND_KEYS:
            self.send_keys_frame.pack(fill=tk.X)
        
        elif action_type == ActionType.CUSTOM_COMMAND:
            self.custom_command_frame.pack(fill=tk.BOTH, expand=True)
        
        self._on_change_callback()
    
    def _on_change_callback(self):
        """Call the change callback if provided."""
        if self.on_change:
            self.on_change()
    
    def get_action_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the current action configuration.
        
        Returns:
            Dictionary with action_type and action_params, or None if invalid
        """
        try:
            action_type = ActionType(self.action_type_var.get())
            action_params = {}
            
            if action_type in [ActionType.LAUNCH_APP, ActionType.CLOSE_APP,
                              ActionType.MINIMIZE_WINDOW, ActionType.MAXIMIZE_WINDOW,
                              ActionType.RESTORE_WINDOW, ActionType.FOCUS_WINDOW]:
                app_name = self.app_name_var.get().strip()
                if not app_name:
                    return None
                action_params = {'app_name': app_name}
            
            elif action_type == ActionType.RESIZE_WINDOW:
                app_name = self.app_name_var.get().strip()
                if not app_name:
                    return None
                action_params = {
                    'app_name': app_name,
                    'width': self.width_var.get(),
                    'height': self.height_var.get()
                }
            
            elif action_type == ActionType.MOVE_WINDOW:
                app_name = self.app_name_var.get().strip()
                if not app_name:
                    return None
                action_params = {
                    'app_name': app_name,
                    'x': self.x_var.get(),
                    'y': self.y_var.get()
                }
            
            elif action_type == ActionType.CLICK_ABS:
                action_params = {
                    'x': self.x_var.get(),
                    'y': self.y_var.get()
                }
            
            elif action_type == ActionType.TYPE_TEXT:
                app_name = self.app_name_var.get().strip()
                text = self.text_var.get().strip()
                if not app_name or not text:
                    return None
                action_params = {
                    'app_name': app_name,
                    'text': text,
                    'x': self.x_var.get(),
                    'y': self.y_var.get()
                }
            
            elif action_type == ActionType.SEND_KEYS:
                keys_str = self.keys_var.get().strip()
                if not keys_str:
                    return None
                # Parse comma-separated keys
                keys = [key.strip() for key in keys_str.split(',') if key.strip()]
                if not keys:
                    return None
                action_params = {'keys': keys}
            
            elif action_type == ActionType.CUSTOM_COMMAND:
                command = self.command_var.get().strip()
                if not command:
                    return None
                action_params = {'command': command}
            
            # Validate parameters
            if not validate_action_params(action_type, action_params):
                return None
            
            return {
                'action_type': action_type,
                'action_params': action_params
            }
        except (ValueError, TypeError):
            return None
    
    def set_action(self, action_type: ActionType, action_params: Dict[str, Any]):
        """
        Set the widget values from action type and parameters.
        
        Args:
            action_type: ActionType to set
            action_params: Parameters dictionary
        """
        # Set action type
        self.action_type_var.set(action_type.value)
        
        # Set parameters based on action type
        if 'app_name' in action_params:
            self.app_name_var.set(action_params['app_name'])
        
        if 'width' in action_params:
            self.width_var.set(action_params['width'])
        if 'height' in action_params:
            self.height_var.set(action_params['height'])
        
        if 'x' in action_params:
            self.x_var.set(action_params['x'])
        if 'y' in action_params:
            self.y_var.set(action_params['y'])
        
        if 'text' in action_params:
            self.text_var.set(action_params['text'])
        
        if 'keys' in action_params:
            keys_str = ', '.join(action_params['keys'])
            self.keys_var.set(keys_str)
        
        if 'command' in action_params:
            self.command_var.set(action_params['command'])
        
        # Update UI
        self._on_action_type_change()
    
    def validate(self) -> bool:
        """
        Validate the current action configuration.
        
        Returns:
            True if configuration is valid
        """
        config = self.get_action_config()
        return config is not None

    def _start_click_capture(self):
        """Start capturing a single mouse click to get coordinates."""
        if self.mouse_listener:
            return

        self.capture_button.config(text="點擊螢幕擷取...", state=tk.DISABLED)

        # Run listener in a separate thread to avoid blocking the GUI
        listener_thread = threading.Thread(target=self._run_listener, daemon=True)
        listener_thread.start()

    def _run_listener(self):
        """Runs the pynput mouse listener."""
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        with self.mouse_listener as listener:
            listener.join()

    def _on_click(self, x, y, button, pressed):
        """Callback for mouse click event."""
        if button == mouse.Button.left and pressed:
            self.x_var.set(x)
            self.y_var.set(y)
            
            # Stop the listener from the main thread
            self.after(0, self._stop_listener)
            return False  # Stop listener after one click

    def _stop_listener(self):
        """Stops the mouse listener and resets the button."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        self._reset_capture_button()

    def _reset_capture_button(self):
        """Resets the capture button to its original state."""
        if self.capture_button:
            self.capture_button.config(text="取得座標", state=tk.NORMAL)