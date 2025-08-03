"""
Action type definitions for Windows operations.
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class ActionType(Enum):
    """Enumeration of available Windows control actions."""
    
    LAUNCH_APP = "launch_app"              # 啟動指定的應用程式
    CLOSE_APP = "close_app"                # 關閉指定的應用程式
    RESIZE_WINDOW = "resize_window"        # 調整視窗大小到指定尺寸
    MOVE_WINDOW = "move_window"            # 移動視窗到指定位置
    MINIMIZE_WINDOW = "minimize_window"    # 最小化視窗
    MAXIMIZE_WINDOW = "maximize_window"    # 最大化視窗
    RESTORE_WINDOW = "restore_window"      # 還原視窗到正常大小
    FOCUS_WINDOW = "focus_window"          # 將視窗帶到前景
    CLICK_ELEMENT = "click_element"        # 點擊視窗內的特定元素
    TYPE_TEXT = "type_text"                # 在指定位置輸入文字
    SEND_KEYS = "send_keys"                # 發送鍵盤快捷鍵
    CUSTOM_COMMAND = "custom_command"      # 執行自訂PowerShell命令


@dataclass
class ActionParams:
    """Base class for action parameters."""
    pass


@dataclass
class LaunchAppParams(ActionParams):
    """Parameters for launching an application."""
    app_name: str


@dataclass
class CloseAppParams(ActionParams):
    """Parameters for closing an application."""
    app_name: str


@dataclass
class ResizeWindowParams(ActionParams):
    """Parameters for resizing a window."""
    app_name: str
    width: int
    height: int


@dataclass
class MoveWindowParams(ActionParams):
    """Parameters for moving a window."""
    app_name: str
    x: int
    y: int


@dataclass
class WindowControlParams(ActionParams):
    """Parameters for basic window control operations."""
    app_name: str


@dataclass
class ClickElementParams(ActionParams):
    """Parameters for clicking an element."""
    app_name: str
    x: int
    y: int


@dataclass
class TypeTextParams(ActionParams):
    """Parameters for typing text."""
    app_name: str
    text: str
    x: int
    y: int


@dataclass
class SendKeysParams(ActionParams):
    """Parameters for sending keyboard shortcuts."""
    keys: List[str]


@dataclass
class CustomCommandParams(ActionParams):
    """Parameters for custom PowerShell commands."""
    command: str


def validate_action_params(action_type: ActionType, params: Dict[str, Any]) -> bool:
    """
    Validate action parameters for the given action type.
    
    Args:
        action_type: The type of action to validate
        params: Dictionary of parameters to validate
        
    Returns:
        bool: True if parameters are valid, False otherwise
    """
    try:
        if action_type == ActionType.LAUNCH_APP:
            return _validate_launch_app_params(params)
        elif action_type == ActionType.CLOSE_APP:
            return _validate_close_app_params(params)
        elif action_type == ActionType.RESIZE_WINDOW:
            return _validate_resize_window_params(params)
        elif action_type == ActionType.MOVE_WINDOW:
            return _validate_move_window_params(params)
        elif action_type in [ActionType.MINIMIZE_WINDOW, ActionType.MAXIMIZE_WINDOW, 
                           ActionType.RESTORE_WINDOW, ActionType.FOCUS_WINDOW]:
            return _validate_window_control_params(params)
        elif action_type == ActionType.CLICK_ELEMENT:
            return _validate_click_element_params(params)
        elif action_type == ActionType.TYPE_TEXT:
            return _validate_type_text_params(params)
        elif action_type == ActionType.SEND_KEYS:
            return _validate_send_keys_params(params)
        elif action_type == ActionType.CUSTOM_COMMAND:
            return _validate_custom_command_params(params)
        else:
            return False
    except (KeyError, TypeError, ValueError):
        return False


def _validate_launch_app_params(params: Dict[str, Any]) -> bool:
    """Validate launch app parameters."""
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0
    )


def _validate_close_app_params(params: Dict[str, Any]) -> bool:
    """Validate close app parameters."""
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0
    )


def _validate_resize_window_params(params: Dict[str, Any]) -> bool:
    """Validate resize window parameters."""
    return (
        'app_name' in params and
        'width' in params and
        'height' in params and
        isinstance(params['app_name'], str) and
        isinstance(params['width'], int) and
        isinstance(params['height'], int) and
        len(params['app_name'].strip()) > 0 and
        params['width'] > 0 and
        params['height'] > 0
    )


def _validate_move_window_params(params: Dict[str, Any]) -> bool:
    """Validate move window parameters."""
    return (
        'app_name' in params and
        'x' in params and
        'y' in params and
        isinstance(params['app_name'], str) and
        isinstance(params['x'], int) and
        isinstance(params['y'], int) and
        len(params['app_name'].strip()) > 0 and
        params['x'] >= 0 and
        params['y'] >= 0
    )


def _validate_window_control_params(params: Dict[str, Any]) -> bool:
    """Validate basic window control parameters."""
    return (
        'app_name' in params and
        isinstance(params['app_name'], str) and
        len(params['app_name'].strip()) > 0
    )


def _validate_click_element_params(params: Dict[str, Any]) -> bool:
    """Validate click element parameters."""
    return (
        'app_name' in params and
        'x' in params and
        'y' in params and
        isinstance(params['app_name'], str) and
        isinstance(params['x'], int) and
        isinstance(params['y'], int) and
        len(params['app_name'].strip()) > 0 and
        params['x'] >= 0 and
        params['y'] >= 0
    )


def _validate_type_text_params(params: Dict[str, Any]) -> bool:
    """Validate type text parameters."""
    return (
        'app_name' in params and
        'text' in params and
        'x' in params and
        'y' in params and
        isinstance(params['app_name'], str) and
        isinstance(params['text'], str) and
        isinstance(params['x'], int) and
        isinstance(params['y'], int) and
        len(params['app_name'].strip()) > 0 and
        params['x'] >= 0 and
        params['y'] >= 0
    )


def _validate_send_keys_params(params: Dict[str, Any]) -> bool:
    """Validate send keys parameters."""
    return (
        'keys' in params and
        isinstance(params['keys'], list) and
        len(params['keys']) > 0 and
        all(isinstance(key, str) and len(key.strip()) > 0 for key in params['keys'])
    )


def _validate_custom_command_params(params: Dict[str, Any]) -> bool:
    """Validate custom command parameters."""
    return (
        'command' in params and
        isinstance(params['command'], str) and
        len(params['command'].strip()) > 0
    )